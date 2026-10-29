from typing import Dict, Any, List
from backend.models.eligibility import EligibilityResult, CriterionMatch, VerificationResult
from backend.agents.matcher_agent import MatcherAgent
from backend.agents.verification_agent import VerificationAgent
from backend.agents.explainer_agent import ExplainerAgent

class EligibilityEngine:
    def __init__(self):
        self.matcher = MatcherAgent()
        self.verifier = VerificationAgent()
        self.explainer = ExplainerAgent()
    
    def evaluate(self, patient: Dict[str, Any], trial: Dict[str, Any]) -> EligibilityResult:
        trial_id = trial.get("trial_id", "unknown")
        title = trial.get("title", "Untitled")
        
        # 1. Match criteria
        inclusion = self.matcher.match_inclusion(patient, trial.get("eligibility", {}))
        exclusion = self.matcher.match_exclusion(patient, trial.get("eligibility", {}))
        unknown = self.matcher.match_unknown(patient, trial.get("eligibility", {}))
        
        # 2. Verify
        verification = self.verifier.verify(inclusion + exclusion + unknown, patient)
        
        # Apply verification overrides
        for override in verification.overrides:
            for item in inclusion + exclusion + unknown:
                if item.criterion_id == override.get("criterion_id"):
                    item.status = override.get("status", item.status)
                    item.reason = override.get("reason", item.reason)
        
        # 3. Deterministic final eligibility
        final_status = self._determine_final_status(inclusion, exclusion, unknown)
        
        # 4. Explain
        explanation = self.explainer.explain(inclusion, exclusion, unknown, final_status)
        
        yes_count = sum(1 for c in inclusion if c.status == "YES")
        no_count = sum(1 for c in (inclusion + exclusion) if c.status == "NO")
        unk_count = sum(1 for c in (inclusion + exclusion + unknown) if c.status == "UNKNOWN")
        
        return EligibilityResult(
            trial_id=trial_id,
            title=title,
            final_status=final_status,
            criteria_summary={"yes": yes_count, "no": no_count, "unknown": unk_count},
            inclusion=inclusion,
            exclusion=exclusion,
            unknown=unknown,
            verification=verification,
            source_url=trial.get("source_url"),
            explanation=explanation,
        )
    
    def _determine_final_status(self, inclusion: List[CriterionMatch], exclusion: List[CriterionMatch], unknown: List[CriterionMatch]) -> str:
        # Inclusion: if any NO -> NOT_ELIGIBLE
        for c in inclusion:
            if c.status == "NO":
                return "NOT_ELIGIBLE"
        
        # If any inclusion UNKNOWN (and no NO) -> UNKNOWN
        for c in inclusion:
            if c.status == "UNKNOWN":
                return "UNKNOWN"
        
        # Exclusion: if any YES (patient satisfies exclusion) -> NOT_ELIGIBLE
        for c in exclusion:
            if c.status == "YES":
                return "NOT_ELIGIBLE"
        
        # If any exclusion UNKNOWN -> UNKNOWN
        for c in exclusion:
            if c.status == "UNKNOWN":
                return "UNKNOWN"
        
        # All inclusion YES and all exclusion NO -> ELIGIBLE
        return "ELIGIBLE"
