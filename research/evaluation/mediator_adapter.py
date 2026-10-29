"""
Mediator-LLM adapter to extract and normalize criterion-level results.

This module adapts the existing Mediator-LLM eligibility engine output to match
the standardized schema used for comparison with the Groq baseline.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.patient_service import get_patient_by_id
from backend.trials.clinicaltrials_api import get_trial_by_nct
from backend.trials.eligibility import EligibilityEngine


class MediatorAdapter:
    """
    Adapter to normalize Mediator-LLM output to standardized schema.
    
    This class extracts criterion-level decisions from the existing
    Mediator-LLM eligibility engine and normalizes them to match
    the Groq baseline schema for fair comparison.
    """
    
    def __init__(self):
        self.eligibility_engine = EligibilityEngine()
    
    def evaluate_pair(
        self, 
        patient_id: str, 
        trial_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single patient-trial pair using Mediator-LLM.
        
        Args:
            patient_id: Patient identifier
            trial_id: Clinical trial NCT ID
        
        Returns:
            Dictionary with overall_eligibility, criteria list, and reasoning_summary
            in the same schema as Groq baseline
        """
        # Get patient and trial data
        patient = get_patient_by_id(patient_id)
        if not patient:
            return self._error_result("Patient not found")
        
        trial = get_trial_by_nct(trial_id)
        if not trial:
            return self._error_result("Trial not found")
        
        # Use existing eligibility engine
        try:
            result = self.eligibility_engine.evaluate(patient, trial)
        except Exception as e:
            return self._error_result(f"Eligibility engine error: {str(e)}")
        
        # Normalize to Groq schema
        normalized = self._normalize_result(result)
        
        return normalized
    
    def _normalize_result(self, result) -> Dict[str, Any]:
        """
        Normalize Mediator-LLM EligibilityResult to Groq schema.
        
        Mapping:
        - final_status -> overall_eligibility
        - inclusion criteria -> type: "INCLUSION", status "YES" -> "MET", "NO" -> "NOT_MET"
        - exclusion criteria -> type: "EXCLUSION", status "YES" -> "MET", "NO" -> "NOT_MET"
        - reason -> evidence
        """
        criteria = []
        
        # Process inclusion criteria
        for inc in result.inclusion:
            criteria.append({
                "criterion": inc.criterion,
                "type": "INCLUSION",
                "decision": self._normalize_status(inc.status, "inclusion"),
                "evidence": inc.reason
            })
        
        # Process exclusion criteria
        for exc in result.exclusion:
            criteria.append({
                "criterion": exc.criterion,
                "type": "EXCLUSION",
                "decision": self._normalize_status(exc.status, "exclusion"),
                "evidence": exc.reason
            })
        
        # Process unknown criteria
        for unk in result.unknown:
            criteria.append({
                "criterion": unk.criterion,
                "type": "UNKNOWN",
                "decision": "UNKNOWN",
                "evidence": unk.reason
            })
        
        # Normalize overall eligibility
        overall_eligibility = self._normalize_overall(result.final_status)
        
        # Build reasoning summary from explanation
        reasoning_summary = result.explanation or ""
        
        return {
            "overall_eligibility": overall_eligibility,
            "criteria": criteria,
            "reasoning_summary": reasoning_summary
        }
    
    def _normalize_status(self, status: str, criterion_type: str) -> str:
        """
        Normalize Mediator status to Groq decision format.
        
        Mediator uses "YES", "NO", "UNKNOWN"
        Groq uses "MET", "NOT_MET", "UNKNOWN"
        
        For inclusion:
        - YES -> MET (patient meets inclusion criterion)
        - NO -> NOT_MET (patient does not meet inclusion criterion)
        - UNKNOWN -> UNKNOWN
        
        For exclusion:
        - YES -> MET (patient satisfies exclusion criterion, which is bad)
        - NO -> NOT_MET (patient does not satisfy exclusion criterion, which is good)
        - UNKNOWN -> UNKNOWN
        """
        if status == "UNKNOWN":
            return "UNKNOWN"
        
        if criterion_type == "inclusion":
            if status == "YES":
                return "MET"
            elif status == "NO":
                return "NOT_MET"
        
        elif criterion_type == "exclusion":
            if status == "YES":
                return "MET"  # Exclusion criterion is met by patient
            elif status == "NO":
                return "NOT_MET"  # Exclusion criterion not met by patient
        
        # Default to UNKNOWN for any unexpected status
        return "UNKNOWN"
    
    def _normalize_overall(self, final_status: str) -> str:
        """
        Normalize Mediator final_status to Groq overall_eligibility format.
        
        Both use the same values: ELIGIBLE, NOT_ELIGIBLE, UNKNOWN
        """
        valid_values = ["ELIGIBLE", "NOT_ELIGIBLE", "UNKNOWN"]
        if final_status in valid_values:
            return final_status
        return "UNKNOWN"
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return error result structure."""
        return {
            "overall_eligibility": "ERROR",
            "criteria": [],
            "reasoning_summary": f"Error: {error_message}",
            "error": error_message
        }


def run_mediator_adapter(patient_id: str, trial_id: str) -> Dict[str, Any]:
    """
    Convenience function to run Mediator-LLM adapter on a single pair.
    
    Args:
        patient_id: Patient identifier
        trial_id: Clinical trial NCT ID
    
    Returns:
        Dictionary with normalized evaluation results
    """
    adapter = MediatorAdapter()
    return adapter.evaluate_pair(patient_id, trial_id)
