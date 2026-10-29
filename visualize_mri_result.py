import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# FILE PATHS
# ============================================================

MRI_PATH = Path(
    r"BraTS20_Training_367\BraTS20_Training_367_t1.nii"
)

MASK_PATH = Path(
    r"test_prediction.nii.gz"
)

OUTPUT_PATH = Path(
    r"Fig4_MRI_Segmentation_Result.png"
)

# ============================================================
# LOAD MRI
# ============================================================

print("Loading MRI...")

mri_img = nib.load(str(MRI_PATH))
mri = mri_img.get_fdata()

print("MRI shape:", mri.shape)

# ============================================================
# LOAD SEGMENTATION
# ============================================================

print("Loading segmentation...")

mask_img = nib.load(str(MASK_PATH))
mask = mask_img.get_fdata()

print("Mask shape:", mask.shape)

# ============================================================
# MAKE SURE DIMENSIONS MATCH
# ============================================================

if mri.shape != mask.shape:
    raise ValueError(
        f"MRI shape {mri.shape} does not match "
        f"mask shape {mask.shape}"
    )

# ============================================================
# FIND SLICE WITH MOST TUMOR
# ============================================================

tumor_voxels_per_slice = np.sum(mask > 0, axis=(0, 1))

best_slice = int(np.argmax(tumor_voxels_per_slice))

print("Selected slice:", best_slice)
print("Tumor voxels in selected slice:",
      tumor_voxels_per_slice[best_slice])

# ============================================================
# EXTRACT SLICE
# ============================================================

mri_slice = mri[:, :, best_slice]
mask_slice = mask[:, :, best_slice]

# Rotate for normal radiological-style display
mri_slice = np.rot90(mri_slice)
mask_slice = np.rot90(mask_slice)

# ============================================================
# NORMALIZE MRI
# ============================================================

p_low, p_high = np.percentile(
    mri_slice[mri_slice > 0],
    (1, 99)
)

mri_display = np.clip(
    (mri_slice - p_low) / (p_high - p_low),
    0,
    1
)

# ============================================================
# STATISTICS
# ============================================================

total_tumor_voxels = int(np.sum(mask > 0))

print("Total tumor voxels:", total_tumor_voxels)

# Try to calculate physical volume from NIfTI voxel spacing
voxel_spacing = mask_img.header.get_zooms()[:3]

voxel_volume_mm3 = np.prod(voxel_spacing)

tumor_volume_mm3 = total_tumor_voxels * voxel_volume_mm3
tumor_volume_cm3 = tumor_volume_mm3 / 1000

print("Voxel spacing:", voxel_spacing)
print("Tumor volume:", tumor_volume_mm3, "mm³")
print("Tumor volume:", tumor_volume_cm3, "cm³")

# ============================================================
# CREATE FIGURE
# ============================================================

fig, axes = plt.subplots(
    1,
    3,
    figsize=(15, 5)
)

# ------------------------------------------------------------
# 1. ORIGINAL MRI
# ------------------------------------------------------------

axes[0].imshow(
    mri_display,
    cmap="gray"
)

axes[0].set_title(
    "T1 MRI Slice",
    fontsize=14,
    fontweight="bold"
)

axes[0].axis("off")

# ------------------------------------------------------------
# 2. SEGMENTATION MASK
# ------------------------------------------------------------

axes[1].imshow(
    mask_slice > 0,
    cmap="gray"
)

axes[1].set_title(
    "Tumor Segmentation Mask",
    fontsize=14,
    fontweight="bold"
)

axes[1].axis("off")

# ------------------------------------------------------------
# 3. OVERLAY
# ------------------------------------------------------------

axes[2].imshow(
    mri_display,
    cmap="gray"
)

# Transparent tumor overlay
axes[2].imshow(
    np.ma.masked_where(
        mask_slice == 0,
        mask_slice
    ),
    cmap="autumn",
    alpha=0.55
)

axes[2].set_title(
    "MRI + Segmentation Overlay",
    fontsize=14,
    fontweight="bold"
)

axes[2].axis("off")

# ============================================================
# MAIN TITLE
# ============================================================

fig.suptitle(
    "MRI Segmentation Result — BraTS20_Training_367",
    fontsize=18,
    fontweight="bold"
)

# ============================================================
# STATISTICS BOX
# ============================================================

statistics = (
    f"Model: MONAI SegResNet\n"
    f"Input: T1, T1ce, T2, FLAIR\n"
    f"Volume: {mri.shape[0]} × {mri.shape[1]} × {mri.shape[2]}\n"
    f"Tumor detected: Yes\n"
    f"Tumor voxels: {total_tumor_voxels:,}\n"
    f"Tumor volume: {tumor_volume_cm3:.2f} cm³\n"
    f"Selected slice: {best_slice}"
)

fig.text(
    0.5,
    0.01,
    statistics,
    ha="center",
    va="bottom",
    fontsize=10
)

plt.tight_layout(
    rect=[0, 0.14, 1, 0.92]
)

# ============================================================
# SAVE
# ============================================================

plt.savefig(
    OUTPUT_PATH,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print()
print("=" * 60)
print("FIGURE CREATED SUCCESSFULLY")
print("=" * 60)
print("Saved to:", OUTPUT_PATH)