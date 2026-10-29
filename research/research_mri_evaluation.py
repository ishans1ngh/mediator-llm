import os
import torch
import nibabel as nib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from monai.networks.nets import SegResNet
from monai.inferers import SlidingWindowInferer

# ============================================================
# CONFIGURATION
# ============================================================

# Input/Output directories
INPUT_DIR = Path("data/mri_cases")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True, parents=True)

# Model path
MODEL_PATH = Path("models/brats_mri_segmentation/models/model.pt")

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {device}")
print(f"Input directory: {INPUT_DIR}")
print(f"Results directory: {RESULTS_DIR}")
print(f"Model path: {MODEL_PATH}")

# ============================================================
# CASE DISCOVERY
# ============================================================

def discover_cases(input_dir: Path) -> List[Path]:
    """
    Automatically discover all valid BraTS case folders in the input directory.
    
    A valid case folder must contain at least the required MRI modalities:
    - *_t1.nii or *_t1.nii.gz
    - *_t1ce.nii or *_t1ce.nii.gz
    - *_t2.nii or *_t2.nii.gz
    - *_flair.nii or *_flair.nii.gz
    - *_seg.nii or *_seg.nii.gz (ground truth)
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    case_folders = []
    
    for item in input_dir.iterdir():
        if item.is_dir():
            case_folders.append(item)
    
    print(f"Found {len(case_folders)} potential case folders in {input_dir}")
    
    # Validate each case folder
    valid_cases = []
    for case_folder in case_folders:
        if is_valid_case(case_folder):
            valid_cases.append(case_folder)
            print(f"  [OK] Valid case: {case_folder.name}")
        else:
            print(f"  [SKIP] Invalid case (missing required files): {case_folder.name}")
    
    return sorted(valid_cases, key=lambda x: x.name)

def is_valid_case(case_folder: Path) -> bool:
    """
    Check if a case folder contains all required MRI modalities.
    """
    case_name = case_folder.name
    
    # Required file patterns
    required_patterns = [
        f"{case_name}_t1.nii",
        f"{case_name}_t1.nii.gz",
        f"{case_name}_t1ce.nii",
        f"{case_name}_t1ce.nii.gz",
        f"{case_name}_t2.nii",
        f"{case_name}_t2.nii.gz",
        f"{case_name}_flair.nii",
        f"{case_name}_flair.nii.gz",
        f"{case_name}_seg.nii",
        f"{case_name}_seg.nii.gz"
    ]
    
    # Check for at least one version of each required modality
    has_t1 = any([(case_folder / f"{case_name}_t1.nii").exists(),
                 (case_folder / f"{case_name}_t1.nii.gz").exists()])
    has_t1ce = any([(case_folder / f"{case_name}_t1ce.nii").exists(),
                   (case_folder / f"{case_name}_t1ce.nii.gz").exists()])
    has_t2 = any([(case_folder / f"{case_name}_t2.nii").exists(),
                 (case_folder / f"{case_name}_t2.nii.gz").exists()])
    has_flair = any([(case_folder / f"{case_name}_flair.nii").exists(),
                    (case_folder / f"{case_name}_flair.nii.gz").exists()])
    has_seg = any([(case_folder / f"{case_name}_seg.nii").exists(),
                  (case_folder / f"{case_name}_seg.nii.gz").exists()])
    
    return has_t1 and has_t1ce and has_t2 and has_flair and has_seg

def find_modality_file(case_folder: Path, case_name: str, modality: str) -> Optional[Path]:
    """
    Find the actual file for a given modality (handles both .nii and .nii.gz extensions).
    """
    # Try .nii first, then .nii.gz
    nii_path = case_folder / f"{case_name}_{modality}.nii"
    nii_gz_path = case_folder / f"{case_name}_{modality}.nii.gz"
    
    if nii_path.exists():
        return nii_path
    elif nii_gz_path.exists():
        return nii_gz_path
    else:
        return None

# ============================================================
# MRI LOADING AND PREPROCESSING
# ============================================================

def load_mri_file(file_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load a single MRI file using nibabel.
    
    Returns:
        (data, affine) tuple
    """
    img = nib.load(str(file_path))
    data = img.get_fdata().astype(np.float32)
    return data, img.affine

