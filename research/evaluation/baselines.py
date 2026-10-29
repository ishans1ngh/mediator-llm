"""
Baseline implementations for clinical trial eligibility matching.

This module provides interfaces for three approaches:
1. Single LLM baseline
2. RAG + LLM baseline
3. Mediator-LLM (existing system)

All baselines operate on the same patient-trial pairs for fair comparison.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.patient_service import get_patient_by_id
from backend.trials.clinicaltrials_api import get_trial_by_nct
from backend.trials.eligibility import EligibilityEngine
from backend.llm.ollama_client import OllamaClient


class SingleLLMBaseline:
    """
    Single LLM baseline for eligibility determination.
    
    This approach uses a direct LLM call with patient and trial information
    without any RAG or specialized agents.
    """
    
    def __init__(self):
        self.llm_client = OllamaClient()
    
    def predict_eligibility(self, patient_id: str, trial_id: str) -> str:
        """
        Predict eligibility using single LLM approach.
        
        Returns: "ELIGIBLE", "NOT_ELIGIBLE", or "UNKNOWN"
        """
        try:
            # Get patient data
            patient = get_patient_by_id(patient_id)
            if not patient:
                return "UNKNOWN"
            
            # Get trial data
            trial = get_trial_by_nct(trial_id)
            if not trial:
                return "UNKNOWN"
            
            # Construct prompt for LLM
            prompt = self._construct_prompt(patient, trial)
            
            # Get LLM response
            response = self.llm_client.generate(prompt)
            
            # Parse response
            return self._parse_response(response)
            
        except Exception as e:
            print(f"Error in Single LLM baseline: {str(e)}")
            return "UNKNOWN"
    
    def _construct_prompt(self, patient: Dict[str, Any], trial: Dict[str, Any]) -> str:
        """Construct prompt for single LLM."""
        prompt = f"""
You are a clinical trial eligibility expert. Determine if this patient is eligible for the clinical trial.

PATIENT INFORMATION:
- Age: {patient.get('age', 'Unknown')}
- Sex: {patient.get('sex', 'Unknown')}
- Diagnosis: {patient.get('diagnosis', 'Unknown')}
- Grade: {patient.get('grade', 'Unknown')}
- IDH Status: {patient.get('IDH_status', 'Unknown')}
- MGMT Status: {patient.get('MGMT_status', 'Unknown')}
- Performance Status: {patient.get('performance_status', 'Unknown')}
- Surgery: {patient.get('surgery', 'Unknown')}
- Radiation: {patient.get('radiation', 'Unknown')}
- Chemotherapy: {patient.get('chemotherapy', 'Unknown')}

CLINICAL TRIAL:
- Title: {trial.get('title', 'Unknown')}
- Brief Summary: {trial.get('brief_summary', 'Unknown')}

INCLUSION CRITERIA:
{chr(10).join(trial.get('eligibility', {}).get('inclusion_criteria', []))}

EXCLUSION CRITERIA:
{chr(10).join(trial.get('eligibility', {}).get('exclusion_criteria', []))}

Based on the patient information and trial criteria, determine if the patient is ELIGIBLE or NOT_ELIGIBLE.
If there is insufficient information to make a determination, respond with UNKNOWN.

Respond with only one word: ELIGIBLE, NOT_ELIGIBLE, or UNKNOWN.
"""
        return prompt
    
    def _parse_response(self, response: str) -> str:
        """Parse LLM response to extract eligibility status."""
        response_upper = response.upper().strip()
        
        if "ELIGIBLE" in response_upper:
            return "ELIGIBLE"
        elif "NOT ELIGIBLE" in response_upper or "INELIGIBLE" in response_upper:
            return "NOT_ELIGIBLE"
        else:
            return "UNKNOWN"


class RAGLLMBaseline:
    """
    RAG + LLM baseline for eligibility determination.
    
    This approach uses retrieval-augmented generation with clinical trial
    information and patient data.
    """
    
    def __init__(self):
        self.llm_client = OllamaClient()
        # TODO: Initialize RAG components when available
        # self.vector_store = VectorStore()
        # self.retriever = TrialRetriever()
    
    def predict_eligibility(self, patient_id: str, trial_id: str) -> str:
        """
        Predict eligibility using RAG + LLM approach.
        
        Returns: "ELIGIBLE", "NOT_ELIGIBLE", or "UNKNOWN"
        """
        try:
            # Get patient data
            patient = get_patient_by_id(patient_id)
            if not patient:
                return "UNKNOWN"
            
            # Get trial data
            trial = get_trial_by_nct(trial_id)
            if not trial:
                return "UNKNOWN"
            
            # TODO: Implement RAG retrieval
            # For now, fall back to single LLM approach
            # retrieved_context = self._retrieve_relevant_trials(patient)
            
            # Construct prompt with retrieved context
            prompt = self._construct_prompt(patient, trial)
            
            # Get LLM response
            response = self.llm_client.generate(prompt)
            
            # Parse response
            return self._parse_response(response)
            
        except Exception as e:
            print(f"Error in RAG LLM baseline: {str(e)}")
            return "UNKNOWN"
    
    def _construct_prompt(self, patient: Dict[str, Any], trial: Dict[str, Any]) -> str:
        """Construct prompt for RAG + LLM."""
        # For now, use same prompt as single LLM
        # TODO: Enhance with retrieved context when RAG is implemented
        prompt = f"""
