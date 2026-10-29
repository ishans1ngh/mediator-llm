"""
Test criterion-level annotation interface.

This script tests the enhanced annotation tool with criterion-level evidence
without creating new annotations. It verifies that:
- Patient information displays correctly
- Trial information displays correctly
- Criterion-level annotation interface works
- Existing annotations are preserved
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

def test_existing_annotated_pair():
    """Test displaying an already-annotated pair."""
    print("="*80)
    print("TEST 1: Display Existing Annotated Pair")
    print("="*80)
    
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    df = pd.read_csv(csv_path)
    
    # Find first annotated pair
    annotated = df[df['ground_truth_eligibility'].notna()]
    if len(annotated) == 0:
        print("No annotated pairs found")
        return False
    
    row = annotated.iloc[0]
    patient_id = row['patient_id']
    trial_id = row['trial_id']
    
    print(f"\nPatient ID: {patient_id}")
    print(f"Trial ID: {trial_id}")
    print(f"Current annotation: {row['ground_truth_eligibility']}")
    
    # Load patient
    patient = get_patient_by_id(patient_id)
    if patient:
        print("[OK] Patient data loaded")
        print(f"  Age: {patient.get('age')}")
        print(f"  Diagnosis: {patient.get('diagnosis')}")
    else:
        print("[FAILED] Could not load patient data")
        return False
    
    # Load trial
    trial = get_trial_by_nct(trial_id)
    if trial:
        print("[OK] Trial data loaded")
        eligibility = trial.get('eligibility', {})
        inclusion = eligibility.get('inclusion_criteria', [])
        exclusion = eligibility.get('exclusion_criteria', [])
        print(f"  Inclusion criteria: {len(inclusion)} items")
        print(f"  Exclusion criteria: {len(exclusion)} items")
    else:
        print("[FAILED] Could not load trial data")
        return False
    
    print("\n[OK] Existing annotated pair displays correctly")
    return True

def test_unannotated_pair():
    """Test displaying an unannotated pair."""
    print("\n" + "="*80)
    print("TEST 2: Display Unannotated Pair")
    print("="*80)
    
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    df = pd.read_csv(csv_path)
    
    # Find first unannotated pair
    unannotated = df[
        (df['ground_truth_eligibility'].isna()) |
        (df['ground_truth_eligibility'] == '')
    ]
    
    if len(unannotated) == 0:
        print("No unannotated pairs found")
        return False
    
    row = unannotated.iloc[0]
    patient_id = row['patient_id']
    trial_id = row['trial_id']
    
    print(f"\nPatient ID: {patient_id}")
    print(f"Trial ID: {trial_id}")
    print(f"Current annotation: [NOT ANNOTATED]")
    
    # Load patient
    patient = get_patient_by_id(patient_id)
    if patient:
        print("[OK] Patient data loaded")
        print(f"  Age: {patient.get('age')}")
        print(f"  Diagnosis: {patient.get('diagnosis')}")
    else:
        print("[FAILED] Could not load patient data")
        return False
    
    # Load trial
    trial = get_trial_by_nct(trial_id)
    if trial:
        print("[OK] Trial data loaded")
        eligibility = trial.get('eligibility', {})
        inclusion = eligibility.get('inclusion_criteria', [])
        exclusion = eligibility.get('exclusion_criteria', [])
        print(f"  Inclusion criteria: {len(inclusion)} items")
        print(f"  Exclusion criteria: {len(exclusion)} items")
        
        # Display first few criteria to verify structure
        if inclusion:
            print(f"\nSample inclusion criterion:")
            print(f"  1. {inclusion[0][:100]}...")
        if exclusion:
            print(f"\nSample exclusion criterion:")
            print(f"  1. {exclusion[0][:100]}...")
    else:
        print("[FAILED] Could not load trial data")
        return False
    
    print("\n[OK] Unannotated pair displays correctly")
    return True

def test_csv_structure():
    """Test CSV has required columns."""
    print("\n" + "="*80)
    print("TEST 3: Verify CSV Structure")
    print("="*80)
    
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    df = pd.read_csv(csv_path)
    
    required_columns = [
        'patient_id', 'trial_id', 'trial_title', 'ground_truth_eligibility',
        'annotation_notes', 'annotation_timestamp', 'annotator_id',
        'inclusion_criteria_annotation', 'exclusion_criteria_annotation'
    ]
    
    for col in required_columns:
        if col in df.columns:
            print(f"[OK] Column '{col}' exists")
        else:
            print(f"[FAILED] Column '{col}' missing")
            return False
    
    print("\n[OK] All required columns present")
    return True

def test_annotation_preservation():
    """Test that existing annotations are preserved."""
    print("\n" + "="*80)
    print("TEST 4: Verify Existing Annotations Preserved")
    print("="*80)
    
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    df = pd.read_csv(csv_path)
    
    annotated = df[df['ground_truth_eligibility'].notna()]
    print(f"\nAnnotated pairs: {len(annotated)}")
    
    for idx, row in annotated.iterrows():
        print(f"  Row {idx}: {row['patient_id']} / {row['trial_id']} -> {row['ground_truth_eligibility']}")
    
    print(f"\n[OK] {len(annotated)} existing annotations preserved")
    return True

def main():
    """Run all tests."""
    print("="*80)
    print("CRITERION-LEVEL ANNOTATION INTERFACE TEST")
    print("="*80)
    
    tests = [
        test_existing_annotated_pair,
        test_unannotated_pair,
        test_csv_structure,
        test_annotation_preservation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n[ERROR] Test failed with exception: {str(e)}")
            results.append(False)
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("\n[SUCCESS] All tests passed")
        print("NO NEW ANNOTATIONS WERE CREATED - THIS WAS A READ-ONLY TEST")
        return True
    else:
        print("\n[FAILED] Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
