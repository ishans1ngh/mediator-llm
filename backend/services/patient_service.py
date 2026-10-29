import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import CLINICAL_DATA_PATH
from backend.database import get_connection

COLUMN_MAP = {
    "patient_id": ["ID", "patient_id", "Patient ID", "Subject ID", "subject_id", "PTGBM ID", "BraTS ID"],
    "brats_id": ["BraTS ID"],
    "age": ["Patient's Age", "Age", "age", "Age (years)", "AGE"],
    "sex": ["Sex at birth", "Sex", "sex", "Gender", "gender", "GENDER"],
    "race": ["Race"],
    "ethnicity": ["Ethnicity"],
    "diagnosis": ["Primary Diagnosis", "diagnosis", "Primary Diagnosis", "DX"],
    "who_diagnosis": ["WHO 2021 Diagnosis"],
    "non_who_diagnosis": ["Non WHO 2021 Diagnosis"],
    "tumor_type": ["Tumor Type", "tumor_type", "TumorType", "Histology", "Grade"],
    "grade": ["Grade"],
    "disease": ["Disease", "disease", "Condition", "condition", "Primary Diagnosis"],
    "IDH_status": ["IDH", "IDH_status", "idh_status"],
    "MGMT_status": ["MGMT", "MGMT_status", "mgmt_status"],
    "ATRX_status": ["ATRX"],
    "1p19q_status": ["1p19q"],
    "performance_status": ["ECOG", "Performance Status", "performance_status", "ECOG PS", "KPS"],
    "surgery": ["Surgery", "surgery", "Surgery History", "surgery_history", "Surgery "],
    "surgery_extend": ["Surgery extend"],
    "number_of_surgeries": ["Number of surgeries"],
    "radiation": ["Radiation", "radiation", "Radiation History", "radiation_history"],
    "number_of_radiation_courses": ["Number of radiation courses"],
    "chemotherapy": ["1st Chemo type", "Chemotherapy", "chemotherapy", "Chemo History", "chemotherapy_history"],
    "immunotherapy": ["Avastin (bevacizumab)", "Avastin� (bevacizumab)", "Immunotherapy", "immunotherapy", "Immuno History"],
    "other_treatment": ["Other treatment prior to scan", "prior_treatment", "Previous Treatment"],
    "overall_survival": ["Overall survival"],
    "progression_free_survival": ["Progression Free survival"],
    "days_to_initial_surgery": ["Days from Acquisition to Date of initial surgery, treatment or diagnosis "],
    "days_to_last_followup": ["Days from Acquisition to Date of last follow-up"],
    "manufacturer": ["Manufacturer"],
    "magnetic_field_strength": ["Magnetic Field Strength"],
    "manufacturer_model": ["Manufacturer's Model Name"],
}

def map_headers(headers: List[str]) -> Dict[str, str]:
    mapped = {}
    for standard, candidates in COLUMN_MAP.items():
        for h in headers:
            if h and h.strip() in candidates:
                mapped[h.strip()] = standard
                break
    return mapped

def load_patients() -> pd.DataFrame:
    path = Path(CLINICAL_DATA_PATH)
    if not path.exists():
        return _create_demo_dataset(path)
    # Try to read from "Cinical info" sheet first, then fall back to default
    try:
        df = pd.read_excel(path, sheet_name="Cinical info", engine="openpyxl")
    except:
        df = pd.read_excel(path, engine="openpyxl")
    return df

def _create_demo_dataset(path: Path) -> pd.DataFrame:
    import os
    os.makedirs(path.parent, exist_ok=True)
    data = [
        {
            "ID": "PTGBM-001",
            "BraTS ID": "BraTS-GLI-00001-000",
            "Patient's Age": 54,
            "Sex at birth": "Male",
            "Primary Diagnosis": "Glioblastoma",
            "WHO 2021 Diagnosis": "None",
            "Non WHO 2021 Diagnosis": "Glioblastoma",
            "Grade": "4",
            "MGMT": "Methylated",
            "IDH": "Wild type",
            "1p19q": "Intact",
            "ATRX": "Loss",
            "Surgery ": "Yes",
            "Radiation": "Yes",
            "1st Chemo type": "Temozolomide",
            "Avastin (bevacizumab)": "No",
            "Other treatment prior to scan": "None",
            "Overall survival": 539,
            "Progression Free survival": 391,
        },
    ]
    df = pd.DataFrame(data)
    df.to_excel(path, index=False, engine="openpyxl")
    return df