def normalize_volume(volume: np.ndarray) -> np.ndarray:
    """
    Normalize MRI volume using z-score normalization on non-zero voxels.
    This matches the normalization used in the original test_mri_inference.py script.
    """
    mask = volume != 0
    
    if np.any(mask):
        mean = volume[mask].mean()
        std = volume[mask].std()
        
        if std > 0:
            volume[mask] = (volume[mask] - mean) / std
    
    return volume

def load_and_preprocess_case(case_folder: Path) -> Optional[Dict]:
    """
    Load and preprocess all MRI modalities for a single case.
    
    Returns:
        Dictionary with preprocessed data and metadata, or None if processing fails.
    """
    case_name = case_folder.name
    
    try:
        # Find required files
        t1_path = find_modality_file(case_folder, case_name, "t1")
        t1ce_path = find_modality_file(case_folder, case_name, "t1ce")
        t2_path = find_modality_file(case_folder, case_name, "t2")
        flair_path = find_modality_file(case_folder, case_name, "flair")
        seg_path = find_modality_file(case_folder, case_name, "seg")
        
        if None in [t1_path, t1ce_path, t2_path, flair_path, seg_path]:
            print(f"    Error: Missing required files for {case_name}")
            return None
        
        # Load all modalities
        print(f"    Loading MRI modalities...")
        t1, affine = load_mri_file(t1_path)
        t1ce, _ = load_mri_file(t1ce_path)
        t2, _ = load_mri_file(t2_path)
        flair, _ = load_mri_file(flair_path)
        seg, _ = load_mri_file(seg_path)
        
        # Validate dimensions
        if not (t1.shape == t1ce.shape == t2.shape == flair.shape == seg.shape):
            print(f"    Error: Dimension mismatch for {case_name}")
            print(f"      T1: {t1.shape}, T1ce: {t1ce.shape}, T2: {t2.shape}, FLAIR: {flair.shape}, Seg: {seg.shape}")
            return None
        
        print(f"    Dimensions: {t1.shape}")
        
        # Normalize each modality
        print(f"    Normalizing modalities...")
        t1 = normalize_volume(t1)
        t1ce = normalize_volume(t1ce)
        t2 = normalize_volume(t2)
        flair = normalize_volume(flair)
        
        # Stack modalities in the required order: T1, T1ce, T2, FLAIR
        print(f"    Stacking modalities...")
        image = np.stack([t1, t1ce, t2, flair], axis=0)
        
        return {
            "case_name": case_name,
            "image": image,
            "affine": affine,
            "ground_truth": seg,
            "shape": t1.shape
        }
        
    except Exception as e:
        print(f"    Error processing {case_name}: {str(e)}")
        return None

# ============================================================
# MODEL LOADING
# ============================================================

