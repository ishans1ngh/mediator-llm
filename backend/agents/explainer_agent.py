from typing import Dict, Any, List
from backend.models.eligibility import CriterionMatch
from backend.config import DEMO_MODE

class ExplainerAgent:
    """Produces human-readable explanations of eligibility results using deterministic rules."""
    
    def __init__(self):
        pass
    
    def explain(self, inclusion: List[CriterionMatch], exclusion: List[CriterionMatch], unknown: List[CriterionMatch], final_status: str) -> str:
        """Generate explanation using rule-based approach."""
        return self._explain_rule_based(inclusion, exclusion, unknown, final_status)
    
    def _explain_rule_based(self, inclusion: List[CriterionMatch], exclusion: List[CriterionMatch], unknown: List[CriterionMatch], final_status: str) -> str:
        """Fallback rule-based explanation."""
        lines = [f"FINAL STATUS: {final_status}", ""]
        
        lines.append("INCLUSION CRITERIA:")
        for c in inclusion:
            lines.append(f"  [{c.status}] {c.criterion}")
            lines.append(f"      Patient: {c.patient_value}")
            lines.append(f"      Reason: {c.reason}")
            lines.append(f"      Source: {c.evidence_source}")
            lines.append("")
        
        lines.append("EXCLUSION CRITERIA:")
        for c in exclusion:
            lines.append(f"  [{c.status}] {c.criterion}")
            lines.append(f"      Patient: {c.patient_value}")
            lines.append(f"      Reason: {c.reason}")
            lines.append(f"      Source: {c.evidence_source}")
            lines.append("")
        
        if unknown:
            lines.append("UNKNOWN CRITERIA:")
            for c in unknown:
                lines.append(f"  [?] {c.criterion}")
                lines.append(f"      Reason: {c.reason}")
                lines.append("")
        
        if final_status == "UNKNOWN":
            lines.append("Additional patient information may be required to determine eligibility.")
        
        return "\n".join(lines)
