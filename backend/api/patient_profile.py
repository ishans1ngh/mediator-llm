from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.agents.reader_agent import ReaderAgent

router = APIRouter(prefix="/patient", tags=["patient"])
reader = ReaderAgent()

@router.post("/profile")
def build_profile(payload: Dict[str, Any]):
    clinical = payload.get("clinical_data", {})
    mri_data = payload.get("mri_data", {})
    
    clinical_profile = reader.read_clinical_data(clinical)
    mri_profile = reader.read_mri_data(mri_data)
    
    demo_source = "Clinical Dataset"
    mri_source = "MRI Analysis" if not mri_profile.get("demo_mode") else "DEMO MODE"
    
    def wrap(value, source=demo_source):
        return {"value": value, "source": source}
    
    profile = {
        "patient_id": clinical.get("patient_id", "unknown"),
        "brats_id": clinical.get("brats_id"),
        "demographics": {
            "age": wrap(clinical.get("age")),
            "sex": wrap(clinical.get("sex")),
            "race": wrap(clinical.get("race")),
            "ethnicity": wrap(clinical.get("ethnicity")),
        },
        "diagnosis": {
            "primary_diagnosis": wrap(clinical.get("diagnosis")),
            "who_diagnosis": wrap(clinical.get("who_diagnosis")),
            "non_who_diagnosis": wrap(clinical.get("non_who_diagnosis")),
            "tumor_type": wrap(clinical.get("tumor_type")),
            "disease": wrap(clinical.get("disease")),
            "grade": wrap(clinical.get("grade")),
        },
        "biomarkers": {
            "IDH_status": wrap(clinical.get("IDH_status")),
            "MGMT_status": wrap(clinical.get("MGMT_status")),
            "ATRX_status": wrap(clinical.get("ATRX_status")),
            "status_1p19q": wrap(clinical.get("1p19q_status")),
            "other": wrap(clinical.get("biomarkers")),
        },
        "treatment_history": {
            "surgery": wrap(clinical.get("surgery")),
            "surgery_extend": wrap(clinical.get("surgery_extend")),
            "number_of_surgeries": wrap(clinical.get("number_of_surgeries")),
            "radiation": wrap(clinical.get("radiation")),
            "number_of_radiation_courses": wrap(clinical.get("number_of_radiation_courses")),
            "chemotherapy": wrap(clinical.get("chemotherapy")),
            "immunotherapy": wrap(clinical.get("immunotherapy")),
            "other_treatment": wrap(clinical.get("other_treatment")),
            "overall_survival": wrap(clinical.get("overall_survival")),
            "progression_free_survival": wrap(clinical.get("progression_free_survival")),
        },
        "clinical_data": {
            "performance_status": wrap(clinical.get("performance_status")),
            "lab_values": wrap(clinical.get("lab_values")),
            "comorbidities": wrap(clinical.get("comorbidities")),
            "medications": wrap(clinical.get("medications")),
            "days_to_initial_surgery": wrap(clinical.get("days_to_initial_surgery")),
            "days_to_last_followup": wrap(clinical.get("days_to_last_followup")),
        },
        "imaging_metadata": {
            "manufacturer": wrap(clinical.get("manufacturer")),
            "manufacturer_model": wrap(clinical.get("manufacturer_model")),
            "magnetic_field_strength": wrap(clinical.get("magnetic_field_strength")),
        },
        "mri": {
            "scan_status": wrap(mri_profile.get("scan_status"), mri_source),
            "segmentation_status": wrap(mri_profile.get("segmentation", {}).get("segmentation_available"), mri_source),
            "tumor_detected": wrap(mri_profile.get("segmentation", {}).get("tumor_detected"), mri_source),
            "feature_vector_available": wrap(mri_profile.get("features", {}).get("feature_vector_available"), mri_source),
        },
        "source_info": {
            "clinical_data_available": bool(clinical),
            "mri_data_available": bool(mri_data),
            "demo_mode": mri_profile.get("demo_mode", False),
        }
    }
    
    return profile