def load_model(model_path: Path, device: torch.device) -> SegResNet:
    """
    Load the trained SegResNet model.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    print(f"Loading model from {model_path}...")
    
    # Create SegResNet with the same architecture as the original
    model = SegResNet(
        blocks_down=(1, 2, 2, 4),
        blocks_up=(1, 1, 1),
        init_filters=16,
        in_channels=4,
        out_channels=3,
        dropout_prob=0.2,
    ).to(device)
    
    # Load trained weights
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        model.load_state_dict(checkpoint["state_dict"])
    elif isinstance(checkpoint, dict) and "model" in checkpoint:
        model.load_state_dict(checkpoint["model"])
    else:
        model.load_state_dict(checkpoint)
    
    print("Model loaded successfully")
    return model

# ============================================================
# INFERENCE
# ============================================================

def run_inference(model: SegResNet, image: np.ndarray, device: torch.device) -> np.ndarray:
    """
    Run SegResNet inference on preprocessed MRI data.
    
    Returns:
        Segmentation mask with MONAI label mapping applied.
    """
    # Convert to tensor
    image_tensor = torch.from_numpy(image).unsqueeze(0).to(device)
    
    # Create sliding window inferer (same configuration as original)
    inferer = SlidingWindowInferer(
        roi_size=(240, 240, 160),
        sw_batch_size=1,
        overlap=0.5
    )
    
    # Run inference
    model.eval()
    with torch.no_grad():
        output = inferer(image_tensor, model)
    
    # Convert predictions
    probabilities = torch.sigmoid(output)
    prediction = (probabilities > 0.5).cpu().numpy()[0]
    
    # Apply MONAI label mapping:
    # channel 0 -> label 1
    # channel 1 -> label 2
    # channel 2 -> label 4
    segmentation = np.zeros(prediction.shape[1:], dtype=np.uint8)
    segmentation[prediction[0]] = 1
    segmentation[prediction[1]] = 2
    segmentation[prediction[2]] = 4
    
    return segmentation

# ============================================================
# METRICS CALCULATION
# ============================================================

def calculate_metrics(ground_truth: np.ndarray, prediction: np.ndarray) -> Dict[str, float]:
    """
    Calculate evaluation metrics for segmentation.
    
    Metrics:
    - Ground truth tumor voxels
    - Predicted tumor voxels
    - Absolute voxel difference
    - Dice score
    - IoU (Intersection over Union)
    """
    # Create binary masks (tumor vs background)
    gt_binary = (ground_truth != 0).astype(np.uint8)
    pred_binary = (prediction != 0).astype(np.uint8)
    
    # Count tumor voxels
    gt_tumor_voxels = np.count_nonzero(gt_binary)
    pred_tumor_voxels = np.count_nonzero(pred_binary)
    
    # Calculate absolute difference
    abs_diff = abs(pred_tumor_voxels - gt_tumor_voxels)
    
    # Calculate Dice score
    intersection = np.sum((gt_binary == 1) & (pred_binary == 1))
    dice = 0.0
    
    if gt_tumor_voxels + pred_tumor_voxels > 0:
        dice = 2.0 * intersection / (gt_tumor_voxels + pred_tumor_voxels)
    elif gt_tumor_voxels == 0 and pred_tumor_voxels == 0:
        # Both are zero - perfect match for background
        dice = 1.0
    
    # Calculate IoU
    union = np.sum((gt_binary == 1) | (pred_binary == 1))
    iou = 0.0
    
    if union > 0:
        iou = intersection / union
    elif gt_tumor_voxels == 0 and pred_tumor_voxels == 0:
        # Both are zero - perfect match for background
        iou = 1.0
    
    return {
        "ground_truth_tumor_voxels": float(gt_tumor_voxels),
        "predicted_tumor_voxels": float(pred_tumor_voxels),
        "absolute_voxel_difference": float(abs_diff),
        "dice_score": float(dice),
        "iou": float(iou)
    }

# ============================================================
# RESULTS STORAGE
# ============================================================

def save_results_to_csv(results: List[Dict], output_path: Path):
    """
    Save evaluation results to CSV file.
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

