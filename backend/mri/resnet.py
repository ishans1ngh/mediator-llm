from pathlib import Path
from typing import Dict, Any
import torch
from backend.config import RESNET50_MODEL_PATH, DEMO_MODE

def extract_resnet_features(preprocessed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract MRI features using ResNet implemented in MONAI + PyTorch.
    
    This uses MONAI's ResNet implementation adapted for 3D medical images
    to extract deep features for tumor classification and analysis.
    """
    model_path = Path(RESNET50_MODEL_PATH)
    
    if DEMO_MODE:
        return {
            "feature_vector_available": False,
            "feature_dimension": None,
            "status": "demo_mode",
            "note": "DEMO MODE — ResNet features simulated. Provide trained model for real feature extraction.",
            "model_path": str(model_path)
        }
    
    if not model_path.exists():
        return {
            "feature_vector_available": False,
            "feature_dimension": None,
            "status": "model_unavailable",
            "note": "ResNet model not found. Expected at: " + str(model_path),
            "model_path": str(model_path)
        }
    
    try:
        from monai.networks.nets import ResNet
        from monai.transforms import Compose, LoadImage, EnsureType, ScaleIntensity
        from monai.data import TensorDataset, DataLoader
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize MONAI ResNet50 for 3D medical image feature extraction
        model = ResNet(
            block='basic',              # Basic building block
            layers=[3, 4, 6, 3],        # ResNet-50 architecture
            block_in_channels=[64, 128, 256, 512],
            n_input_channels=1,         # Single channel input
            conv1_t_stride=[2, 2, 2],  # 3D convolution stride
            conv1_t_size=[7, 7, 7],     # 3D kernel size
            feed_forward=False,         # Don't include classification head
        ).to(device)
        
        # Load trained weights
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        
        # Get processed file path
        processed_path = preprocessed.get("processed_path")
        if not processed_path:
            return {
                "feature_vector_available": False,
                "status": "error",
                "error": "No processed file path provided"
            }
        
        # MONAI preprocessing pipeline for feature extraction
        transforms = Compose([
            LoadImage(image_only=True),
            ScaleIntensity(),           # Normalize intensity to [0, 1]
            EnsureType(device=device),
        ])
        
        # Apply transforms and extract features
        image_tensor = transforms(processed_path)
        
        # Add batch dimension
        image_tensor = image_tensor.unsqueeze(0)
        
        # Extract features
        with torch.no_grad():
            features = model(image_tensor)
            # Reshape if needed
            if len(features.shape) > 2:
                features = features.view(features.size(0), -1)
        
        return {
            "feature_vector_available": True,
            "feature_dimension": features.shape[-1],
            "status": "success",
            "framework": "MONAI + PyTorch",
            "model_architecture": "3D ResNet-50 adapted for medical imaging",
            "feature_type": "deep_convolutional_features",
            "device": str(device),
            "model_path": str(model_path)
        }
    except Exception as e:
        return {
            "feature_vector_available": False,
            "feature_dimension": None,
            "status": f"error: {str(e)}",
            "error_details": str(e),
            "model_path": str(model_path)
        }
