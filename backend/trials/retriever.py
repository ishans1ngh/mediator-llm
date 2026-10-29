from typing import List, Dict, Any
from backend.trials.clinicaltrials_api import search_trials
from backend.config import DEMO_MODE

def build_query_from_patient(patient: Dict[str, Any]) -> List[str]:
    terms = []
    
    # Primary diagnosis
    diagnosis = patient.get("diagnosis")
    if diagnosis:
        terms.append(diagnosis)
    
    # WHO 2021 diagnosis
    who_dx = patient.get("who_diagnosis")
    if who_dx and who_dx.lower() not in ("none", "nan", "unknown", "n/a"):
        terms.append(who_dx)
    
    # Non-WHO diagnosis
    non_who_dx = patient.get("non_who_diagnosis")
    if non_who_dx and non_who_dx.lower() not in ("none", "nan", "unknown", "n/a"):
        terms.append(non_who_dx)
    
    # Grade/tumor type
    grade = patient.get("grade")
    if grade and str(grade).lower() not in ("none", "nan", "unknown", "n/a"):
        terms.append("grade " + str(grade))
    
    # Broader disease terms
    lower_terms = [t.lower() for t in terms]
    if any("glioblastoma" in t for t in lower_terms):
        terms.extend(["glioma", "brain tumor"])
    if any("astrocytoma" in t for t in lower_terms):
        terms.extend(["glioma", "brain tumor"])
    if any("glioma" in t for t in lower_terms):
        terms.append("brain tumor")
    
    # Biomarker terms
    biomarkers = patient.get("biomarkers") or []
    if biomarkers:
        for b in biomarkers:
            b_lower = str(b).lower()
            if "mgmt" in b_lower:
                terms.append("MGMT")
            if "idh" in b_lower:
                terms.append("IDH")
            if "atrx" in b_lower:
                terms.append("ATRX")
            if "1p19q" in b_lower or "1p/19q" in b_lower:
                terms.append("1p/19q")
    
    # Direct biomarker fields
    if patient.get("MGMT_status"):
        terms.append("MGMT")
    if patient.get("IDH_status"):
        terms.append("IDH")
    if patient.get("ATRX_status"):
        terms.append("ATRX")
    if patient.get("status_1p19q"):
        terms.append("1p/19q")
    
    # Treatment history terms
    if patient.get("surgery"):
        terms.append("surgery")
    if patient.get("radiation"):
        terms.append("radiation")
    if patient.get("chemotherapy"):
        terms.append("chemotherapy")
    if patient.get("immunotherapy"):
        terms.append("immunotherapy")
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for t in terms:
        tl = t.lower().strip()
        if tl and tl not in seen and tl not in ("none", "nan", "unknown", "n/a"):
            seen.add(tl)
            unique.append(t)
    return unique

def score_trial_relevance(
    patient: Dict[str, Any],
    trial: Dict[str, Any]
) -> int:
    """
    Score how closely a trial matches the patient's known profile.

    This is a retrieval/ranking score only.
    It does NOT determine clinical eligibility.
    """

    score = 0

    diagnosis = str(
        patient.get("diagnosis")
        or patient.get("disease")
        or ""
    ).lower()

    grade = str(patient.get("grade") or "").lower()

    trial_text = " ".join([
        str(trial.get("title") or ""),
        str(trial.get("brief_summary") or ""),
        " ".join(map(str, trial.get("conditions") or [])),
        " ".join(map(str, trial.get("interventions") or [])),
        " ".join(
            map(
                str,
                (trial.get("eligibility") or {}).get(
                    "inclusion_criteria",
                    []
                )
            )
        ),
    ]).lower()

    # --------------------------------------------------
    # Disease match
    # --------------------------------------------------

    if "glioblastoma" in diagnosis:
        if "glioblastoma" in trial_text:
            score += 40
        elif "glioma" in trial_text:
            score += 20
        elif "brain tumor" in trial_text:
            score += 10

    # --------------------------------------------------
    # Grade match
    # --------------------------------------------------

    if grade:
        if f"grade {grade}" in trial_text:
            score += 15

    # --------------------------------------------------
    # Disease stage / recurrence
    # --------------------------------------------------

    recurrence_value = patient.get("recurrence") or patient.get("relapse")

    if recurrence_value is not None:
        recurrence_text = str(recurrence_value).lower()

        is_recurrent = recurrence_text in {
            "yes",
            "true",
            "recurrent",
            "relapsed",
            "progressive",
        }

        if is_recurrent:
            if "recurrent" in trial_text or "relapse" in trial_text:
                score += 25
            elif "newly diagnosed" in trial_text:
                score -= 25

        else:
            if "newly diagnosed" in trial_text:
                score += 25
            elif "recurrent" in trial_text or "relapse" in trial_text:
                score -= 25

    # --------------------------------------------------
    # Biomarkers
    # --------------------------------------------------

    biomarker_fields = [
        ("IDH_status", "idh"),
        ("MGMT_status", "mgmt"),
        ("ATRX_status", "atrx"),
        ("1p19q_status", "1p/19q"),
    ]

    for field, marker in biomarker_fields:
        value = patient.get(field)

        if value and str(value).lower() not in {
            "none",
            "nan",
            "unknown",
            "n/a",
        }:
            if marker in trial_text:
                score += 10

    # --------------------------------------------------
    # Trial status
    # --------------------------------------------------

    status = str(
        trial.get("status") or ""
    ).upper()

    if status == "RECRUITING":
        score += 10
    elif status in {
        "ACTIVE_NOT_RECRUITING",
        "NOT_YET_RECRUITING",
    }:
        score += 3
    elif status in {
        "COMPLETED",
        "WITHDRAWN",
        "TERMINATED",
    }:
        score -= 25

    return score