def save_summary_statistics(results: List[Dict], failed_cases: List[Dict], output_path: Path):
    """
    Save summary statistics to text file.
    """
    if not results:
        summary = "No successful results to summarize.\n"
        summary += f"Failed cases: {len(failed_cases)}\n"
        for case in failed_cases:
            summary += f"  - {case['case_name']}: {case['error']}\n"
        
        with open(output_path, 'w') as f:
            f.write(summary)
        return
    
    # Extract metrics
    gt_voxels = [r['ground_truth_tumor_voxels'] for r in results]
    pred_voxels = [r['predicted_tumor_voxels'] for r in results]
    abs_diffs = [r['absolute_voxel_difference'] for r in results]
    dice_scores = [r['dice_score'] for r in results]
    ious = [r['iou'] for r in results]
    
    # Calculate statistics
    mean_gt = np.mean(gt_voxels)
    mean_pred = np.mean(pred_voxels)
    mean_abs_diff = np.mean(abs_diffs)
    mean_dice = np.mean(dice_scores)
    std_dice = np.std(dice_scores)
    mean_iou = np.mean(ious)
    std_iou = np.std(ious)
    min_dice = np.min(dice_scores)
    max_dice = np.max(dice_scores)
    
    # Build summary
    summary = "=" * 60 + "\n"
    summary += "MRI SEGMENTATION EVALUATION SUMMARY\n"
    summary += "=" * 60 + "\n\n"
    
    summary += f"Successfully processed cases: {len(results)}\n"
    summary += f"Failed/skipped cases: {len(failed_cases)}\n\n"
    
    summary += "METRICS SUMMARY\n"
    summary += "-" * 60 + "\n"
    summary += f"Mean ground-truth tumor voxels: {mean_gt:.2f}\n"
    summary += f"Mean predicted tumor voxels: {mean_pred:.2f}\n"
    summary += f"Mean absolute voxel difference: {mean_abs_diff:.2f}\n"
    summary += f"Mean Dice: {mean_dice:.4f}\n"
    summary += f"Std Dev Dice: {std_dice:.4f}\n"
    summary += f"Mean IoU: {mean_iou:.4f}\n"
    summary += f"Std Dev IoU: {std_iou:.4f}\n"
    summary += f"Min Dice: {min_dice:.4f}\n"
    summary += f"Max Dice: {max_dice:.4f}\n\n"
    
    if failed_cases:
        summary += "FAILED CASES\n"
        summary += "-" * 60 + "\n"
        for case in failed_cases:
            summary += f"  - {case['case_name']}: {case['error']}\n"
        summary += "\n"
    
    summary += "=" * 60 + "\n"
    
    with open(output_path, 'w') as f:
        f.write(summary)
    
    print(f"Summary saved to {output_path}")

# ============================================================
# GRAPH GENERATION
# ============================================================