def normalize_patient(row: pd.Series, mapped_headers: Dict[str, str]) -> Dict[str, Any]:
    def get(field):
        for h, std in mapped_headers.items():
            if std == field:
                val = row.get(h)
                if pd.isna(val):
                    return None
                return val
        return None

    def to_bool(val):
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        s = str(val).lower().strip()
        if s in ("yes", "true", "1", "y"):
            return True
        if s in ("no", "false", "0", "n", "none"):
            return False
        return None

    def to_list(val):
        if val is None:
            return None
        if isinstance(val, list):
            return val
        s = str(val).strip()
        if s.lower() in ("none", "nan", ""):
            return []
        return [x.strip() for x in s.split(",") if x.strip()]

    def clean_str(val):
        if val is None:
            return None
        s = str(val).strip()
        if s.lower() in ("none", "nan", "unknown", "n/a"):
            return None
        return s

    biomarkers = []
    for marker, field in [("MGMT", "MGMT_status"), ("IDH", "IDH_status"), ("ATRX", "ATRX_status"), ("1p19q", "1p19q_status")]:
        val = clean_str(get(field))
        if val:
            biomarkers.append(f"{marker}: {val}")

    diagnosis = clean_str(get("diagnosis"))
    who_dx = clean_str(get("who_diagnosis"))
    non_who_dx = clean_str(get("non_who_diagnosis"))
    final_diagnosis = diagnosis or who_dx or non_who_dx

    return {
        "patient_id": clean_str(get("patient_id")) or str(row.iloc[0]),
        "brats_id": clean_str(get("brats_id")),
        "age": int(get("age")) if get("age") is not None else None,
        "sex": clean_str(get("sex")),
        "race": clean_str(get("race")),
        "ethnicity": clean_str(get("ethnicity")),
        "diagnosis": final_diagnosis,
        "who_diagnosis": who_dx,
        "non_who_diagnosis": non_who_dx,
        "tumor_type": clean_str(get("tumor_type")),
        "grade": clean_str(get("grade")),
        "disease": clean_str(get("disease")),
        "IDH_status": clean_str(get("IDH_status")),
        "MGMT_status": clean_str(get("MGMT_status")),
        "ATRX_status": clean_str(get("ATRX_status")),
        "1p19q_status": clean_str(get("status_1p19q")),
        "biomarkers": biomarkers if biomarkers else None,
        "performance_status": clean_str(get("performance_status")),
        "surgery": to_bool(get("surgery")),
        "surgery_extend": clean_str(get("surgery_extend")),
        "number_of_surgeries": get("number_of_surgeries"),
        "radiation": to_bool(get("radiation")),
        "number_of_radiation_courses": get("number_of_radiation_courses"),
        "chemotherapy": clean_str(get("chemotherapy")),
        "immunotherapy": to_bool(get("immunotherapy")),
        "other_treatment": clean_str(get("other_treatment")),
        "overall_survival": get("overall_survival"),
        "progression_free_survival": get("progression_free_survival"),
        "days_to_initial_surgery": get("days_to_initial_surgery"),
        "days_to_last_followup": get("days_to_last_followup"),
        "manufacturer": clean_str(get("manufacturer")),
        "magnetic_field_strength": get("magnetic_field_strength"),
        "manufacturer_model": clean_str(get("manufacturer_model")),
    }

def get_all_patients() -> List[Dict[str, Any]]:
    df = load_patients()
    mapped = map_headers(list(df.columns))
    patients = []
    for _, row in df.iterrows():
        patients.append(normalize_patient(row, mapped))
    return patients

def get_patient_by_id(patient_id: str) -> Optional[Dict[str, Any]]:
    patients = get_all_patients()
    for p in patients:
        if str(p.get("patient_id")) == str(patient_id):
            return p
    return None
