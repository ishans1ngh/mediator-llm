"""
Comparison module for Groq baseline vs Mediator-LLM.

This module compares the outputs of Groq and Mediator-LLM at both:
1. Overall eligibility decision level
2. Criterion-level decision level

It provides normalization functions and calculates agreement statistics.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter


class ComparisonNormalizer:
    """
    Normalization functions for comparing Groq and Mediator-LLM outputs.
    """
    
    @staticmethod
    def normalize_overall(overall: str) -> str:
        """
        Normalize overall eligibility label.
        
        Valid values: ELIGIBLE, NOT_ELIGIBLE, UNCERTAIN
        """
        if not overall or overall == "ERROR":
            return "ERROR"
        
        upper = overall.upper().strip()
        
        # Map various possible labels to standard values
        mapping = {
            "ELIGIBLE": "ELIGIBLE",
            "NOT ELIGIBLE": "NOT_ELIGIBLE",
            "NOT_ELIGIBLE": "NOT_ELIGIBLE",
            "INELIGIBLE": "NOT_ELIGIBLE",
            "UNCERTAIN": "UNCERTAIN",
            "UNKNOWN": "UNCERTAIN"
        }
        
        return mapping.get(upper, "ERROR")
    
    @staticmethod
    def normalize_decision(decision: str) -> str:
        """
        Normalize criterion decision label.
        
        Valid values: MET, NOT_MET, UNKNOWN
        """
        if not decision or decision == "ERROR":
            return "ERROR"
        
        upper = decision.upper().strip()
        
        # Map various possible labels to standard values
        mapping = {
            "MET": "MET",
            "NOT MET": "NOT_MET",
            "NOT_MET": "NOT_MET",
            "UNKNOWN": "UNKNOWN",
            "UNCERTAIN": "UNKNOWN"
        }
        
        return mapping.get(upper, "ERROR")
    
    @staticmethod
    def normalize_criterion_type(criterion_type: str) -> str:
        """
        Normalize criterion type.
        
        Valid values: INCLUSION, EXCLUSION
        """
        if not criterion_type:
            return "UNKNOWN"
        
        upper = criterion_type.upper().strip()
        
        if upper in ["INCLUSION", "EXCLUSION"]:
            return upper
        
        return "UNKNOWN"


class GroqMediatorComparator:
    """
    Comparator for Groq baseline vs Mediator-LLM results.
    """
    
    def __init__(self):
        self.normalizer = ComparisonNormalizer()
    
    def compare_overall(
        self, 
        groq_result: Dict[str, Any], 
        mediator_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare overall eligibility decisions.
        
        Args:
            groq_result: Groq evaluation result
            mediator_result: Mediator-LLM evaluation result
        
        Returns:
            Dictionary with comparison details
        """
        groq_overall = self.normalizer.normalize_overall(
            groq_result.get("overall_eligibility", "")
        )
        mediator_overall = self.normalizer.normalize_overall(
            mediator_result.get("overall_eligibility", "")
        )
        
        # Check for errors
        groq_error = groq_overall == "ERROR"
        mediator_error = mediator_overall == "ERROR"
        
        if groq_error or mediator_error:
            return {
                "groq_overall": groq_overall,
                "mediator_overall": mediator_overall,
                "agreement": None,
                "groq_error": groq_error,
                "mediator_error": mediator_error
            }
        
        # Determine agreement
        agreement = groq_overall == mediator_overall
        
        return {
            "groq_overall": groq_overall,
            "mediator_overall": mediator_overall,
            "agreement": agreement,
            "groq_error": False,
            "mediator_error": False
        }
    
    def compare_criteria(
        self, 
        groq_result: Dict[str, Any], 
        mediator_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare criterion-level decisions.
        
        Args:
            groq_result: Groq evaluation result
            mediator_result: Mediator-LLM evaluation result
        
        Returns:
            List of criterion-level comparisons
        """
        groq_criteria = groq_result.get("criteria", [])
        mediator_criteria = mediator_result.get("criteria", [])
        
        comparisons = []
        
        # Try to match criteria by index (assumes same order)
        # This is a simplified approach - in practice, you might want
        # to match by criterion text similarity
        max_len = max(len(groq_criteria), len(mediator_criteria))
        
        for i in range(max_len):
            groq_crit = groq_criteria[i] if i < len(groq_criteria) else None
            mediator_crit = mediator_criteria[i] if i < len(mediator_criteria) else None
            
            comparison = self._compare_single_criterion(groq_crit, mediator_crit, i)
            comparisons.append(comparison)
        
        return comparisons
    
    def _compare_single_criterion(
        self, 
        groq_crit: Optional[Dict[str, Any]], 
        mediator_crit: Optional[Dict[str, Any]],
        index: int
    ) -> Dict[str, Any]:
        """Compare a single criterion pair."""
        
        if groq_crit is None and mediator_crit is None:
            return {
                "index": index,
                "criterion": "MISSING_BOTH",
                "groq_decision": "MISSING",
                "mediator_decision": "MISSING",
                "agreement": None,
                "both_unknown": False
            }
        
        if groq_crit is None:
            return {
                "index": index,
                "criterion": mediator_crit.get("criterion", "UNKNOWN"),
                "groq_decision": "MISSING",
                "mediator_decision": self.normalizer.normalize_decision(
                    mediator_crit.get("decision", "")
                ),
                "agreement": None,
                "both_unknown": False
            }
        
        if mediator_crit is None:
            return {
                "index": index,
                "criterion": groq_crit.get("criterion", "UNKNOWN"),
                "groq_decision": self.normalizer.normalize_decision(
                    groq_crit.get("decision", "")
                ),
                "mediator_decision": "MISSING",
                "agreement": None,
                "both_unknown": False
            }
        
        # Both criteria exist
        groq_decision = self.normalizer.normalize_decision(
            groq_crit.get("decision", "")
        )
        mediator_decision = self.normalizer.normalize_decision(
            mediator_crit.get("decision", "")
        )
        
        # Check for errors
        if groq_decision == "ERROR" or mediator_decision == "ERROR":
            return {
                "index": index,
                "criterion": groq_crit.get("criterion", "UNKNOWN"),
                "groq_decision": groq_decision,
                "mediator_decision": mediator_decision,
                "agreement": None,
                "both_unknown": False
            }
        
        # Determine agreement
        agreement = groq_decision == mediator_decision
        both_unknown = (groq_decision == "UNKNOWN" and 
                       mediator_decision == "UNKNOWN")
        
        return {
            "index": index,
            "criterion": groq_crit.get("criterion", "UNKNOWN"),
            "criterion_type": groq_crit.get("type", "UNKNOWN"),
            "groq_decision": groq_decision,
            "mediator_decision": mediator_decision,
            "agreement": agreement,
            "both_unknown": both_unknown
        }
    
    def calculate_statistics(
        self, 
        overall_comparisons: List[Dict[str, Any]],
        criterion_comparisons: List[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Calculate overall statistics from comparisons.
        
        Args:
            overall_comparisons: List of overall decision comparisons
            criterion_comparisons: List of criterion-level comparisons per pair
        
        Returns:
            Dictionary with statistics
        """
        # Overall statistics
        total_pairs = len(overall_comparisons)
        valid_overall = [
            c for c in overall_comparisons 
            if not c.get("groq_error", False) and not c.get("mediator_error", False)
        ]
        same_overall = sum(1 for c in valid_overall if c.get("agreement", False))
        different_overall = len(valid_overall) - same_overall
        groq_errors = sum(1 for c in overall_comparisons if c.get("groq_error", False))
        mediator_errors = sum(1 for c in overall_comparisons if c.get("mediator_error", False))
        
        overall_agreement_rate = (
            same_overall / len(valid_overall) * 100 
            if valid_overall else 0
        )
        
        # Criterion-level statistics
        all_criterion_comparisons = []
        for comp_list in criterion_comparisons:
            all_criterion_comparisons.extend(comp_list)
        
        valid_criterion_comparisons = [
            c for c in all_criterion_comparisons 
            if c.get("agreement") is not None
        ]
        
        total_criterion_comparisons = len(valid_criterion_comparisons)
        criterion_agreements = sum(1 for c in valid_criterion_comparisons if c.get("agreement", False))
        criterion_disagreements = total_criterion_comparisons - criterion_agreements
        both_unknown = sum(1 for c in valid_criterion_comparisons if c.get("both_unknown", False))
        
        criterion_agreement_rate = (
            criterion_agreements / total_criterion_comparisons * 100 
            if total_criterion_comparisons > 0 else 0
        )
        
        return {
            "n_pairs": total_pairs,
            "valid_pairs": len(valid_overall),
            "overall_agreement_rate": overall_agreement_rate,
            "same_overall": same_overall,
            "different_overall": different_overall,
            "groq_errors": groq_errors,
            "mediator_errors": mediator_errors,
            "criterion_comparisons": total_criterion_comparisons,
            "criterion_agreements": criterion_agreements,
            "criterion_disagreements": criterion_disagreements,
            "criterion_agreement_rate": criterion_agreement_rate,
            "both_unknown": both_unknown
        }
    
    def create_comparison_csv(
        self, 
        patient_trial_pairs: List[Tuple[str, str]],
        overall_comparisons: List[Dict[str, Any]],
        criterion_comparisons: List[List[Dict[str, Any]]]
    ) -> pd.DataFrame:
        """
        Create a detailed comparison CSV.
        
        Args:
            patient_trial_pairs: List of (patient_id, trial_id) tuples
            overall_comparisons: List of overall decision comparisons
            criterion_comparisons: List of criterion-level comparisons per pair
        
        Returns:
            DataFrame with detailed comparison results
        """
        rows = []
        
        for idx, (patient_id, trial_id) in enumerate(patient_trial_pairs):
            overall_comp = overall_comparisons[idx]
            crit_comps = criterion_comparisons[idx]
            
            for crit_comp in crit_comps:
                rows.append({
                    "patient_id": patient_id,
                    "trial_id": trial_id,
                    "groq_overall": overall_comp.get("groq_overall", ""),
                    "mediator_overall": overall_comp.get("mediator_overall", ""),
                    "overall_agreement": overall_comp.get("agreement", ""),
                    "criterion_index": crit_comp.get("index", ""),
                    "criterion": crit_comp.get("criterion", ""),
                    "criterion_type": crit_comp.get("criterion_type", ""),
                    "groq_decision": crit_comp.get("groq_decision", ""),
                    "mediator_decision": crit_comp.get("mediator_decision", ""),
                    "criterion_agreement": crit_comp.get("agreement", ""),
                    "both_unknown": crit_comp.get("both_unknown", "")
                })
        
        return pd.DataFrame(rows)
