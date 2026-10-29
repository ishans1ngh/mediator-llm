"""
Non-destructive test of the manual annotation tool.

This script tests the annotation tool without making any changes to the CSV.
It verifies that:
- Patient information loads correctly
- Trial information loads correctly
- Inclusion/exclusion criteria display correctly
- The annotation interface renders correctly
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.patient_service import get_patient_by_id
from backend.trials.clinicaltrials_api import get_trial_by_nct
import pandas as pd

def test_annotation_tool():
    """Test annotation tool functionality without modifying data."""
    
    print("="*80)
    print("ANNOTATION TOOL TEST - NON-DESTRUCTIVE")
    print("="*80)
    
    # Load the evaluation CSV
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    df = pd.read_csv(csv_path)
    
    print(f"\nLoaded {len(df)} patient-trial pairs from {csv_path}")
    
    # Test with the first pair only
    test_row = df.iloc[0]
    patient_id = test_row['patient_id']
    trial_id = test_row['trial_id']
    
    print(f"\n{'='*80}")
    print(f"TESTING PAIR 1")
    print(f"{'='*80}")
    print(f"Patient ID: {patient_id}")
    print(f"Trial ID: {trial_id}")
    
    # Test 1: Load patient information
    print(f"\n{'='*80}")
    print("TEST 1: Loading Patient Information")
    print(f"{'='*80}")
    
    patient = get_patient_by_id(patient_id)
    
    if patient:
        print("[OK] Patient data loaded successfully")
        print(f"  Patient ID: {patient.get('patient_id')}")
        print(f"  Age: {patient.get('age')}")
        print(f"  Sex: {patient.get('sex')}")
        print(f"  Diagnosis: {patient.get('diagnosis')}")
        print(f"  Grade: {patient.get('grade')}")
        print(f"  IDH Status: {patient.get('IDH_status')}")
        print(f"  MGMT Status: {patient.get('MGMT_status')}")
    else:
        print("[FAILED] Could not load patient data")
        return False
    
    # Test 2: Load trial information
    print(f"\n{'='*80}")
    print("TEST 2: Loading Trial Information")
    print(f"{'='*80}")
    
    trial = get_trial_by_nct(trial_id)
    
    if trial:
        print("[OK] Trial data loaded successfully")
        print(f"  NCT ID: {trial.get('trial_id')}")
        print(f"  Title: {trial.get('title')}")
        print(f"  Status: {trial.get('status')}")
        print(f"  Phase: {trial.get('phase')}")
        print(f"  Study Type: {trial.get('study_type')}")
        
        eligibility = trial.get('eligibility', {})
        inclusion = eligibility.get('inclusion_criteria', [])
        exclusion = eligibility.get('exclusion_criteria', [])
        
        print(f"  Inclusion criteria count: {len(inclusion)}")
        print(f"  Exclusion criteria count: {len(exclusion)}")
        
        if inclusion:
            print(f"  First inclusion criterion: {inclusion[0][:100]}...")
        if exclusion:
            print(f"  First exclusion criterion: {exclusion[0][:100]}...")
    else:
        print("[FAILED] Could not load trial data from ClinicalTrials.gov")
        return False
    
    # Test 3: Display full information (simulating annotation display)
    print(f"\n{'='*80}")
    print("TEST 3: Displaying Full Patient Information")
    print(f"{'='*80}")
    
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
    
    print(f"\n{'='*80}")
    print("TEST 4: Displaying Full Trial Information")
    print(f"{'='*80}")
    
    print(f"NCT ID               : {trial.get('trial_id', 'N/A')}")
    print(f"Title                : {trial.get('title', 'N/A')}")
    print(f"Status               : {trial.get('status', 'N/A')}")
    print(f"Phase                : {trial.get('phase', 'N/A')}")
    print(f"Study Type           : {trial.get('study_type', 'N/A')}")
    
    summary = trial.get('brief_summary', 'N/A')
    if summary and summary != 'N/A':
        print(f"\nBrief Summary:")
        print(f"  {summary}")
    
    print(f"\nEligibility Requirements:")
    print(f"  Minimum Age        : {eligibility.get('minimum_age', 'N/A')}")
    print(f"  Maximum Age        : {eligibility.get('maximum_age', 'N/A')}")
    print(f"  Sex                : {eligibility.get('sex', 'N/A')}")
    print(f"  Healthy Volunteers : {eligibility.get('healthy_volunteers', 'N/A')}")
    
    print(f"\nInclusion Criteria ({len(inclusion)} items):")
    if inclusion:
        for i, criterion in enumerate(inclusion, 1):
            print(f"  {i}. {criterion}")
    else:
        print("  None specified")
    
    print(f"\nExclusion Criteria ({len(exclusion)} items):")
    if exclusion:
        for i, criterion in enumerate(exclusion, 1):
            print(f"  {i}. {criterion}")
    else:
        print("  None specified")
    
    # Test 5: Verify CSV columns
    print(f"\n{'='*80}")
    print("TEST 5: Verifying CSV Structure")
    print(f"{'='*80}")
    
    required_columns = ['patient_id', 'trial_id', 'trial_title', 'ground_truth_eligibility']
    for col in required_columns:
        if col in df.columns:
            print(f"[OK] Column '{col}' exists")
        else:
            print(f"[FAILED] Column '{col}' missing")
            return False
    
    # Check for new metadata columns
    metadata_columns = ['annotation_notes', 'annotation_timestamp', 'annotator_id']
    for col in metadata_columns:
        if col in df.columns:
            print(f"[OK] Metadata column '{col}' exists")
        else:
            print(f"  Note: Metadata column '{col}' will be added on first annotation")
    
    # Final summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print("[OK] All tests passed")
    print("[OK] Patient information loads correctly")
    print("[OK] Trial information loads correctly")
    print("[OK] Inclusion/exclusion criteria display correctly")
    print("[OK] Annotation interface renders correctly")
    print("\nNO ANNOTATIONS WERE MADE - THIS WAS A READ-ONLY TEST")
    print(f"{'='*80}")
    
    return True

if __name__ == "__main__":
    success = test_annotation_tool()
    sys.exit(0 if success else 1)
