import re
from typing import Dict, Any, List

from backend.models.eligibility import CriterionMatch
from backend.config import DEMO_MODE


class MatcherAgent:
    """
    Deterministic eligibility matcher.

    Important:
    - YES means the available patient data supports the criterion.
    - NO means the available patient data contradicts the criterion.
    - UNKNOWN means the available data is insufficient to determine eligibility.

    The matcher intentionally avoids guessing when clinical information is missing.
    """

    def __init__(self):
        pass

    # ============================================================
    # PUBLIC MATCHING METHODS
    # ============================================================

    def match_inclusion(
        self,
        patient: Dict[str, Any],
        eligibility: Dict[str, Any]
    ) -> List[CriterionMatch]:

        results = []
        criteria = eligibility.get("inclusion_criteria", [])

        for idx, text in enumerate(criteria):
            results.append(
                self._evaluate_criterion(
                    patient,
                    text,
                    "inclusion",
                    idx
                )
            )

        return results

    def match_exclusion(
        self,
        patient: Dict[str, Any],
        eligibility: Dict[str, Any]
    ) -> List[CriterionMatch]:

        results = []
        criteria = eligibility.get("exclusion_criteria", [])

        for idx, text in enumerate(criteria):
            results.append(
                self._evaluate_criterion(
                    patient,
                    text,
                    "exclusion",
                    idx
                )
            )

        return results

    def match_unknown(
        self,
        patient: Dict[str, Any],
        eligibility: Dict[str, Any]
    ) -> List[CriterionMatch]:

        return []

    # ============================================================
    # MAIN ROUTER
    # ============================================================

    def _evaluate_criterion(
        self,
        patient: Dict[str, Any],
        text: str,
        criterion_type: str,
        idx: int
    ) -> CriterionMatch:

        text_lower = text.lower().strip()

        # --------------------------------------------------------
        # 1. Age
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "age",
            "years old",
            "years of age",
            "years and older",
            "years or older",
            "years and younger",
            "years or younger"
        ]):
            return self._match_age(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 2. Sex
        #
        # Word boundaries are important.
        # "men" must NOT match "treatment".
        # --------------------------------------------------------

        sex_terms = [
            "sex",
            "gender",
            "male",
            "female",
            "men",
            "women"
        ]

        if any(
            re.search(
                rf"\b{re.escape(term)}\b",
                text_lower
            )
            for term in sex_terms
        ):
            return self._match_sex(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 3. Pregnancy / reproductive
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "pregnant",
            "pregnancy",
            "breastfeeding",
            "breast feeding",
            "lactating",
            "childbearing",
            "contraception"
        ]):
            return self._match_pregnancy(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 4. ECOG / Performance Status
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "ecog",
            "performance status",
            "kps",
            "karnofsky",
            "performance score"
        ]):
            return self._match_performance_status(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 5. Detect biomarker requirements
        # --------------------------------------------------------

        biomarker_terms = [
            "mgmt",
            "idh",
            "atrx",
            "1p19q",
            "1p/19q",
            "braf",
            "biomarker",
            "mutation",
            "molecular",
            "methylated",
            "unmethylated",
            "wild type",
            "wild-type"
        ]

        has_biomarker = any(
            term in text_lower
            for term in biomarker_terms
        )

        # --------------------------------------------------------
        # Study-policy / investigator-discretion criteria
        # --------------------------------------------------------
        
        policy_phrases = [
            "new standard of care",
            "before the first patient is enrolled",
            "at the discretion of the investigator",
            "maximum patient accrual",
            "open label randomized",
        ]
        
        if any(phrase in text_lower for phrase in policy_phrases):
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Study-policy/investigator-discretion criterion requires manual review."
            )

        # --------------------------------------------------------
        # 6. Detect diagnosis requirement
        # --------------------------------------------------------

        diagnosis_terms = [
            "glioblastoma",
            "gbm",
            "glioma",
            "astrocytoma",
            "oligodendroglioma",
            "brain tumor",
            "brain tumour",
            "histologically confirmed",
            "histologic diagnosis"
        ]

        has_diagnosis = any(
            term in text_lower
            for term in diagnosis_terms
        )

        # --------------------------------------------------------
        # 7. Grade
        #
        # Grade can coexist with diagnosis and biomarkers.
        # For a mixed criterion we handle all components together.
        # --------------------------------------------------------

        has_grade = bool(
            re.search(
                r"\b(?:who\s+)?grade\s*[1-4]\b",
                text_lower
            )
        )

        # --------------------------------------------------------
        # 8. Treatment / surgery indicators
        # --------------------------------------------------------

        treatment_terms = [
            "surgery",
            "resection",
            "resected",
            "radiation",
            "radiotherapy",
            "chemotherapy",
            "temozolomide",
            "systemic therapy",
            "immunotherapy",
            "bevacizumab",
            "avastin",
            "clinical intervention",
            "prior treatment",
            "previous treatment",
            "additional therapy",
            "treatment",
            "therapy"
        ]

        has_treatment = any(
            term in text_lower
            for term in treatment_terms
        )

        # --------------------------------------------------------
        # 9. Mixed diagnosis + biomarker + grade criterion
        #
        # Example:
        #
        # "newly diagnosed WHO grade 4 glioblastoma,
        #  IDH-1 R132H wild type"
        #
        # We need to check ALL available components.
        # --------------------------------------------------------

        if has_diagnosis and (has_biomarker or has_grade):
            return self._match_mixed_diagnosis(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 10. Surgery / resection
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "maximum safe resection",
            "extent of resection",
            "resection extent",
            "gross total resection",
            "resected",
            "resection",
            "surgery"
        ]):
            return self._match_treatment_history(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 11. Radiation / chemotherapy / treatment
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "radiation",
            "radiotherapy",
            "chemotherapy",
            "temozolomide",
            "systemic therapy",
            "immunotherapy",
            "bevacizumab",
            "avastin",
            "prior treatment",
            "previous treatment",
            "additional therapy",
            "clinical intervention"
        ]):
            return self._match_treatment_history(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 12. Pure biomarker criterion
        # --------------------------------------------------------

        if has_biomarker:
            return self._match_biomarkers(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 13. Pure diagnosis criterion
        #
        # IMPORTANT:
        #
        # "Any diagnosis or medical condition..."
        # is NOT automatically a diagnosis requirement.
        # It represents an investigator judgment.
        # --------------------------------------------------------

        if has_diagnosis:

            investigator_discretion_terms = [
                "any diagnosis",
                "any medical condition",
                "investigator feels",
                "investigator discretion",
                "precludes the patient",
                "preclude the patient"
            ]

            if any(
                term in text_lower
                for term in investigator_discretion_terms
            ):
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Criterion depends on investigator assessment; patient data is insufficient for automatic determination."
                )

            return self._match_diagnosis(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 14. Grade
        # --------------------------------------------------------

        if has_grade:
            return self._match_grade(
                patient,
                text,
                criterion_type,
                idx
            )

        # --------------------------------------------------------
        # 15. Default
        # --------------------------------------------------------

        return self._unknown(
            text,
            criterion_type,
            idx,
            "Criterion not interpretable by current rules; insufficient evidence."
        )

    # ============================================================
    # MIXED DIAGNOSIS / GRADE / BIOMARKER
    # ============================================================

    def _match_mixed_diagnosis(
        self,
        patient,
        text,
        criterion_type,
        idx
    ) -> CriterionMatch:

        checks = []
        evidence = []

        text_lower = text.lower()

        # --------------------------------------------------------
        # Diagnosis
        # --------------------------------------------------------

        diagnosis = (
            patient.get("diagnosis")
            or patient.get("who_diagnosis")
            or patient.get("non_who_diagnosis")
            or ""
        )

        diagnosis_combined = " ".join([
            str(patient.get("diagnosis") or ""),
            str(patient.get("who_diagnosis") or ""),
            str(patient.get("non_who_diagnosis") or "")
        ]).lower()

        required_diagnosis = None

        if "glioblastoma" in text_lower or "gbm" in text_lower:
            required_diagnosis = "glioblastoma"

        elif "astrocytoma" in text_lower:
            required_diagnosis = "astrocytoma"

        elif "oligodendroglioma" in text_lower:
            required_diagnosis = "oligodendroglioma"

        elif "glioma" in text_lower:
            required_diagnosis = "glioma"

        if required_diagnosis:

            if not diagnosis_combined.strip():
                checks.append("UNKNOWN")
                evidence.append(
                    "Patient diagnosis is not available."
                )

            elif required_diagnosis in diagnosis_combined:
                checks.append("YES")
                evidence.append(
                    f"Diagnosis matches {required_diagnosis}."
                )

            else:
                checks.append("NO")
                evidence.append(
                    f"Patient diagnosis ({diagnosis}) does not match required diagnosis ({required_diagnosis})."
                )

        # --------------------------------------------------------
        # Grade
        # --------------------------------------------------------

        required_grades = re.findall(
            r"\b(?:who\s+)?grade\s*(\d+)\b",
            text_lower
        )

        if required_grades:

            patient_grade = patient.get("grade")

            if patient_grade is None:
                checks.append("UNKNOWN")
                evidence.append(
                    "Patient tumor grade is not available."
                )

            elif str(patient_grade).strip() in required_grades:
                checks.append("YES")
                evidence.append(
                    f"Patient grade ({patient_grade}) matches required grade."
                )

            else:
                checks.append("NO")
                evidence.append(
                    f"Patient grade ({patient_grade}) does not match required grade {', '.join(required_grades)}."
                )

        # --------------------------------------------------------
        # IDH
        # --------------------------------------------------------

        if "idh" in text_lower:

            idh = patient.get("IDH_status")

            if idh is None:
                checks.append("UNKNOWN")
                evidence.append(
                    "Patient IDH status is not available."
                )

            else:
                idh_lower = str(idh).lower()

                # Wild type
                if (
                    "wild type" in text_lower
                    or "wild-type" in text_lower
                ):

                    if "wild" in idh_lower:
                        checks.append("YES")
                        evidence.append(
                            f"Patient IDH status ({idh}) matches wild-type requirement."
                        )
                    else:
                        checks.append("NO")
                        evidence.append(
                            f"Patient IDH status ({idh}) does not match wild-type requirement."
                        )

                # Mutant
                elif "mutant" in text_lower:
                    if (
                        "mutant" in idh_lower
                        or "mutation" in idh_lower
                    ):
                        checks.append("YES")
                        evidence.append(
                            f"Patient IDH status ({idh}) matches mutant requirement."
                        )
                    else:
                        checks.append("NO")
                        evidence.append(
                            f"Patient IDH status ({idh}) does not match mutant requirement."
                        )

                else:
                    checks.append("UNKNOWN")
                    evidence.append(
                        f"IDH requirement could not be precisely parsed from criterion."
                    )

        # --------------------------------------------------------
        # MGMT
        # --------------------------------------------------------

        if "mgmt" in text_lower:

            mgmt = patient.get("MGMT_status")

            if mgmt is None:
                checks.append("UNKNOWN")
                evidence.append(
                    "Patient MGMT status is not available."
                )

            else:
                mgmt_lower = str(mgmt).lower()

                if "methylated" in text_lower:

                    if "methylated" in mgmt_lower:
                        checks.append("YES")
                        evidence.append(
                            f"Patient MGMT status ({mgmt}) matches methylated requirement."
                        )
                    else:
                        checks.append("NO")
                        evidence.append(
                            f"Patient MGMT status ({mgmt}) does not match methylated requirement."
                        )

                elif "unmethylated" in text_lower:

                    if "unmethylated" in mgmt_lower:
                        checks.append("YES")
                        evidence.append(
                            f"Patient MGMT status ({mgmt}) matches unmethylated requirement."
                        )
                    else:
                        checks.append("NO")
                        evidence.append(
                            f"Patient MGMT status ({mgmt}) does not match unmethylated requirement."
                        )

        # --------------------------------------------------------
        # ATRX
        # --------------------------------------------------------

        if "atrx" in text_lower:

            atrx = patient.get("ATRX_status")

            if atrx is None:
                checks.append("UNKNOWN")
                evidence.append(
                    "Patient ATRX status is not available."
                )
            else:
                checks.append("YES")
                evidence.append(
                    f"Patient ATRX status available: {atrx}."
                )

        # --------------------------------------------------------
        # 1p/19q
        # --------------------------------------------------------

        if "1p19q" in text_lower or "1p/19q" in text_lower:

            p19q = (
                patient.get("1p19q_status")
                or patient.get("status_1p19q")
            )

            if p19q is None:
                checks.append("UNKNOWN")
                evidence.append(
                    "Patient 1p/19q status is not available."
                )
            else:
                checks.append("YES")
                evidence.append(
                    f"Patient 1p/19q status available: {p19q}."
                )

        # --------------------------------------------------------
        # Final mixed result
        # --------------------------------------------------------

        if not checks:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Mixed criterion could not be parsed."
            )

        if "NO" in checks:

            status = (
                "NO"
                if criterion_type == "inclusion"
                else "YES"
            )

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value={
                    "diagnosis": patient.get("diagnosis"),
                    "grade": patient.get("grade"),
                    "IDH": patient.get("IDH_status"),
                    "MGMT": patient.get("MGMT_status"),
                    "ATRX": patient.get("ATRX_status"),
                    "1p19q": (
                        patient.get("1p19q_status")
                        or patient.get("status_1p19q")
                    )
                },
                required_value=text,
                status=status,
                reason="; ".join(evidence),
                evidence_source="Clinical Dataset"
            )

        if "UNKNOWN" in checks:

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value={
                    "diagnosis": patient.get("diagnosis"),
                    "grade": patient.get("grade"),
                    "IDH": patient.get("IDH_status"),
                    "MGMT": patient.get("MGMT_status"),
                    "ATRX": patient.get("ATRX_status"),
                    "1p19q": (
                        patient.get("1p19q_status")
                        or patient.get("status_1p19q")
                    )
                },
                required_value=text,
                status="UNKNOWN",
                reason="; ".join(evidence),
                evidence_source="Clinical Dataset"
            )

        # Every component passed
        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value={
                "diagnosis": patient.get("diagnosis"),
                "grade": patient.get("grade"),
                "IDH": patient.get("IDH_status"),
                "MGMT": patient.get("MGMT_status"),
                "ATRX": patient.get("ATRX_status"),
                "1p19q": (
                    patient.get("1p19q_status")
                    or patient.get("status_1p19q")
                )
            },
            required_value=text,
            status="YES" if criterion_type == "inclusion" else "NO",
            reason="; ".join(evidence),
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # AGE
    # ============================================================

    def _match_age(self, patient, text, criterion_type, idx):

        age = patient.get("age")

        min_age = self._extract_min_age(text)
        max_age = self._extract_max_age(text)

        if age is None:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Patient age not available."
            )

        if min_age is not None and age < min_age:

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=age,
                required_value=f">= {min_age}",
                status="NO" if criterion_type == "inclusion" else "YES",
                reason=f"Patient age is {age}, below required minimum {min_age}.",
                evidence_source="Clinical Dataset"
            )

        if max_age is not None and age > max_age:

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=age,
                required_value=f"<= {max_age}",
                status="NO" if criterion_type == "inclusion" else "YES",
                reason=f"Patient age is {age}, above required maximum {max_age}.",
                evidence_source="Clinical Dataset"
            )

        if min_age is None and max_age is None:

            return self._unknown(
                text,
                criterion_type,
                idx,
                "Could not parse age requirement."
            )

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value=age,
            required_value=f"min={min_age}, max={max_age}",
            status="YES" if criterion_type == "inclusion" else "NO",
            reason=f"Patient age is {age}, satisfies age requirement.",
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # PERFORMANCE STATUS
    # ============================================================

    def _match_performance_status(
        self,
        patient,
        text,
        criterion_type,
        idx
    ):

        ps = patient.get("performance_status")

        if ps is None:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Performance status not available."
            )

        ps_val = self._parse_performance_status(ps)
        max_allowed = self._extract_ecog_max(text)

        if ps_val is None or max_allowed is None:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Could not parse performance status requirement."
            )

        if ps_val <= max_allowed:

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=ps,
                required_value=f"<= {max_allowed}",
                status="YES" if criterion_type == "inclusion" else "NO",
                reason=f"Performance status {ps} is within acceptable range.",
                evidence_source="Clinical Dataset"
            )

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value=ps,
            required_value=f"<= {max_allowed}",
            status="NO" if criterion_type == "inclusion" else "YES",
            reason=f"Performance status {ps} exceeds required maximum {max_allowed}.",
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # SEX
    # ============================================================

    def _match_sex(self, patient, text, criterion_type, idx):

        sex = patient.get("sex")

        if sex is None:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Patient sex not available."
            )

        required = self._extract_required_sex(text)

        if not required:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Could not parse sex requirement."
            )

        if sex.lower() == required.lower():

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=sex,
                required_value=required,
                status="YES" if criterion_type == "inclusion" else "NO",
                reason=f"Patient sex ({sex}) matches required sex ({required}).",
                evidence_source="Clinical Dataset"
            )

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value=sex,
            required_value=required,
            status="NO" if criterion_type == "inclusion" else "YES",
            reason=f"Patient sex ({sex}) does not match required sex ({required}).",
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # DIAGNOSIS
    # ============================================================

    def _match_diagnosis(
        self,
        patient,
        text,
        criterion_type,
        idx
    ):

        diagnosis = patient.get("diagnosis") or ""
        who_dx = patient.get("who_diagnosis") or ""
        non_who_dx = patient.get("non_who_diagnosis") or ""

        combined = (
            f"{diagnosis} {who_dx} {non_who_dx}"
        ).lower()

        if not combined.strip():
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Patient diagnosis/disease not available."
            )

        diag_terms = [
            "glioblastoma",
            "gbm",
            "astrocytoma",
            "glioma",
            "oligodendroglioma"
        ]

        required_terms = [
            term
            for term in diag_terms
            if term in text.lower()
        ]

        if not required_terms:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Could not identify a specific diagnosis requirement."
            )

        matched = any(
            term in combined
            for term in required_terms
        )

        if matched:

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=patient.get("diagnosis"),
                required_value=text,
                status="YES" if criterion_type == "inclusion" else "NO",
                reason=f"Patient diagnosis ({diagnosis}) is consistent with criterion.",
                evidence_source="Clinical Dataset"
            )

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value=patient.get("diagnosis"),
            required_value=text,
            status="NO" if criterion_type == "inclusion" else "YES",
            reason=f"Patient diagnosis ({diagnosis}) does not match criterion.",
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # GRADE
    # ============================================================

    def _match_grade(
        self,
        patient,
        text,
        criterion_type,
        idx
    ):

        grade = patient.get("grade")

        if grade is None:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Tumor grade not available."
            )

        req_grades = re.findall(
            r"\b(?:who\s+)?grade\s*(\d+)\b",
            text,
            re.IGNORECASE
        )

        if not req_grades:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Could not parse grade requirement."
            )

        patient_grade = str(grade).strip()

        matched = patient_grade in req_grades

        if matched:

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=grade,
                required_value=f"Grade {', '.join(req_grades)}",
                status="YES" if criterion_type == "inclusion" else "NO",
                reason=f"Patient grade ({grade}) matches required grade.",
                evidence_source="Clinical Dataset"
            )

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value=grade,
            required_value=f"Grade {', '.join(req_grades)}",
            status="NO" if criterion_type == "inclusion" else "YES",
            reason=f"Patient grade ({grade}) does not match required grade.",
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # BIOMARKERS
    # ============================================================

    def _match_biomarkers(
        self,
        patient,
        text,
        criterion_type,
        idx
    ):

        mgmt = patient.get("MGMT_status")
        idh = patient.get("IDH_status")
        atrx = patient.get("ATRX_status")

        # Support BOTH field names.
        p19q = (
            patient.get("1p19q_status")
            or patient.get("status_1p19q")
        )

        biomarkers = patient.get("biomarkers") or []

        text_lower = text.lower()

        bio_str = " ".join(
            str(x)
            for x in biomarkers
        ).lower()

        if mgmt:
            bio_str += f" mgmt {mgmt}".lower()

        if idh:
            bio_str += f" idh {idh}".lower()

        if atrx:
            bio_str += f" atrx {atrx}".lower()

        if p19q:
            bio_str += f" 1p19q {p19q}".lower()

        # --------------------------------------------------------
        # MGMT
        # --------------------------------------------------------

        if "mgmt" in text_lower:

            if mgmt is None:
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Patient MGMT status is not available."
                )

            mgmt_lower = str(mgmt).lower()

            if "unmethylated" in text_lower:

                matched = "unmethylated" in mgmt_lower

            elif "methylated" in text_lower:

                matched = "methylated" in mgmt_lower

            else:
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Could not parse specific MGMT requirement."
                )

            return self._biomarker_result(
                patient,
                text,
                criterion_type,
                idx,
                matched,
                f"Patient MGMT status ({mgmt}) "
                f"{'matches' if matched else 'does not match'} "
                f"the required criterion."
            )

        # --------------------------------------------------------
        # IDH
        # --------------------------------------------------------

        if "idh" in text_lower:

            if idh is None:
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Patient IDH status is not available."
                )

            idh_lower = str(idh).lower()

            if (
                "wild type" in text_lower
                or "wild-type" in text_lower
            ):

                matched = "wild" in idh_lower

            elif "mutant" in text_lower:

                matched = (
                    "mutant" in idh_lower
                    or "mutation" in idh_lower
                )

            else:
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Could not parse specific IDH requirement."
                )

            return self._biomarker_result(
                patient,
                text,
                criterion_type,
                idx,
                matched,
                f"Patient IDH status ({idh}) "
                f"{'matches' if matched else 'does not match'} "
                f"the required criterion."
            )

        # --------------------------------------------------------
        # ATRX
        # --------------------------------------------------------

        if "atrx" in text_lower:

            if atrx is None:
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Patient ATRX status is not available."
                )

            return self._biomarker_result(
                patient,
                text,
                criterion_type,
                idx,
                True,
                f"Patient ATRX status is available: {atrx}."
            )

        # --------------------------------------------------------
        # 1p/19q
        # --------------------------------------------------------

        if (
            "1p19q" in text_lower
            or "1p/19q" in text_lower
        ):

            if p19q is None:
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Patient 1p/19q status is not available."
                )

            return self._biomarker_result(
                patient,
                text,
                criterion_type,
                idx,
                True,
                f"Patient 1p/19q status is available: {p19q}."
            )

        # --------------------------------------------------------
        # Generic biomarker criterion
        # --------------------------------------------------------

        if not biomarkers and not mgmt and not idh and not atrx and not p19q:

            return self._unknown(
                text,
                criterion_type,
                idx,
                "Biomarker data not available."
            )

        return self._unknown(
            text,
            criterion_type,
            idx,
            "Could not parse specific biomarker requirement."
        )

    # ============================================================
    # BIOMARKER RESULT HELPER
    # ============================================================

    def _biomarker_result(
        self,
        patient,
        text,
        criterion_type,
        idx,
        matched,
        reason
    ):

        patient_value = {
            "MGMT": patient.get("MGMT_status"),
            "IDH": patient.get("IDH_status"),
            "ATRX": patient.get("ATRX_status"),
            "1p19q": (
                patient.get("1p19q_status")
                or patient.get("status_1p19q")
            )
        }

        if matched:

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=patient_value,
                required_value=text,
                status="YES" if criterion_type == "inclusion" else "NO",
                reason=reason,
                evidence_source="Clinical Dataset"
            )

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value=patient_value,
            required_value=text,
            status="NO" if criterion_type == "inclusion" else "YES",
            reason=reason,
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # TREATMENT HISTORY
    # ============================================================

    def _match_treatment_history(
        self,
        patient,
        text,
        criterion_type,
        idx
    ):

        surgery = patient.get("surgery")
        surgery_extend = patient.get("surgery_extend")
        radiation = patient.get("radiation")
        chemotherapy = patient.get("chemotherapy")
        immunotherapy = patient.get("immunotherapy")
        other = patient.get("other_treatment")

        text_lower = text.lower()

        # --------------------------------------------------------
        # Surgery / resection
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "surgery",
            "resection",
            "resected"
        ]):

            # Exact percentage requirement
            percentage_match = re.search(
                r"(?:>=|≥|at least)\s*(\d+)\s*%",
                text
            )

            if percentage_match:
                required_percentage = int(
                    percentage_match.group(1)
                )

                # Look for an actual resection percentage in patient data
                possible_percentage = (
                    patient.get("resection_percentage")
                    or patient.get("percent_resected")
                    or patient.get("resection_percent")
                )

                if possible_percentage is None:
                    return self._unknown(
                        text,
                        criterion_type,
                        idx,
                        f"Exact resection percentage (>= {required_percentage}%) is not available."
                    )

                try:
                    actual_percentage = float(
                        possible_percentage
                    )
                except (TypeError, ValueError):
                    return self._unknown(
                        text,
                        criterion_type,
                        idx,
                        "Could not parse the patient's resection percentage."
                    )

                matched = actual_percentage >= required_percentage

                return CriterionMatch(
                    criterion_id=f"{criterion_type}_{idx}",
                    criterion=text,
                    patient_value=actual_percentage,
                    required_value=f">= {required_percentage}%",
                    status=(
                        "YES"
                        if matched and criterion_type == "inclusion"
                        else "NO"
                        if matched
                        else "NO"
                        if criterion_type == "inclusion"
                        else "YES"
                    ),
                    reason=(
                        f"Patient resection percentage is "
                        f"{actual_percentage}%, required >= "
                        f"{required_percentage}%."
                    ),
                    evidence_source="Clinical Dataset"
                )

            # GTR alone does NOT prove a numerical percentage.
            if (
                "maximum safe resection" in text_lower
                or "70%" in text_lower
                or "%" in text_lower
            ):
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Surgery extent is documented, but the required resection percentage is not available."
                )

            if surgery is None and surgery_extend is None:
                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Surgery/resection history is not available."
                )

        # --------------------------------------------------------
        # Radiation
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "radiation",
            "radiotherapy"
        ]):

            if radiation is None:

                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Radiation history is not available."
                )

        # --------------------------------------------------------
        # Chemotherapy
        # --------------------------------------------------------

        if any(k in text_lower for k in [
            "chemotherapy",
            "temozolomide",
            "chemo"
        ]):

            if chemotherapy is None:

                return self._unknown(
                    text,
                    criterion_type,
                    idx,
                    "Chemotherapy history is not available."
                )

        # --------------------------------------------------------
        # Complex treatment criteria
        #
        # Do NOT assume that simply having treatment data means
        # the patient satisfies a complicated criterion.
        # --------------------------------------------------------

        complex_terms = [
            "within",
            "additional",
            "prevent",
            "uniform treatment",
            "up to",
            "cycles",
            "plan to receive",
            "before",
            "new standard of care",
            "clinical intervention",
            "investigator"
        ]

        if any(
            term in text_lower
            for term in complex_terms
        ):

            return self._unknown(
                text,
                criterion_type,
                idx,
                "Treatment information is present, but the exact timing/condition cannot be determined automatically; manual review required."
            )

        # --------------------------------------------------------
        # Simple treatment presence criterion
        # --------------------------------------------------------

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value={
                "surgery": surgery,
                "surgery_extend": surgery_extend,
                "radiation": radiation,
                "chemotherapy": chemotherapy,
                "immunotherapy": immunotherapy,
                "other": other
            },
            required_value=text,
            status="YES" if criterion_type == "inclusion" else "NO",
            reason="Required treatment history is available.",
            evidence_source="Clinical Dataset"
        )

    # ============================================================
    # PREGNANCY
    # ============================================================

    def _match_pregnancy(
        self,
        patient,
        text,
        criterion_type,
        idx
    ):

        sex = patient.get("sex")

        if sex is None:
            return self._unknown(
                text,
                criterion_type,
                idx,
                "Patient sex not available; cannot evaluate pregnancy-related criterion."
            )

        if sex.lower() == "male":

            return CriterionMatch(
                criterion_id=f"{criterion_type}_{idx}",
                criterion=text,
                patient_value=sex,
                required_value=text,
                status="NO" if criterion_type == "exclusion" else "YES",
                reason="Patient is male; pregnancy criterion does not apply.",
                evidence_source="Clinical Dataset"
            )

        return self._unknown(
            text,
            criterion_type,
            idx,
            "Pregnancy status not documented; requires manual verification."
        )

    # ============================================================
    # UNKNOWN HELPER
    # ============================================================

    def _unknown(
        self,
        text,
        criterion_type,
        idx,
        reason
    ):

        return CriterionMatch(
            criterion_id=f"{criterion_type}_{idx}",
            criterion=text,
            patient_value=None,
            required_value=text,
            status="UNKNOWN",
            reason=reason,
            evidence_source="Matcher Agent"
        )

    # ============================================================
    # AGE PARSERS
    # ============================================================

    def _extract_min_age(self, text: str):

        m = re.search(
            r"(?:>=|≥|at least)\s*(\d+)",
            text,
            re.IGNORECASE
        )

        if m:
            return int(m.group(1))

        m = re.search(
            r"(\d+)\s*years?\s*(?:and|or)\s*older",
            text,
            re.IGNORECASE
        )

        if m:
            return int(m.group(1))

        return None

    def _extract_max_age(self, text: str):

        m = re.search(
            r"(?:<=|≤|up to)\s*(\d+)",
            text,
            re.IGNORECASE
        )

        if m:
            return int(m.group(1))

        m = re.search(
            r"(\d+)\s*years?\s*(?:and|or)\s*younger",
            text,
            re.IGNORECASE
        )

        if m:
            return int(m.group(1))

        return None

    # ============================================================
    # PERFORMANCE PARSERS
    # ============================================================

    def _parse_performance_status(self, val):

        if isinstance(val, (int, float)):
            return int(val)

        s = str(val).lower()

        m = re.search(
            r"(\d+)",
            s
        )

        if m:
            return int(m.group(1))

        return None

    def _extract_ecog_max(self, text: str):

        # Example:
        # ECOG performance status 0 to 1
        m = re.search(
            r"ecog.*?\b(?:0\s*to\s*)?(\d)\b",
            text,
            re.IGNORECASE
        )

        if m:
            return int(m.group(1))

        m = re.search(
            r"performance status.*?\b(\d)\b",
            text,
            re.IGNORECASE
        )

        if m:
            return int(m.group(1))

        m = re.search(
            r"(\d)\s*(?:or|and)\s*below",
            text,
            re.IGNORECASE
        )

        if m:
            return int(m.group(1))

        return None

    # ============================================================
    # SEX PARSER
    # ============================================================

    def _extract_required_sex(self, text: str):

        text_lower = text.lower()

        for word in [
            "male",
            "female",
            "men",
            "women"
        ]:

            if re.search(
                rf"\b{re.escape(word)}\b",
                text_lower
            ):

                if word in ("male", "men"):
                    return "Male"

                if word in ("female", "women"):
                    return "Female"

        return None