from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.models.trial import TrialSearchRequest, TrialSearchResponse, TrialSummary
from backend.models.eligibility import MatchRequest, MatchResponse, EligibilityResult
from backend.trials.retriever import retrieve_trials_for_patient
from backend.trials.eligibility import EligibilityEngine
from backend.rag.vector_store import vector_store

router = APIRouter(prefix="/trials", tags=["trials"])
engine = EligibilityEngine()

@router.post("/search")
def search_trials(request: TrialSearchRequest):
    try:
        patient = request.patient_profile
        max_results = request.max_results
        trials = retrieve_trials_for_patient(patient, max_results=max_results)
        query_terms = []
        diagnosis = patient.get("diagnosis") or patient.get("disease")
        if diagnosis:
            query_terms.append(diagnosis)
        if patient.get("tumor_type"):
            query_terms.append(patient["tumor_type"])
        return {
            "trials": trials,
            "query_terms": query_terms,
            "total_found": len(trials),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trial search failed: {str(e)}")

@router.post("/match")
def match_trial(request: MatchRequest):
    try:
        result = engine.evaluate(request.patient_profile, request.trial)
        return {"result": result.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

@router.get("/{trial_id}")
def get_trial(trial_id: str):
    from backend.trials.clinicaltrials_api import get_trial_by_nct
    trial = get_trial_by_nct(trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return trial
