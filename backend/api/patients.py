from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.services.patient_service import get_all_patients, get_patient_by_id
from backend.models.patient import PatientProfile

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("", response_model=List[Dict[str, Any]])
def list_patients():
    try:
        patients = get_all_patients()
        return patients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load patients: {str(e)}")

@router.get("/{patient_id}")
def get_patient(patient_id: str):
    patient = get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
