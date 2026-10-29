"""
Script to create initial evaluation dataset for clinical trial matching evaluation.

This script:
1. Loads existing patients from the clinical dataset
2. Retrieves relevant clinical trials for each patient
3. Creates patient-trial pairs for evaluation
4. Populates the evaluation CSV with these pairs

Ground truth eligibility labels are left empty for manual annotation.
"""

import pandas as pd
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.patient_service import get_all_patients
from backend.trials.clinicaltrials_api import search_trials
from backend.config import MAX_TRIALS_PER_QUERY

def create_evaluation_dataset():
    """Create initial evaluation dataset with patient-trial pairs."""
    
    # Load existing patients
    print("Loading patients from clinical dataset...")
    patients = get_all_patients()
    print(f"Found {len(patients)} patients")
    
    # Limit to a reasonable number for initial evaluation
    # (can be adjusted later)
    sample_patients = patients[:10]  # Start with 10 patients
    print(f"Using {len(sample_patients)} patients for initial evaluation")
    
    # Create evaluation pairs
    evaluation_pairs = []
    
    for patient in sample_patients:
        patient_id = patient.get("patient_id")
        print(f"\nProcessing patient: {patient_id}")
        
        # Get search terms for this patient
        query_terms = []
        diagnosis = patient.get("diagnosis") or patient.get("disease")
        if diagnosis:
            query_terms.append(diagnosis)
        if patient.get("tumor_type"):
            query_terms.append(patient["tumor_type"])
        
        if not query_terms:
            print(f"  Skipping - no diagnosis/tumor type found")
            continue
        
        print(f"  Search terms: {query_terms}")
        
        # Retrieve trials for this patient
        try:
            trials = search_trials(query_terms, max_results=5)  # Get 5 trials per patient
            print(f"  Found {len(trials)} trials")
            
            for trial in trials:
                evaluation_pairs.append({
                    "patient_id": patient_id,
                    "trial_id": trial.get("trial_id", ""),
                    "trial_title": trial.get("title", ""),
                    "ground_truth_eligibility": "",  # Empty for manual annotation
                    "single_llm_prediction": "",    # To be filled by evaluation
                    "rag_llm_prediction": "",        # To be filled by evaluation
                    "mediator_llm_prediction": ""    # To be filled by evaluation
                })
        except Exception as e:
            print(f"  Error retrieving trials: {str(e)}")
            continue
    
    # Save to CSV
    output_path = Path("research/evaluation/trial_matching_evaluation.csv")
    
    if evaluation_pairs:
        df = pd.DataFrame(evaluation_pairs)
        df.to_csv(output_path, index=False)
        print(f"\nCreated evaluation dataset with {len(evaluation_pairs)} patient-trial pairs")
        print(f"Saved to: {output_path}")
    else:
        print("\nNo evaluation pairs created")
    
    return len(evaluation_pairs)

if __name__ == "__main__":
    num_pairs = create_evaluation_dataset()
    print(f"\n{'='*60}")
    print(f"EVALUATION DATASET CREATED")
    print(f"{'='*60}")
    print(f"Patient-trial pairs: {num_pairs}")
    print(f"Ground truth status: NOT ANNOTATED (requires manual review)")
    print(f"Next steps:")
    print(f"1. Manually review and annotate ground truth eligibility")
    print(f"2. Run evaluation script to generate predictions")
    print(f"3. Calculate accuracy metrics")
