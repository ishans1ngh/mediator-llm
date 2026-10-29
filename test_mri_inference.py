import os
import torch
import nibabel as nib
import numpy as np

from monai.networks.nets import SegResNet
from monai.inferers import SlidingWindowInferer

# -----------------------------
# Paths
# -----------------------------
MRI_DIR = r"C:\Users\ishan\Downloads\archive\BraTS2020_TrainingData\MICCAI_BraTS2020_TrainingData\BraTS20_Training_367"

MODEL_PATH = r"D:\mediator-llm\models\brats_mri_segmentation\models\model.pt"

OUTPUT_PATH = r"D:\mediator-llm\test_prediction.nii.gz"


# -----------------------------
# Device
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {device}")


# -----------------------------
# Load MRI
# -----------------------------
def load_mri(filename):
    path = os.path.join(MRI_DIR, filename)
    img = nib.load(path)
    data = img.get_fdata().astype(np.float32)

    print(f"{filename}: {data.shape}")

    return data, img.affine


flair, affine = load_mri("BraTS20_Training_367_flair.nii")
t1, _ = load_mri("BraTS20_Training_367_t1.nii")
t1ce, _ = load_mri("BraTS20_Training_367_t1ce.nii")
t2, _ = load_mri("BraTS20_Training_367_t2.nii")


# -----------------------------
# Validate dimensions
# -----------------------------
assert flair.shape == t1.shape == t1ce.shape == t2.shape, \
    "MRI dimensions do not match!"

print("MRI dimensions: OK")


# -----------------------------
# Normalize each modality
# -----------------------------
def normalize(volume):
    mask = volume != 0

    if np.any(mask):
        mean = volume[mask].mean()
        std = volume[mask].std()

        if std > 0:
            volume[mask] = (volume[mask] - mean) / std

    return volume


flair = normalize(flair)
t1 = normalize(t1)
t1ce = normalize(t1ce)
t2 = normalize(t2)


# -----------------------------
# Stack modalities
# Channel order:
# T1, T1ce, T2, FLAIR
# -----------------------------
image = np.stack(
    [t1, t1ce, t2, flair],
    axis=0
)

print(f"Input shape: {image.shape}")


# -----------------------------
# Convert to tensor
# -----------------------------
image_tensor = torch.from_numpy(image).unsqueeze(0).to(device)

print(f"Tensor shape: {image_tensor.shape}")


# -----------------------------
# Create SegResNet
# -----------------------------
model = SegResNet(
    blocks_down=(1, 2, 2, 4),
    blocks_up=(1, 1, 1),
    init_filters=16,
    in_channels=4,
    out_channels=3,
    dropout_prob=0.2,
).to(device)


# -----------------------------
# Load trained weights
# -----------------------------
checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=False
)

if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    model.load_state_dict(checkpoint["state_dict"])
elif isinstance(checkpoint, dict) and "model" in checkpoint:
    model.load_state_dict(checkpoint["model"])
else:
    model.load_state_dict(checkpoint)

print("Model weights loaded")


# -----------------------------
# Inference
# -----------------------------
model.eval()

inferer = SlidingWindowInferer(
    roi_size=(240, 240, 160),
    sw_batch_size=1,
    overlap=0.5
)

print("Running MRI inference...")

with torch.no_grad():
    output = inferer(
        image_tensor,
        model
    )

print(f"Raw output shape: {output.shape}")


# -----------------------------
# Convert predictions
# -----------------------------
probabilities = torch.sigmoid(output)

prediction = (probabilities > 0.5).cpu().numpy()[0]

# MONAI bundle mapping:
# channel 0 -> label 1
# channel 1 -> label 2
# channel 2 -> label 4

segmentation = np.zeros(prediction.shape[1:], dtype=np.uint8)

segmentation[prediction[0]] = 1
segmentation[prediction[1]] = 2
segmentation[prediction[2]] = 4


# -----------------------------
# Save result
# -----------------------------
nib.save(
    nib.Nifti1Image(segmentation, affine),
    OUTPUT_PATH
)


# -----------------------------
# Results
# -----------------------------
tumor_voxels = np.count_nonzero(segmentation)

print()
print("================================")
print("MRI INFERENCE SUCCESS")
print("================================")
print(f"Output: {OUTPUT_PATH}")
print(f"Segmentation shape: {segmentation.shape}")
print(f"Tumor voxels detected: {tumor_voxels}")
print("================================")