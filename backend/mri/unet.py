from pathlib import Path
from typing import Dict, Any
import torch
import numpy as np
import nibabel as nib

from backend.config import MONAI_BUNDLE_DIR, DEMO_MODE, MRI_DEVICE


def check_monai_bundle() -> Dict[str, Any]:
    """Check that the MONAI BraTS bundle exists."""

    bundle_dir = Path(MONAI_BUNDLE_DIR)

    required_files = [
        bundle_dir / "configs" / "inference.json",
        bundle_dir / "models" / "model.pt",
    ]

    if not bundle_dir.exists():
        return {
            "available": False,
            "reason": "Bundle directory not found",
            "bundle_path": str(bundle_dir),
        }

    missing = [str(f) for f in required_files if not f.exists()]

    if missing:
        return {
            "available": False,
            "reason": "Required bundle files missing",
            "missing_files": missing,
            "bundle_path": str(bundle_dir),
        }

    return {
        "available": True,
        "bundle_path": str(bundle_dir),
        "model_path": str(bundle_dir / "models" / "model.pt"),
        "config_path": str(bundle_dir / "configs" / "inference.json"),
    }


def _load_and_normalize(path: str):
    """Load one NIfTI MRI volume and normalize non-zero voxels."""

    img = nib.load(path)
    data = img.get_fdata().astype(np.float32)

    mask = data != 0

    if np.any(mask):
        mean = data[mask].mean()
        std = data[mask].std()

        if std > 0:
            data[mask] = (data[mask] - mean) / std

    return data, img.affine


def run_unet_segmentation(preprocessed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run MONAI BraTS SegResNet using four MRI modalities:

    T1
    T1ce
    T2
    FLAIR
    """

    bundle_status = check_monai_bundle()

    if DEMO_MODE:
        return {
            "segmentation_available": False,
            "status": "demo_mode",
            "note": "Demo mode enabled.",
            "bundle_status": bundle_status,
        }

    if not bundle_status["available"]:
        return {
            "segmentation_available": False,
            "status": "model_unavailable",
            "error": bundle_status["reason"],
            "bundle_status": bundle_status,
        }

    try:
        from monai.networks.nets import SegResNet
        from monai.inferers import SlidingWindowInferer

        # ---------------------------------
        # Get modality paths
        # ---------------------------------

        modalities = preprocessed.get("modalities")

        if not modalities:
            return {
                "segmentation_available": False,
                "status": "missing_modalities",
                "error": (
                    "Four MRI modalities are required: "
                    "T1, T1ce, T2 and FLAIR."
                ),
            }

        required = ["t1", "t1ce", "t2", "flair"]

        missing = [
            modality
            for modality in required
            if not modalities.get(modality)
        ]

        if missing:
            return {
                "segmentation_available": False,
                "status": "missing_modalities",
                "missing_modalities": missing,
            }

        # ---------------------------------
        # Load MRI volumes
        # ---------------------------------

        t1, affine = _load_and_normalize(modalities["t1"])
        t1ce, _ = _load_and_normalize(modalities["t1ce"])
        t2, _ = _load_and_normalize(modalities["t2"])
        flair, _ = _load_and_normalize(modalities["flair"])

        # ---------------------------------
        # Validate dimensions
        # ---------------------------------

        shapes = {
            "t1": t1.shape,
            "t1ce": t1ce.shape,
            "t2": t2.shape,
            "flair": flair.shape,
        }

        if len(set(shapes.values())) != 1:
            return {
                "segmentation_available": False,
                "status": "dimension_mismatch",
                "shapes": shapes,
            }

        # ---------------------------------
        # Stack into 4-channel tensor
        #
        # Channel order:
        # T1, T1ce, T2, FLAIR
        # ---------------------------------

        image = np.stack(
            [t1, t1ce, t2, flair],
            axis=0,
        )

        image_tensor = (
            torch.from_numpy(image)
            .unsqueeze(0)
        )

        device = torch.device(
            MRI_DEVICE
            if torch.cuda.is_available()
            else "cpu"
        )

        image_tensor = image_tensor.to(device)

        # ---------------------------------
        # Create SegResNet
        # ---------------------------------

        model = SegResNet(
            blocks_down=(1, 2, 2, 4),
            blocks_up=(1, 1, 1),
            init_filters=16,
            in_channels=4,
            out_channels=3,
            dropout_prob=0.2,
        ).to(device)

        # ---------------------------------
        # Load MONAI pretrained weights
        # ---------------------------------

        checkpoint = torch.load(
            bundle_status["model_path"],
            map_location=device,
            weights_only=False,
        )

        if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            model.load_state_dict(checkpoint["state_dict"])
        elif isinstance(checkpoint, dict) and "model" in checkpoint:
            model.load_state_dict(checkpoint["model"])
        else:
            model.load_state_dict(checkpoint)

        model.eval()

        # ---------------------------------
        # Sliding-window inference
        # ---------------------------------

        inferer = SlidingWindowInferer(
            roi_size=(240, 240, 160),
            sw_batch_size=1,
            overlap=0.5,
        )

        with torch.no_grad():
            output = inferer(
                image_tensor,
                model,
            )

        # ---------------------------------
        # Convert 3 output channels
        # into BraTS labels
        # ---------------------------------

        probabilities = torch.sigmoid(output)

        prediction = (
            probabilities > 0.5
        ).cpu().numpy()[0]

        segmentation = np.zeros(
            prediction.shape[1:],
            dtype=np.uint8,
        )

        segmentation[prediction[0]] = 1
        segmentation[prediction[1]] = 2
        segmentation[prediction[2]] = 4

        # ---------------------------------
        # Save segmentation
        # ---------------------------------

        output_dir = Path(
            preprocessed.get(
                "output_dir",
                "backend/data/processed",
            )
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_dir /
            "mri_segmentation.nii.gz"
        )

        nib.save(
            nib.Nifti1Image(
                segmentation,
                affine,
            ),
            str(output_path),
        )

        # ---------------------------------
        # Calculate volumes
        # ---------------------------------

        voxel_volume = np.prod(
            nib.load(
                modalities["t1"]
            ).header.get_zooms()[:3]
        )

        regions = {}
        label_names = {
            1: "necrotic_core",
            2: "peritumoral_edema",
            4: "enhancing_tumor",
        }

        for label, name in label_names.items():
            voxel_count = int(
                np.sum(segmentation == label)
            )

            regions[name] = {
                "voxel_count": voxel_count,
                "volume_mm3": float(
                    voxel_count * voxel_volume
                ),
            }

        total_tumor_voxels = int(
            np.count_nonzero(segmentation)
        )

        return {
            "segmentation_available": True,
            "status": "success",
            "mask_path": str(output_path),
            "tumor_detected": total_tumor_voxels > 0,
            "total_tumor_voxels": total_tumor_voxels,
            "regions": regions,
            "framework": "MONAI + PyTorch",
            "model_architecture": "3D SegResNet",
            "input_channels": 4,
            "modalities_used": required,
            "device": str(device),
            "medical_disclaimer": (
                "MRI segmentation is for research purposes only. "
                "Not for clinical diagnosis."
            ),
        }

    except Exception as e:

        return {
            "segmentation_available": False,
            "status": "error",
            "error": str(e),
            "medical_disclaimer": (
                "MRI segmentation is for research purposes only. "
                "Not for clinical diagnosis."
            ),
        }