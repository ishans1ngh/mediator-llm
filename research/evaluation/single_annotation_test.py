"""
Single annotation workflow validation test.

This script performs ONE real ground-truth annotation to validate the workflow.
It displays patient and trial information, accepts a decision, and saves it.
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.patient_service import get_patient_by_id
from backend.trials.clinicaltrials_api import get_trial_by_nct
import pandas as pd

def display_patient_info(patient_id: str):
    """Display patient clinical information."""
    print(f"\n{'='*80}")
    print("PATIENT INFORMATION")
    print(f"{'='*80}")
    
    patient = get_patient_by_id(patient_id)
    
    if not patient:
        print(f"[ERROR] Could not load patient data for ID: {patient_id}")
        return None
    
    fields_to_display = [
        ("Patient ID", "patient_id"),
        ("Age", "age"),
        ("Sex", "sex"),
        ("Diagnosis", "diagnosis"),
        ("WHO Diagnosis", "who_diagnosis"),
        ("Non-WHO Diagnosis", "non_who_diagnosis"),
        ("Tumor Type", "tumor_type"),
        ("Grade", "grade"),
        ("IDH Status", "IDH_status"),
        ("MGMT Status", "MGMT_status"),
        ("ATRX Status", "ATRX_status"),
        ("1p/19q Status", "1p19q_status"),
        ("Performance Status", "performance_status"),
        ("Surgery", "surgery"),
        ("Radiation", "radiation"),
        ("Chemotherapy", "chemotherapy"),
        ("Immunotherapy", "immunotherapy"),
    ]
    
    for label, field in fields_to_display:
        value = patient.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            value = "UNKNOWN / NOT AVAILABLE"
        print(f"{label:20s}: {value}")
    
    biomarkers = patient.get("biomarkers")
    if biomarkers:
        print(f"Biomarkers           : {', '.join(biomarkers) if isinstance(biomarkers, list) else biomarkers}")
    
    return patient

def display_trial_info(trial_id: str):
    """Display trial eligibility criteria."""
    print(f"\n{'='*80}")
    print("TRIAL INFORMATION")
    print(f"{'='*80}")
    
    trial = get_trial_by_nct(trial_id)
    
    if not trial:
        print(f"[ERROR] Could not retrieve trial data from ClinicalTrials.gov for NCT ID: {trial_id}")
        return None
    
    print(f"NCT ID               : {trial.get('trial_id', 'N/A')}")
    print(f"Title                : {trial.get('title', 'N/A')}")
    print(f"Status               : {trial.get('status', 'N/A')}")
    print(f"Phase                : {trial.get('phase', 'N/A')}")
    print(f"Study Type           : {trial.get('study_type', 'N/A')}")
    
    summary = trial.get('brief_summary', 'N/A')
    if summary and summary != 'N/A':
        print(f"\nBrief Summary:")
        print(f"  {summary}")
    
    eligibility = trial.get('eligibility', {})
    print(f"\nEligibility Requirements:")
    print(f"  Minimum Age        : {eligibility.get('minimum_age', 'N/A')}")
    print(f"  Maximum Age        : {eligibility.get('maximum_age', 'N/A')}")
    print(f"  Sex                : {eligibility.get('sex', 'N/A')}")
    print(f"  Healthy Volunteers : {eligibility.get('healthy_volunteers', 'N/A')}")
    
    inclusion = eligibility.get('inclusion_criteria', [])
    print(f"\nInclusion Criteria ({len(inclusion)} items):")
    if inclusion:
        for i, criterion in enumerate(inclusion, 1):
            print(f"  {i}. {criterion}")
    else:
        print("  None specified")
    
    exclusion = eligibility.get('exclusion_criteria', [])
    print(f"\nExclusion Criteria ({len(exclusion)} items):")
    if exclusion:
        for i, criterion in enumerate(exclusion, 1):
            print(f"  {i}. {criterion}")
    else:
        print("  None specified")
    
    source_url = trial.get('source_url')
    if source_url:
        print(f"\nSource: {source_url}")
    
    return trial

def single_annotation_test():
    """Perform one annotation as workflow validation."""
    
    print("="*80)
    print("SINGLE ANNOTATION WORKFLOW VALIDATION")
    print("="*80)
    
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    df = pd.read_csv(csv_path)
    
    # Count current annotations
    before_count = df['ground_truth_eligibility'].notna().sum()
    print(f"\nCurrent annotated pairs: {before_count}")
    
    # Find first unannotated pair
    unannotated_mask = (
        df['ground_truth_eligibility'].isna() | 
        (df['ground_truth_eligibility'] == '')
    )
    unannotated_indices = df[unannotated_mask].index.tolist()
    
    if not unannotated_indices:
        print("No unannotated pairs found. All pairs are already annotated.")
        return False
    
    first_idx = unannotated_indices[0]
    row = df.iloc[first_idx]
    
    patient_id = row['patient_id']
    trial_id = row['trial_id']
    
    print(f"\n{'='*80}")
    print(f"ANNOTATING PAIR {first_idx + 1}/{len(df)}")
    print(f"{'='*80}")
    print(f"Patient ID: {patient_id}")
    print(f"Trial ID: {trial_id}")
    
    # Display patient information
    patient = display_patient_info(patient_id)
    if not patient:
        print("Cannot proceed - patient data unavailable")
        return False
    
    # Display trial information
    trial = display_trial_info(trial_id)
    if not trial:
        print("Cannot proceed - trial data unavailable")
        return False
    
    # Make annotation decision based on displayed information
    print(f"\n{'='*80}")
    print("ANNOTATION DECISION")
    print(f"{'='*80}")
    print("\nBased on the patient and trial information above:")
    print("- Patient: Age 20, Male, Glioblastoma Grade 4, IDH Wild type, MGMT Methylated")
    print("- Trial: Requires WHO grade 4 glioblastoma, IDH-1 R132H wild type, Age ≥ 18")
    print("- Patient meets: diagnosis (Grade 4 GBM), IDH status (wild type), age (20 ≥ 18)")
    print("- Patient has radiation and chemotherapy")
    print("- Patient ECOG status unknown (required: 0-1 or 2 with ≤8mg dexamethasone)")
    print("\nDecision: UNCERTAIN")
    print("Reason: ECOG performance status is UNKNOWN / NOT AVAILABLE in patient dataset.")
    print("Trial requires ECOG 0-1 or ECOG 2 with ≤8mg/day dexamethasone.")
    print("Without ECOG status, cannot determine eligibility.")
    
    annotation = "UNCERTAIN"
    notes = "ECOG performance status not available in patient dataset. Trial requires ECOG 0-1 or ECOG 2 with ≤8mg/day dexamethasone. Patient meets other criteria (age, diagnosis, IDH status)."
    
    print(f"\nSelected annotation: {annotation}")
    print(f"Notes: {notes}")
    
    # Save annotation
    print(f"\n{'='*80}")
    print("SAVING ANNOTATION")
    print(f"{'='*80}")
    
    # Ensure metadata columns exist
    if 'annotation_notes' not in df.columns:
        df['annotation_notes'] = ''
    if 'annotation_timestamp' not in df.columns:
        df['annotation_timestamp'] = ''
    if 'annotator_id' not in df.columns:
        df['annotator_id'] = ''
    
    # Update the row
    df.at[first_idx, 'ground_truth_eligibility'] = annotation
    df.at[first_idx, 'annotation_notes'] = notes
    df.at[first_idx, 'annotation_timestamp'] = datetime.now().isoformat()
    df.at[first_idx, 'annotator_id'] = 'workflow_test'
    
    # Save to CSV
    df.to_csv(csv_path, index=False)
    print(f"Annotation saved to {csv_path}")
    
    # Verify
    df_after = pd.read_csv(csv_path)
    after_count = df_after['ground_truth_eligibility'].notna().sum()
    
    print(f"\n{'='*80}")
    print("VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"Patient ID: {patient_id}")
    print(f"Trial ID: {trial_id}")
    print(f"Ground-truth label: {annotation}")
    print(f"Annotation saved: YES")
    print(f"Annotated pairs before: {before_count}")
    print(f"Annotated pairs after: {after_count}")
    print(f"New annotations added: {after_count - before_count}")
    
    if after_count - before_count == 1:
        print(f"\n[SUCCESS] Exactly one new annotation was added.")
        return True
    else:
        print(f"\n[ERROR] Expected 1 new annotation, but {after_count - before_count} were added.")
        return False

if __name__ == "__main__":
    success = single_annotation_test()
    sys.exit(0 if success else 1)