def retrieve_trials_for_patient(
    patient: Dict[str, Any],
    max_results: int = 20
) -> List[Dict[str, Any]]:

    diagnosis = (
        patient.get("diagnosis")
        or patient.get("disease")
        or "glioblastoma"
    )

    trials = search_trials(
        [diagnosis],
        max_results=max_results
    )

    if not trials and DEMO_MODE:
        trials = _demo_trials()

    # Rank trials by patient-specific relevance.
    for trial in trials:
        trial["relevance_score"] = score_trial_relevance(
            patient,
            trial
        )

    trials.sort(
        key=lambda x: x.get("relevance_score", 0),
        reverse=True
    )

    return trials

def _demo_trials() -> List[Dict[str, Any]]:
    return [
        {
            "trial_id": "NCT04534802",
            "nct_id": "NCT04534802",
            "title": "CAR T-Cell Therapy for Recurrent Glioblastoma",
            "brief_summary": "Phase I/II study evaluating safety and efficacy of CAR T-cells in recurrent GBM.",
            "status": "Recruiting",
            "conditions": ["Glioblastoma", "Recurrent Glioblastoma"],
            "interventions": ["CAR T-Cell Therapy"],
            "eligibility": {
                "minimum_age": "18 Years",
                "maximum_age": "75 Years",
                "sex": "ALL",
                "healthy_volunteers": False,
                "inclusion_criteria": [
                    "Histologically confirmed glioblastoma",
                    "Age >= 18 years",
                    "ECOG performance status 0-2",
                    "Adequate organ function",
                ],
                "exclusion_criteria": [
                    "Active infection",
                    "Pregnancy",
                    "Prior CAR T-cell therapy",
                ],
            },
            "locations": [],
            "source_url": "https://clinicaltrials.gov/study/NCT04534802",
            "phase": "Phase 1/Phase 2",
            "study_type": "Interventional",
            "sponsor": "City of Hope Medical Center",
        },
        {
            "trial_id": "NCT03970443",
            "nct_id": "NCT03970443",
            "title": "Dabrafenib and Trametinib in BRAF V600E-Mutant Glioma",
            "brief_summary": "Study evaluating dabrafenib plus trametinib in pediatric and adult patients with BRAF V600E-mutant glioma.",
            "status": "Active, not recruiting",
            "conditions": ["Glioma", "BRAF V600E Mutation"],
            "interventions": ["Dabrafenib", "Trametinib"],
            "eligibility": {
                "minimum_age": "1 Year",
                "maximum_age": "N/A",
                "sex": "ALL",
                "healthy_volunteers": False,
                "inclusion_criteria": [
                    "BRAF V600E-mutant glioma",
                    "Measurable disease",
                    "Age >= 1 year",
                ],
                "exclusion_criteria": [
                    "Prior treatment with BRAF or MEK inhibitor",
                    "Uncontrolled hypertension",
                ],
            },
            "locations": [],
            "source_url": "https://clinicaltrials.gov/study/NCT03970443",
            "phase": "Phase 2",
            "study_type": "Interventional",
            "sponsor": "Novartis Pharmaceuticals",
        },
        {
            "trial_id": "NCT04222292",
            "nct_id": "NCT04222292",
            "title": "Radiation Therapy and Temozolomide With or Without Pembrolizumab",
            "brief_summary": "Randomized phase 3 trial evaluating pembrolizumab with standard chemoradiation for newly diagnosed glioblastoma.",
            "status": "Completed",
            "conditions": ["Glioblastoma"],
            "interventions": ["Pembrolizumab", "Temozolomide", "Radiation Therapy"],
            "eligibility": {
                "minimum_age": "18 Years",
                "maximum_age": "N/A",
                "sex": "ALL",
                "healthy_volunteers": False,
                "inclusion_criteria": [
                    "Newly diagnosed glioblastoma",
                    "Age >= 18 years",
                    "Adequate bone marrow function",
                ],
                "exclusion_criteria": [
                    "Prior systemic therapy for GBM",
                    "Active autoimmune disease",
                    "Uncontrolled intercurrent illness",
                ],
            },
            "locations": [],
            "source_url": "https://clinicaltrials.gov/study/NCT04222292",
            "phase": "Phase 3",
            "study_type": "Interventional",
            "sponsor": "Merck Sharp & Dohme LLC",
        },
    ]
