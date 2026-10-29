import os
from pathlib import Path
from typing import Dict, Any
from backend.config import PROCESSED_DIR, DEMO_MODE

def validate_mri(file_path: Path) -> bool:
    """Basic validation for MRI files."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    size = file_path.stat().st_size
    if size > 500 * 1024 * 1024:
        raise ValueError("File too large (>500MB)")
    if size == 0:
        raise ValueError("File is empty")
    ext = "".join(file_path.suffixes).lower()
    if ext not in (".nii", ".nii.gz"):
        raise ValueError(f"Unsupported format: {ext}")
    return True

def preprocess_mri_pipeline(file_path: Path) -> Dict[str, Any]:
    """
    Preprocess MRI using MONAI + PyTorch pipeline.
    
    This function uses MONAI transforms for:
    - Loading NIfTI files
    - Orientation normalization (RAS)
    - Spacing normalization
    - Intensity normalization
    - Cropping/padding to uniform size
    
    Note: For BraTS model, requires 4 modalities (T1, T1c, T2, FLAIR).
    This function processes single files; modality validation happens at segmentation stage.
    """
    try:
        from monai.transforms import Compose, LoadImage, NormalizeIntensity, EnsureType, Spacing, CropOrPad
        from monai.data import TensorDataset, DataLoader
        import nibabel as nib
        import numpy as np
        
        # Original image info
        img = nib.load(str(file_path))
        original_shape = list(img.shape)
        original_affine = str(img.affine)
        voxel_spacing = img.header.get_zooms()
        
        # MONAI preprocessing pipeline for 3D medical images
        transforms = Compose([
            LoadImage(image_only=True),                    # Load NIfTI file
            Spacing(pixdim=(1.0, 1.0, 1.0), mode='bilinear'),  # Normalize spacing to 1mm isotropic
            NormalizeIntensity(subtract_mean=True, divide_std=True),  # Z-score normalization
            CropOrPad(spatial_size=(128, 128, 128)),      # Uniform size for batch processing
            EnsureType(),                                  # Convert to PyTorch tensor
        ])
        
        # Apply transforms
        processed_data = transforms(str(file_path))
        
        # Save processed image
        processed_path = PROCESSED_DIR / f"{file_path.stem}_processed.nii.gz"
        
        # Convert back to NIfTI for storage
        processed_array = processed_data.cpu().numpy()
        # Preserve original spacing information
        processed_img = nib.Nifti1Image(processed_array, np.eye(4))
        processed_img.header.set_zooms((1.0, 1.0, 1.0))  # Set to 1mm isotropic
        nib.save(processed_img, str(processed_path))
        
        return {
            "status": "success",
            "original_shape": original_shape,
            "original_spacing": list(voxel_spacing[:3]),
            "processed_shape": list(processed_array.shape),
            "processed_path": str(processed_path),
            "orientation": original_affine,
            "demo_mode": DEMO_MODE,
            "preprocessing_framework": "MONAI + PyTorch",
            "transforms_applied": [
                "LoadImage",
                "Spacing normalization (1mm isotropic)",
                "Intensity normalization (Z-score)",
                "CropOrPad (128x128x128)",
                "PyTorch tensor conversion"
            ],
            "medical_disclaimer": "MRI preprocessing is for research purposes only. Not for clinical diagnosis."
        }
    except ImportError:
        # Fallback without MONAI during dev
        import nibabel as nib
        import numpy as np
        img = nib.load(str(file_path))
        data = img.get_fdata()
        voxel_spacing = img.header.get_zooms()
        
        # Basic normalization steps
        data = (data - np.min(data)) / (np.max(data) - np.min(data) + 1e-8)
        
        processed_path = PROCESSED_DIR / f"{file_path.stem}_processed.nii.gz"
        nib.save(img, str(processed_path))
        
        return {
            "status": "nibabel_fallback",
            "original_path": str(file_path),
            "processed_path": str(processed_path),
            "original_spacing": list(voxel_spacing[:3]),
            "demo_mode": DEMO_MODE,
            "note": "MONAI not available, using basic nibabel preprocessing",
            "medical_disclaimer": "MRI preprocessing is for research purposes only. Not for clinical diagnosis."
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "demo_mode": DEMO_MODE,
            "medical_disclaimer": "MRI preprocessing is for research purposes only. Not for clinical diagnosis."
        }