You are a clinical trial eligibility expert with access to retrieved clinical trial information.
Determine if this patient is eligible for the clinical trial.

PATIENT INFORMATION:
- Age: {patient.get('age', 'Unknown')}
- Sex: {patient.get('sex', 'Unknown')}
- Diagnosis: {patient.get('diagnosis', 'Unknown')}
- Grade: {patient.get('grade', 'Unknown')}
- IDH Status: {patient.get('IDH_status', 'Unknown')}
- MGMT Status: {patient.get('MGMT_status', 'Unknown')}
- Performance Status: {patient.get('performance_status', 'Unknown')}
- Surgery: {patient.get('surgery', 'Unknown')}
- Radiation: {patient.get('radiation', 'Unknown')}
- Chemotherapy: {patient.get('chemotherapy', 'Unknown')}

CLINICAL TRIAL:
- Title: {trial.get('title', 'Unknown')}
- Brief Summary: {trial.get('brief_summary', 'Unknown')}

INCLUSION CRITERIA:
{chr(10).join(trial.get('eligibility', {}).get('inclusion_criteria', []))}

EXCLUSION CRITERIA:
{chr(10).join(trial.get('eligibility', {}).get('exclusion_criteria', []))}

Based on the patient information and trial criteria, determine if the patient is ELIGIBLE or NOT_ELIGIBLE.
If there is insufficient information to make a determination, respond with UNKNOWN.

Respond with only one word: ELIGIBLE, NOT_ELIGIBLE, or UNKNOWN.
"""
        return prompt
    
    def _parse_response(self, response: str) -> str:
        """Parse LLM response to extract eligibility status."""
        response_upper = response.upper().strip()
        
        if "ELIGIBLE" in response_upper:
            return "ELIGIBLE"
        elif "NOT ELIGIBLE" in response_upper or "INELIGIBLE" in response_upper:
            return "NOT_ELIGIBLE"
        else:
            return "UNKNOWN"


class MediatorLLMBaseline:
    """
    Mediator-LLM baseline (existing system).
    
    This uses the full Mediator-LLM architecture with Matcher Agent,
    Verification Agent, and Explainer Agent.
    """
    
    def __init__(self):
        self.eligibility_engine = EligibilityEngine()
    
    def predict_eligibility(self, patient_id: str, trial_id: str) -> str:
        """
        Predict eligibility using Mediator-LLM approach.
        
        Returns: "ELIGIBLE", "NOT_ELIGIBLE", or "UNKNOWN"
        """
        try:
            # Get patient data
            patient = get_patient_by_id(patient_id)
            if not patient:
                return "UNKNOWN"
            
            # Get trial data
            trial = get_trial_by_nct(trial_id)
            if not trial:
                return "UNKNOWN"
            
            # Use existing eligibility engine
            result = self.eligibility_engine.evaluate(patient, trial)
            
            return result.final_status
            
        except Exception as e:
            print(f"Error in Mediator-LLM baseline: {str(e)}")
            return "UNKNOWN"


def get_baseline(baseline_type: str):
    """
    Factory function to get baseline implementation.
    
    Args:
        baseline_type: "single_llm", "rag_llm", or "mediator_llm"
    
    Returns:
        Baseline instance
    """
    if baseline_type == "single_llm":
        return SingleLLMBaseline()
    elif baseline_type == "rag_llm":
        return RAGLLMBaseline()
    elif baseline_type == "mediator_llm":
        return MediatorLLMBaseline()
    else:
        raise ValueError(f"Unknown baseline type: {baseline_type}")
