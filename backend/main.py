from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import init_directories, DEMO_MODE, MONAI_BUNDLE_DIR, RESNET50_MODEL_PATH
from backend.database import init_db
from backend.api import patients, mri, trials, patient_profile
from backend.mri.unet import check_monai_bundle
from pathlib import Path

app = FastAPI(
    title="Mediator-LLM API",
    description="Agentic Clinical Trial Matching System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(patients.router, prefix="/api")
app.include_router(mri.router, prefix="/api")
app.include_router(trials.router, prefix="/api")
app.include_router(patient_profile.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "mediator-llm"}

@app.get("/api/models/status")
def models_status():
    """Get status of ML models (MONAI bundle, ResNet)."""
    monai_status = check_monai_bundle()
    
    resnet_path = Path(RESNET50_MODEL_PATH)
    resnet_status = {
        "available": resnet_path.exists(),
        "path": str(resnet_path)
    }
    
    return {
        "demo_mode": DEMO_MODE,
        "monai_bundle": monai_status,
        "resnet": resnet_status
    }