import re
import requests
import json
from typing import Dict, Any, List, Optional
from backend.config import CLINICALTRIALS_API_BASE, MAX_TRIALS_PER_QUERY

def search_trials(query_terms: List[str], max_results: int = MAX_TRIALS_PER_QUERY) -> List[Dict[str, Any]]:
    """Search ClinicalTrials.gov API v2 for trials."""
    base_url = CLINICALTRIALS_API_BASE.rstrip("/")
    url = f"{base_url}/studies"
    
    # Build filter query from terms
    query_string = " OR ".join(query_terms)
    params = {
        "query.cond": query_string,
        "pageSize": min(max_results, 100),
        "fields": "NCTId,BriefTitle,OverallStatus,Condition,Intervention,EligibilityCriteria,Location,Phase,StudyType,BriefSummary",
        "format": "json",
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        studies = data.get("studies", [])
        return [_normalize_study(s) for s in studies]
    except requests.RequestException as e:
        # Return empty on failure; caller should handle
        return []

def get_trial_by_nct(nct_id: str) -> Optional[Dict[str, Any]]:
    base_url = CLINICALTRIALS_API_BASE.rstrip("/")
    url = f"{base_url}/studies/{nct_id}"
    params = {"fields": "NCTId,BriefTitle,OverallStatus,Condition,Intervention,EligibilityCriteria,Location,Phase,StudyType,BriefSummary"}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return _normalize_study(data)
    except Exception:
        return None

def _normalize_study(study: Dict[str, Any]) -> Dict[str, Any]:
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    cond = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    elig = protocol.get("eligibilityModule", {})
    loc = protocol.get("contactsLocationsModule", {})
    desc = protocol.get("descriptionModule", {})
    
    nct = ident.get("nctId", "")
    
    # Parse eligibility criteria into inclusion/exclusion lists
    raw_elig = elig.get("eligibilityCriteria", "")
    inclusion, exclusion = _parse_eligibility_criteria(raw_elig)
    
    return {
        "trial_id": nct,
        "nct_id": nct,
        "title": ident.get("briefTitle", "Untitled"),
        "brief_summary": desc.get("briefSummary", ""),
        "status": status.get("overallStatus", "Unknown"),
        "conditions": cond.get("conditions", []),
        "interventions": _extract_interventions(protocol),
        "eligibility": {
            "minimum_age": elig.get("minimumAge", "N/A"),
            "maximum_age": elig.get("maximumAge", "N/A"),
            "sex": elig.get("sex", "ALL"),
            "healthy_volunteers": elig.get("healthyVolunteers", False),
            "inclusion_criteria": inclusion,
            "exclusion_criteria": exclusion,
        },
        "locations": _extract_locations(loc),
        "source_url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
        "phase": design.get("phases", [None])[0] if design.get("phases") else None,
        "study_type": design.get("studyType", None),
        "sponsor": sponsor.get("leadSponsor", {}).get("name", None),
        "original_data": study,
    }

def _parse_eligibility_criteria(raw: str) -> (List[str], List[str]):
    """Split ClinicalTrials.gov eligibility text into inclusion/exclusion criteria."""
    inclusion = []
    exclusion = []

    if not raw:
        return inclusion, exclusion

    current = None

    for line in raw.splitlines():
        line = line.strip()

        if not line:
            continue

        lower = line.lower().strip(" :.-")

        # Detect section headings
        if lower.startswith("inclusion criteria"):
            current = "inclusion"
            continue

        if lower.startswith("exclusion criteria"):
            current = "exclusion"
            continue

        # Ignore anything before a recognized section
        if current is None:
            continue

        # Remove common bullet/number prefixes
        text = re.sub(r"^(?:[-*•]|\d+[.)])\s*", "", line).strip()

        if not text:
            continue

        if current == "inclusion":
            inclusion.append(text)
        else:
            exclusion.append(text)

    return inclusion, exclusion

def _extract_interventions(protocol: Dict[str, Any]) -> List[str]:
    arms = protocol.get("armsInterventionsModule", {})
    intervs = arms.get("interventions", [])
    return [i.get("name", "") for i in intervs if i.get("name")]

def _extract_locations(loc: Dict[str, Any]) -> List[Dict[str, Any]]:
    locs = loc.get("locations", [])
    out = []
    for l in locs:
        out.append({
            "facility": l.get("facility", ""),
            "city": l.get("city", ""),
            "state": l.get("state", ""),
            "country": l.get("country", ""),
            "zip_code": l.get("zip", ""),
        })
    return out