def generate_tumor_voxels_graph(results: List[Dict], output_path: Path):
    """
    Generate a research-quality graph comparing Ground Truth vs Predicted Total Tumor Voxels.
    """
    if not results:
        print("No results to graph")
        return
    
    # Extract data
    case_ids = [r['case_id'] for r in results]
    gt_voxels = [r['ground_truth_tumor_voxels'] for r in results]
    pred_voxels = [r['predicted_tumor_voxels'] for r in results]
    
    # Create figure with appropriate size for number of cases
    n_cases = len(case_ids)
    fig_width = max(12, n_cases * 0.4)
    fig_height = 8
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Set up bar positions
    x = np.arange(n_cases)
    width = 0.35
    
    # Create grouped bar chart
    bars1 = ax.bar(x - width/2, gt_voxels, width, label='Ground Truth', color='#2E86AB', alpha=0.8)
    bars2 = ax.bar(x + width/2, pred_voxels, width, label='Predicted', color='#A23B72', alpha=0.8)
    
    # Customize the plot
    ax.set_xlabel('MRI Case', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Tumor Voxels', fontsize=12, fontweight='bold')
    ax.set_title('Ground Truth vs Predicted Total Tumor Voxels', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(case_ids, rotation=45, ha='right', fontsize=8)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Format y-axis to show numbers in a readable format
    ax.ticklabel_format(style='plain', axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Tumor voxels graph saved to {output_path}")

def generate_dice_scores_graph(results: List[Dict], output_path: Path):
    """
    Generate a graph showing Dice scores for each MRI case.
    """
    if not results:
        print("No results to graph")
        return
    
    # Extract data
    case_ids = [r['case_id'] for r in results]
    dice_scores = [r['dice_score'] for r in results]
    
    # Create figure with appropriate size for number of cases
    n_cases = len(case_ids)
    fig_width = max(12, n_cases * 0.4)
    fig_height = 6
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Create bar chart
    colors = ['#2E86AB' if score >= 0.8 else '#F18F01' if score >= 0.6 else '#C73E1D' for score in dice_scores]
    bars = ax.bar(case_ids, dice_scores, color=colors, alpha=0.8)
    
    # Add reference line at 0.8
    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='Good (0.8)')
    ax.axhline(y=0.6, color='orange', linestyle='--', alpha=0.5, label='Fair (0.6)')
    
    # Customize the plot
    ax.set_xlabel('MRI Case', fontsize=12, fontweight='bold')
    ax.set_ylabel('Dice Score', fontsize=12, fontweight='bold')
    ax.set_title('Dice Scores by MRI Case', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(case_ids)))
    ax.set_xticklabels(case_ids, rotation=45, ha='right', fontsize=8)
    ax.set_ylim([0, 1.05])
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Dice scores graph saved to {output_path}")

# ============================================================
# MAIN EVALUATION PIPELINE
# ============================================================

def process_single_case(model: SegResNet, case_folder: Path, case_idx: int, total_cases: int) -> Optional[Dict]:
    """
    Process a single MRI case through the entire pipeline.
    
    Returns:
        Result dictionary with metrics, or None if processing fails.
    """
    case_name = case_folder.name
    print(f"[{case_idx}/{total_cases}] Processing {case_name}")
    
    try:
        # Load and preprocess
        preprocessed = load_and_preprocess_case(case_folder)
        if preprocessed is None:
            return None
        
        # Run inference
        print(f"    Running inference...")
        segmentation = run_inference(model, preprocessed["image"], device)
        
        # Calculate metrics
        print(f"    Calculating metrics...")
        metrics = calculate_metrics(preprocessed["ground_truth"], segmentation)
        
        # Add case ID to results
        metrics["case_id"] = case_name
        
        # Print results for this case
        print(f"    Results:")
        print(f"      GT tumor voxels: {metrics['ground_truth_tumor_voxels']:.0f}")
        print(f"      Pred tumor voxels: {metrics['predicted_tumor_voxels']:.0f}")
        print(f"      Dice: {metrics['dice_score']:.4f}")
        print(f"      IoU: {metrics['iou']:.4f}")
        
        # Clean up tensors to free memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return metrics
        
    except Exception as e:
        print(f"    Error: {str(e)}")
        return {
            "case_name": case_name,
            "error": str(e)
        }

def main():
    """
    Main evaluation pipeline.
    """
    print("=" * 60)
    print("MRI SEGMENTATION EVALUATION PIPELINE")
    print("=" * 60)
    print()
    
    # Discover cases
    print("Discovering MRI cases...")
    case_folders = discover_cases(INPUT_DIR)
    
    if not case_folders:
        print("No valid cases found in input directory.")
        print(f"Please place MRI case folders in: {INPUT_DIR}")
        return
    
    print(f"Found {len(case_folders)} valid cases to process")
    print()
    
    # Load model (once, reused for all cases)
    try:
        model = load_model(MODEL_PATH, device)
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return
    
    print()
    
    # Process all cases
    results = []
    failed_cases = []
    
    for idx, case_folder in enumerate(case_folders, 1):
        result = process_single_case(model, case_folder, idx, len(case_folders))
        
        if result and "error" not in result:
            results.append(result)
        else:
            failed_cases.append(result if result else {"case_name": case_folder.name, "error": "Unknown error"})
        
        print()
    
    # Save results
    print("=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    csv_path = RESULTS_DIR / "mri_segmentation_results.csv"
    summary_path = RESULTS_DIR / "mri_segmentation_summary.txt"
    figure1_path = RESULTS_DIR / "figure_1_tumor_voxels.png"
    figure1b_path = RESULTS_DIR / "figure_1b_dice_scores.png"
    
    save_results_to_csv(results, csv_path)
    save_summary_statistics(results, failed_cases, summary_path)
    generate_tumor_voxels_graph(results, figure1_path)
    generate_dice_scores_graph(results, figure1b_path)
    
    # Print final summary
    print()
    print("=" * 60)
    print("MRI EVALUATION COMPLETED")
    print("=" * 60)
    print(f"Cases processed: {len(results)}")
    print(f"Cases failed: {len(failed_cases)}")
    
    if results:
        dice_scores = [r['dice_score'] for r in results]
        ious = [r['iou'] for r in results]
        print(f"Mean Dice: {np.mean(dice_scores):.4f}")
        print(f"Mean IoU: {np.mean(ious):.4f}")
    
    print()
    print("Results:")
    print(f"  {csv_path}")
    print(f"  {summary_path}")
    print(f"  {figure1_path}")
    print(f"  {figure1b_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
