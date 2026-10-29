"""
Groq LLM baseline for clinical trial eligibility evaluation.

This module implements an external LLM baseline using Groq's API to evaluate
patient-trial eligibility with structured JSON output including criterion-level decisions.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from groq import Groq
from groq.types.chat import ChatCompletion

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import GROQ_API_KEY, GROQ_MODEL
from backend.services.patient_service import get_patient_by_id
from backend.trials.clinicaltrials_api import get_trial_by_nct


class GroqBaseline:
    """
    External LLM baseline using Groq API for eligibility evaluation.
    
    This baseline sends structured prompts to Groq and expects JSON responses
    with both overall eligibility and criterion-level decisions.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Groq baseline.
        
        Args:
            api_key: Groq API key (falls back to config if not provided)
            model: Groq model name (falls back to config if not provided)
        """
        self.api_key = api_key or GROQ_API_KEY
        self.model = model or GROQ_MODEL
        
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured. Please set it in your .env file or pass it explicitly.\n"
                "Example: GROQ_API_KEY=your_key_here"
            )
        
        self.client = Groq(api_key=self.api_key)
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.timeout = 60  # seconds
    
    def evaluate_pair(
        self, 
        patient_id: str, 
        trial_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single patient-trial pair.
        
        Args:
            patient_id: Patient identifier
            trial_id: Clinical trial NCT ID
        
        Returns:
            Dictionary with overall_eligibility, criteria list, and reasoning_summary
        """
        # Get patient and trial data
        patient = get_patient_by_id(patient_id)
        if not patient:
            return self._error_result("Patient not found")
        
        trial = get_trial_by_nct(trial_id)
        if not trial:
            return self._error_result("Trial not found")
        
        # Construct prompt
        prompt = self._construct_prompt(patient, trial)
        
        # Call Groq API with retries
        response = self._call_groq_with_retry(prompt)
        
        if response is None:
            return self._error_result("API call failed after retries")
        
        # Parse response
        parsed = self._parse_response(response)
        
        if parsed is None:
            return self._error_result("Failed to parse JSON response")
        
        return parsed
    
    def _construct_prompt(self, patient: Dict[str, Any], trial: Dict[str, Any]) -> str:
        """Construct structured prompt for Groq."""
        
        eligibility = trial.get("eligibility", {})
        inclusion_criteria = eligibility.get("inclusion_criteria", [])
        exclusion_criteria = eligibility.get("exclusion_criteria", [])
        
        prompt = f"""You are evaluating whether a patient satisfies the eligibility criteria of a clinical trial.

Evaluate each inclusion and exclusion criterion independently.

For each criterion return:
- criterion: the exact criterion text
- type: INCLUSION or EXCLUSION
- decision: MET / NOT_MET / UNKNOWN
- evidence: short evidence based only on the provided patient information

Then provide an overall result:
ELIGIBLE / NOT_ELIGIBLE / UNCERTAIN

Do not assume missing information.
If the patient information is insufficient to determine a criterion, return UNKNOWN.

PATIENT INFORMATION:
- Age: {patient.get('age', 'Unknown')}
- Sex: {patient.get('sex', 'Unknown')}
- Diagnosis: {patient.get('diagnosis', 'Unknown')}
- WHO Diagnosis: {patient.get('who_diagnosis', 'Unknown')}
- Non-WHO Diagnosis: {patient.get('non_who_diagnosis', 'Unknown')}
- Grade: {patient.get('grade', 'Unknown')}
- IDH Status: {patient.get('IDH_status', 'Unknown')}
- MGMT Status: {patient.get('MGMT_status', 'Unknown')}
- ATRX Status: {patient.get('ATRX_status', 'Unknown')}
- 1p19q Status: {patient.get('1p19q_status', 'Unknown')}
- Performance Status: {patient.get('performance_status', 'Unknown')}
- Surgery: {patient.get('surgery', 'Unknown')}
- Surgery Extent: {patient.get('surgery_extend', 'Unknown')}
- Radiation: {patient.get('radiation', 'Unknown')}
- Chemotherapy: {patient.get('chemotherapy', 'Unknown')}
- Immunotherapy: {patient.get('immunotherapy', 'Unknown')}
- Other Treatment: {patient.get('other_treatment', 'Unknown')}

CLINICAL TRIAL:
- Title: {trial.get('title', 'Unknown')}
- Brief Summary: {trial.get('brief_summary', 'Unknown')}

INCLUSION CRITERIA:
{self._format_criteria(inclusion_criteria)}

EXCLUSION CRITERIA:
{self._format_criteria(exclusion_criteria)}

Respond with valid JSON in the following format:
{{
  "overall_eligibility": "ELIGIBLE | NOT_ELIGIBLE | UNCERTAIN",
  "criteria": [
    {{
      "criterion": "...",
      "type": "INCLUSION | EXCLUSION",
      "decision": "MET | NOT_MET | UNKNOWN",
      "evidence": "..."
    }}
  ],
  "reasoning_summary": "..."
}}"""
        
        return prompt
    
    def _format_criteria(self, criteria: List[str]) -> str:
        """Format criteria list for prompt."""
        if not criteria:
            return "None"
        return "\n".join(f"- {c}" for c in criteria)
    
    def _call_groq_with_retry(self, prompt: str) -> Optional[str]:
        """Call Groq API with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a clinical trial eligibility expert. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,  # Low temperature for consistency
                    timeout=self.timeout
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                print(f"  Groq API call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    print(f"  Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"  All {self.max_retries} attempts failed")
                    return None
        
        return None
    
    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from Groq."""
        try:
            parsed = json.loads(response)
            
            # Validate required fields
            required_fields = ["overall_eligibility", "criteria"]
            for field in required_fields:
                if field not in parsed:
                    print(f"  Missing required field in response: {field}")
                    return None
            
            # Validate overall_eligibility value
            valid_overall = ["ELIGIBLE", "NOT_ELIGIBLE", "UNCERTAIN"]
            if parsed["overall_eligibility"] not in valid_overall:
                print(f"  Invalid overall_eligibility: {parsed['overall_eligibility']}")
                return None
            
            # Validate criteria structure
            for criterion in parsed["criteria"]:
                required_criterion_fields = ["criterion", "type", "decision", "evidence"]
                for field in required_criterion_fields:
                    if field not in criterion:
                        print(f"  Missing required field in criterion: {field}")
                        return None
                
                valid_types = ["INCLUSION", "EXCLUSION"]
                if criterion["type"] not in valid_types:
                    print(f"  Invalid criterion type: {criterion['type']}")
                    return None
                
                valid_decisions = ["MET", "NOT_MET", "UNKNOWN"]
                if criterion["decision"] not in valid_decisions:
                    print(f"  Invalid criterion decision: {criterion['decision']}")
                    return None
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"  Failed to parse JSON response: {str(e)}")
            return None
        except Exception as e:
            print(f"  Error parsing response: {str(e)}")
            return None
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return error result structure."""
        return {
            "overall_eligibility": "ERROR",
            "criteria": [],
            "reasoning_summary": f"Error: {error_message}",
            "error": error_message
        }


def run_groq_baseline(
    patient_id: str, 
    trial_id: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to run Groq baseline on a single pair.
    
    Args:
        patient_id: Patient identifier
        trial_id: Clinical trial NCT ID
        api_key: Optional Groq API key
        model: Optional Groq model name
    
    Returns:
        Dictionary with evaluation results
    """
    baseline = GroqBaseline(api_key=api_key, model=model)
    return baseline.evaluate_pair(patient_id, trial_id)
