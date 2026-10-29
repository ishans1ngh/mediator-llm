"""
Manual annotation tool for clinical trial eligibility ground truth.

This tool allows researchers to manually review patient-trial pairs
and annotate ground truth eligibility labels with criterion-level evidence.
"""

import pandas as pd
import sys
import io
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.patient_service import get_patient_by_id
from backend.trials.clinicaltrials_api import get_trial_by_nct


class ManualAnnotationTool:
    """Tool for manual ground truth annotation."""
    
    def __init__(self, csv_path: str, annotator_id: Optional[str] = None):
        self.csv_path = Path(csv_path)
        self.df = None
        self.annotator_id = annotator_id or "unknown"
        
        # Add new columns if they don't exist
        self._ensure_columns_exist()
    
    def _ensure_columns_exist(self):
        """Ensure CSV has required columns for enhanced annotation."""
        if not self.csv_path.exists():
            return
        
        df = pd.read_csv(self.csv_path)
        
        # Add annotation metadata columns if missing
        if 'annotation_notes' not in df.columns:
            df['annotation_notes'] = ''
        if 'annotation_timestamp' not in df.columns:
            df['annotation_timestamp'] = ''
        if 'annotator_id' not in df.columns:
            df['annotator_id'] = ''
        
        # Add criterion-level annotation columns if missing
        if 'inclusion_criteria_annotation' not in df.columns:
            df['inclusion_criteria_annotation'] = ''
        if 'exclusion_criteria_annotation' not in df.columns:
            df['exclusion_criteria_annotation'] = ''
        
        # Save if columns were added
        df.to_csv(self.csv_path, index=False)
    
    def load_data(self):
        """Load evaluation dataset."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Evaluation CSV not found: {self.csv_path}")
        
        self.df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(self.df)} patient-trial pairs")
    
    def _display_patient_info(self, patient_id: str):
        """Display patient clinical information."""
        print(f"\n{'='*80}")
        print("PATIENT INFORMATION")
        print(f"{'='*80}")
        
        patient = get_patient_by_id(patient_id)
        
        if not patient:
            print(f"[ERROR] Could not load patient data for ID: {patient_id}")
            print("Patient information not available in dataset.")
            return
        
        # Display key clinical fields
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
        
        # Display biomarkers if available
        biomarkers = patient.get("biomarkers")
        if biomarkers:
            print(f"Biomarkers           : {', '.join(biomarkers) if isinstance(biomarkers, list) else biomarkers}")
    
    def _display_trial_info(self, trial_id: str):
        """Display trial eligibility criteria."""
        print(f"\n{'='*80}")
        print("TRIAL INFORMATION")
        print(f"{'='*80}")
        
        trial = get_trial_by_nct(trial_id)
        
        if not trial:
            print(f"[ERROR] Could not retrieve trial data from ClinicalTrials.gov for NCT ID: {trial_id}")
            print("Trial information not available. Cannot annotate this pair.")
            return False
        
        # Display trial metadata
        print(f"NCT ID               : {trial.get('trial_id', 'N/A')}")
        print(f"Title                : {trial.get('title', 'N/A')}")
        print(f"Status               : {trial.get('status', 'N/A')}")
        print(f"Phase                : {trial.get('phase', 'N/A')}")
        print(f"Study Type           : {trial.get('study_type', 'N/A')}")
        
        # Display brief summary
        summary = trial.get('brief_summary', 'N/A')
        if summary and summary != 'N/A':
            print(f"\nBrief Summary:")
            print(f"  {summary}")
        
        # Display eligibility requirements
        eligibility = trial.get('eligibility', {})
        print(f"\nEligibility Requirements:")
        print(f"  Minimum Age        : {eligibility.get('minimum_age', 'N/A')}")
        print(f"  Maximum Age        : {eligibility.get('maximum_age', 'N/A')}")
        print(f"  Sex                : {eligibility.get('sex', 'N/A')}")
        print(f"  Healthy Volunteers : {eligibility.get('healthy_volunteers', 'N/A')}")
        
        # Display inclusion criteria
        inclusion = eligibility.get('inclusion_criteria', [])
        print(f"\nInclusion Criteria ({len(inclusion)} items):")
        if inclusion:
            for i, criterion in enumerate(inclusion, 1):
                print(f"  {i}. {criterion}")
        else:
            print("  None specified")
        
        # Display exclusion criteria
        exclusion = eligibility.get('exclusion_criteria', [])
        print(f"\nExclusion Criteria ({len(exclusion)} items):")
        if exclusion:
            for i, criterion in enumerate(exclusion, 1):
                print(f"  {i}. {criterion}")
        else:
            print("  None specified")
        
        # Display source URL
        source_url = trial.get('source_url')
        if source_url:
            print(f"\nSource: {source_url}")
        
        return True
    
    def _annotate_criteria(self, criteria: List[str], criterion_type: str) -> List[Dict[str, str]]:
        """
        Annotate a list of criteria (inclusion or exclusion).
        
        Args:
            criteria: List of criterion text
            criterion_type: "inclusion" or "exclusion"
        
        Returns:
            List of annotation dictionaries with status and notes
        """
        annotations = []
        
        for i, criterion in enumerate(criteria, 1):
            print(f"\n{'-'*80}")
            print(f"{criterion_type.upper()} CRITERION {i}/{len(criteria)}")
            print(f"{'-'*80}")
            print(f"Criterion: {criterion}")
            
            # Determine valid options based on criterion type
            if criterion_type == "inclusion":
                print("\nOptions:")
                print("  YES      - Patient meets this inclusion criterion")
                print("  NO       - Patient does NOT meet this inclusion criterion")
                print("  UNKNOWN  - Insufficient information to determine")
            else:  # exclusion
                print("\nOptions:")
                print("  YES      - Exclusion criterion APPLIES to patient (excludes patient)")
                print("  NO       - Exclusion criterion does NOT apply to patient")
                print("  UNKNOWN  - Insufficient information to determine")
            
            while True:
                status = input(f"\nEnter status (YES/NO/UNKNOWN): ").strip().upper()
                if status in ['YES', 'NO', 'UNKNOWN']:
                    break
                else:
                    print("Invalid input. Please enter: YES, NO, or UNKNOWN")
            
            # Get optional note for this criterion
            note = input(f"Optional note for this criterion (press Enter to skip): ").strip()
            
            annotations.append({
                'criterion_index': i,
                'criterion_text': criterion,
                'status': status,
                'note': note
            })
            
            print(f"\nSaved: {status}")
            if note:
                print(f"Note: {note}")
        
        return annotations
    
    def annotate_pair(self, idx: int) -> tuple:
        """
        Annotate a single patient-trial pair with criterion-level evidence.
        
        Returns: Tuple of (annotation, notes, inclusion_annotations, exclusion_annotations)
        """
        row = self.df.iloc[idx]
        
        print(f"\n{'='*80}")
        print(f"PAIR {idx + 1}/{len(self.df)}")
        print(f"{'='*80}")
        
        patient_id = row['patient_id']
        trial_id = row['trial_id']
        
        # Display patient information
        self._display_patient_info(patient_id)
        
        # Display trial information
        trial_available = self._display_trial_info(trial_id)
        
        if not trial_available:
            print(f"\n{'='*80}")
            print("Cannot annotate this pair - trial information unavailable.")
            print("Recommendation: SKIP this pair.")
            print(f"{'='*80}")
            
            while True:
                decision = input("\nEnter SKIP to continue or QUIT to exit: ").strip().upper()
                if decision == 'SKIP':
                    return ('', '', '', '')
                elif decision == 'QUIT':
                    return ('QUIT', '', '', '')
                else:
                    print("Invalid input. Please enter SKIP or QUIT.")
        
        # Display current annotation status
        current_gt = row['ground_truth_eligibility']
        current_notes = row.get('annotation_notes', '')
        if current_gt and current_gt != '':
            print(f"\n{'='*80}")
            print(f"Current Annotation: {current_gt}")
            if current_notes:
                print(f"Current Notes: {current_notes}")
            print(f"{'='*80}")
        else:
            print(f"\n{'='*80}")
            print("Current Annotation: [NOT ANNOTATED]")
            print(f"{'='*80}")
        
        # Ask if annotator wants to do criterion-level annotation
        print(f"\n{'-'*80}")
        print("CRITERION-LEVEL ANNOTATION")
        print(f"{'-'*80}")
        print("Do you want to annotate each criterion individually?")
        print("This provides more detailed evidence for the overall decision.")
        
        while True:
            do_criterion_level = input("\nAnnotate criteria individually? (YES/NO): ").strip().upper()
            if do_criterion_level in ['YES', 'NO']:
                break
            else:
                print("Invalid input. Please enter: YES or NO")
        
        inclusion_annotations = []
        exclusion_annotations = []
        
        if do_criterion_level == 'YES':
            # Load trial again to get criteria
            trial = get_trial_by_nct(trial_id)
            if trial:
                eligibility = trial.get('eligibility', {})
                inclusion = eligibility.get('inclusion_criteria', [])
                exclusion = eligibility.get('exclusion_criteria', [])
                
                # Annotate inclusion criteria
                if inclusion:
                    print(f"\n{'='*80}")
                    print("ANNOTATING INCLUSION CRITERIA")
                    print(f"{'='*80}")
                    inclusion_annotations = self._annotate_criteria(inclusion, "inclusion")
                
                # Annotate exclusion criteria
                if exclusion:
                    print(f"\n{'='*80}")
                    print("ANNOTATING EXCLUSION CRITERIA")
                    print(f"{'='*80}")
                    exclusion_annotations = self._annotate_criteria(exclusion, "exclusion")
        
        # Get overall annotation decision
        print(f"\n{'='*80}")
        print("OVERALL ELIGIBILITY DECISION")
        print(f"{'='*80}")
        print("Based on the patient and trial information above, determine eligibility:")
        print("  ELIGIBLE     - Patient meets all inclusion criteria and no exclusion criteria")
        print("  NOT_ELIGIBLE - Patient fails inclusion criteria or meets exclusion criteria")
        print("  UNCERTAIN    - Insufficient information to determine eligibility")
        print("  SKIP         - Keep current annotation (or leave blank)")
        print("  QUIT         - Save progress and exit")
        print(f"{'='*80}")
        
        while True:
            annotation = input("\nEnter annotation (ELIGIBLE/NOT_ELIGIBLE/UNCERTAIN/SKIP/QUIT): ").strip().upper()
            
            if annotation in ['ELIGIBLE', 'NOT_ELIGIBLE', 'UNCERTAIN']:
                break
            elif annotation == 'SKIP':
                return (current_gt if current_gt else '', current_notes, '', '')
            elif annotation == 'QUIT':
                return ('QUIT', '', '', '')
            else:
                print("Invalid input. Please enter: ELIGIBLE, NOT_ELIGIBLE, UNCERTAIN, SKIP, or QUIT")
        
        # Get optional notes
        print(f"\n{'-'*80}")
        print("Optional: Add notes explaining your overall decision (press Enter to skip):")
        print(f"{'-'*80}")
        notes = input("Notes: ").strip()
        
        # Convert criterion annotations to JSON for storage
        inclusion_json = json.dumps(inclusion_annotations) if inclusion_annotations else ''
        exclusion_json = json.dumps(exclusion_annotations) if exclusion_annotations else ''
        
        return (annotation, notes, inclusion_json, exclusion_json)
    
    def run_annotation(self):
        """Run interactive annotation session."""
        print(f"\n{'='*80}")
        print(f"MANUAL GROUND TRUTH ANNOTATION TOOL")
        print(f"Annotator ID: {self.annotator_id}")
        print(f"{'='*80}")
        
        self.load_data()
        
        # Find unannotated pairs
        unannotated_mask = (
            self.df['ground_truth_eligibility'].isna() | 
            (self.df['ground_truth_eligibility'] == '')
        )
        unannotated_indices = self.df[unannotated_mask].index.tolist()
        
        print(f"\nUnannotated pairs: {len(unannotated_indices)}")
        print(f"Already annotated: {len(self.df) - len(unannotated_indices)}")
        
        if len(unannotated_indices) == 0:
            print("All pairs are already annotated!")
            return
        
        print(f"\nStarting annotation session...")
        print(f"Press Ctrl+C at any time to save and exit.")
        
        for idx in unannotated_indices:
            try:
                annotation, notes, inclusion_json, exclusion_json = self.annotate_pair(idx)
                
                if annotation == 'QUIT':
                    print("\nSaving progress and exiting...")
                    break
                
                # Only update if annotation changed
                if annotation != self.df.at[idx, 'ground_truth_eligibility']:
                    self.df.at[idx, 'ground_truth_eligibility'] = annotation
                    self.df.at[idx, 'annotation_notes'] = notes
                    self.df.at[idx, 'annotation_timestamp'] = datetime.now().isoformat()
                    self.df.at[idx, 'annotator_id'] = self.annotator_id
                    self.df.at[idx, 'inclusion_criteria_annotation'] = inclusion_json
                    self.df.at[idx, 'exclusion_criteria_annotation'] = exclusion_json
                    
                    print(f"\nSaved: {annotation}")
                    if notes:
                        print(f"Notes: {notes}")
                    if inclusion_json:
                        print(f"Inclusion criteria annotated: {len(json.loads(inclusion_json))} items")
                    if exclusion_json:
                        print(f"Exclusion criteria annotated: {len(json.loads(exclusion_json))} items")
                    
                    # Save after each annotation
                    self.df.to_csv(self.csv_path, index=False)
                    print(f"Progress saved to {self.csv_path}")
                else:
                    print(f"\nAnnotation unchanged: {annotation}")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Saving progress...")
                self.df.to_csv(self.csv_path, index=False)
                print(f"Progress saved to {self.csv_path}")
                break
            except Exception as e:
                print(f"\nError processing pair {idx}: {str(e)}")
                print("Skipping this pair and continuing...")
                continue
        
        print(f"\n{'='*80}")
        print(f"ANNOTATION SESSION COMPLETED")
        print(f"{'='*80}")
        
        # Print final statistics
        final_unannotated = (
            self.df['ground_truth_eligibility'].isna() | 
            (self.df['ground_truth_eligibility'] == '')
        ).sum()
        
        print(f"Total pairs: {len(self.df)}")
        print(f"Annotated: {len(self.df) - final_unannotated}")
        print(f"Remaining unannotated: {final_unannotated}")
        print(f"Results saved to: {self.csv_path}")


def main():
    """Main function."""
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    
    # Optional: Get annotator ID from command line or environment
    import os
    annotator_id = os.getenv("ANNOTATOR_ID", None)
    
    if not annotator_id:
        print("Note: No ANNOTATOR_ID environment variable set.")
        print("Annotations will be attributed to 'unknown'.")
        print("To set annotator ID: export ANNOTATOR_ID=your_name (Linux/Mac) or set ANNOTATOR_ID=your_name (Windows)")
        print()
    
    tool = ManualAnnotationTool(csv_path, annotator_id=annotator_id)
    tool.run_annotation()


if __name__ == "__main__":
    main()
