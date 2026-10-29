from typing import Dict, Any, List
from backend.models.eligibility import CriterionMatch, VerificationResult

class VerificationAgent:
    """Verifies matcher outputs and overrides unsupported conclusions."""
    
    def verify(self, matches: List[CriterionMatch], patient: Dict[str, Any]) -> VerificationResult:
        issues = []
        overrides = []
        
        for match in matches:
            # Check 1: If status is YES but patient_value is None or empty
            if match.status == "YES" and (match.patient_value is None or match.patient_value == ""):
                issue = f"Criterion '{match.criterion[:40]}...' marked YES but patient_value is missing"
                issues.append(issue)
                overrides.append({
                    "criterion_id": match.criterion_id,
                    "status": "UNKNOWN",
                    "reason": "Verification override: evidence missing despite YES conclusion",
                })
            
            # Check 2: Age consistency
            if "age" in match.criterion.lower() and match.patient_value is not None:
                age = patient.get("age")
                if age is not None and str(match.patient_value) != str(age):
                    issue = f"Age mismatch: match says {match.patient_value}, patient has {age}"
                    issues.append(issue)
            
            # Check 3: Contradiction in performance status
            if "ecog" in match.criterion.lower() or "performance" in match.criterion.lower():
                ps = patient.get("performance_status")
                if ps is None and match.status != "UNKNOWN":
                    issue = f"Performance status missing but criterion evaluated as {match.status}"
                    issues.append(issue)
                    overrides.append({
                        "criterion_id": match.criterion_id,
                        "status": "UNKNOWN",
                        "reason": "Verification override: performance status not available",
                    })
            
            # Check 4: Unsupported assumption detection
            if match.status in ("YES", "NO") and match.evidence_source == "Matcher Agent":
                if "not interpretable" in match.reason.lower():
                    issue = f"Criterion interpreted without direct patient evidence: {match.criterion[:50]}"
                    issues.append(issue)
                    overrides.append({
                        "criterion_id": match.criterion_id,
                        "status": "UNKNOWN",
                        "reason": "Verification override: unsupported assumption by matcher",
                    })
        
        return VerificationResult(
            verified=len(issues) == 0,
            issues=issues,
            overrides=overrides,
        )
