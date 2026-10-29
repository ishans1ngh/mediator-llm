from typing import Dict, Any, List

class ReaderAgent:
    """Reads and structures patient data from multiple sources."""
    
    def read_clinical_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "Clinical Dataset",
            "demographics": {
                "age": raw.get("age"),
                "sex": raw.get("sex"),
            },
            "diagnosis": {
                "primary_diagnosis": raw.get("diagnosis"),
                "tumor_type": raw.get("tumor_type"),
                "disease": raw.get("disease"),
            },
            "biomarkers": {
                "IDH_status": raw.get("IDH_status"),
                "MGMT_status": raw.get("MGMT_status"),
                "other": raw.get("biomarkers"),
            },
            "treatment_history": {
                "surgery": raw.get("surgery"),
                "radiation": raw.get("radiation"),
                "chemotherapy": raw.get("chemotherapy"),
                "immunotherapy": raw.get("immunotherapy"),
                "other": raw.get("prior_treatment"),
            },
            "clinical_data": {
                "performance_status": raw.get("performance_status"),
                "lab_values": raw.get("lab_values"),
                "comorbidities": raw.get("comorbidities"),
                "medications": raw.get("medications"),
            },
        }
    
    def read_mri_data(self, mri_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "MRI Analysis",
            "scan_status": mri_result.get("status"),
            "segmentation": mri_result.get("segmentation"),
            "features": mri_result.get("features"),
            "demo_mode": mri_result.get("demo_mode", False),
        }
