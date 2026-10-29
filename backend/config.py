import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

CLINICAL_DATA_PATH = os.getenv("CLINICAL_DATA_PATH", str(BASE_DIR / "data" / "patient_dataset.xlsx"))
CLINICALTRIALS_API_BASE = os.getenv("CLINICALTRIALS_API_BASE", "https://clinicaltrials.gov/api/v2")
UNET_MODEL_PATH = os.getenv("UNET_MODEL_PATH", str(BASE_DIR / "models" / "unet" / "model.pt"))
RESNET50_MODEL_PATH = os.getenv("RESNET50_MODEL_PATH", str(BASE_DIR / "models" / "resnet" / "model.pt"))

# MONAI Bundle Configuration
MONAI_BUNDLE_DIR = Path(os.getenv("MONAI_BUNDLE_DIR", str(Path(__file__).parent.parent / "models" / "brats_mri_segmentation")))
MRI_DEVICE = os.getenv("MRI_DEVICE", "cpu")
MRI_MODEL_NAME = "brats_mri_segmentation"
MRI_REQUIRED_MODALITIES = ["t1c", "t1", "t2", "flair"]
MRI_MODALITY_PATTERNS = {
    "t1c": ["_t1ce", "_t1c"],
    "t1": ["_t1"],
    "t2": ["_t2"],
    "flair": ["_flair"],
}

# RAG Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", str(BASE_DIR / "storage" / "vector_store"))
CACHE_PATH = os.getenv("CACHE_PATH", str(BASE_DIR / "storage" / "cache"))

# Trial Matching Configuration
MAX_TRIALS_PER_QUERY = int(os.getenv("MAX_TRIALS_PER_QUERY", "20"))

# Demo Mode
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "storage" / "mediator.db"))

# Groq Configuration for External LLM Baseline
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Storage Directories
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
PROCESSED_DIR = BASE_DIR / "storage" / "processed"
RESULTS_DIR = BASE_DIR / "storage" / "results"


def init_directories():
    for d in [
        UPLOAD_DIR,
        PROCESSED_DIR,
        RESULTS_DIR,
        Path(VECTOR_STORE_PATH),
        Path(CACHE_PATH),
        Path(DATABASE_PATH).parent,
    ]:
        d.mkdir(parents=True, exist_ok=True)


init_directories()
