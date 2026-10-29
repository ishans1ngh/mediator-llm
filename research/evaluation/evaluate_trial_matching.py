"""
Evaluation script for clinical trial eligibility matching.

This script:
1. Loads the evaluation CSV with patient-trial pairs
2. Validates ground-truth labels
3. Runs each baseline system on the same patient-trial pairs
4. Saves predictions to the CSV
5. Calculates accuracy, precision, recall, and F1-score when ground truth exists
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from research.evaluation.baselines import get_baseline


class TrialMatchingEvaluator:
    """Evaluator for clinical trial eligibility matching."""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.results = {}
    
    def load_evaluation_data(self):
        """Load evaluation dataset from CSV."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Evaluation CSV not found: {self.csv_path}")
        
        self.df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(self.df)} patient-trial pairs from {self.csv_path}")
        
        # Check for required columns
        required_columns = ['patient_id', 'trial_id', 'trial_title', 'ground_truth_eligibility']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    def validate_ground_truth(self) -> Dict[str, int]:
        """Validate ground-truth labels and return statistics."""
        gt_column = self.df['ground_truth_eligibility']
        
        # Count valid vs invalid ground truth
        valid_gt = gt_column.notna() & (gt_column != '')
        invalid_gt = ~valid_gt
        
        # Count label distribution
        valid_labels = gt_column[valid_gt].str.upper().str.strip()
        label_counts = Counter(valid_labels)
        
        stats = {
            'total_pairs': len(self.df),
            'valid_ground_truth': valid_gt.sum(),
            'invalid_ground_truth': invalid_gt.sum(),
            'label_distribution': dict(label_counts)
        }
        
        print(f"\nGround Truth Validation:")
        print(f"  Total pairs: {stats['total_pairs']}")
        print(f"  Valid ground truth: {stats['valid_ground_truth']}")
        print(f"  Invalid/missing ground truth: {stats['invalid_ground_truth']}")
        print(f"  Label distribution: {stats['label_distribution']}")
        
        return stats
    
    def run_baseline(self, baseline_type: str, prediction_column: str) -> Dict[str, int]:
        """
        Run a baseline on all patient-trial pairs.
        
        Args:
            baseline_type: Type of baseline ("single_llm", "rag_llm", "mediator_llm")
            prediction_column: Column name to store predictions
        
        Returns:
            Statistics about predictions
        """
        print(f"\n{'='*60}")
        print(f"Running {baseline_type.upper()} baseline")
        print(f"{'='*60}")
        
        # Initialize baseline
        baseline = get_baseline(baseline_type)
        
        # Add prediction column if it doesn't exist
        if prediction_column not in self.df.columns:
            self.df[prediction_column] = ""
        
        predictions = []
        error_count = 0
        
        for idx, row in self.df.iterrows():
            patient_id = row['patient_id']
            trial_id = row['trial_id']
            
            try:
                prediction = baseline.predict_eligibility(patient_id, trial_id)
                self.df.at[idx, prediction_column] = prediction
                predictions.append(prediction)
                
                if (idx + 1) % 10 == 0:
                    print(f"  Processed {idx + 1}/{len(self.df)} pairs")
                    
            except Exception as e:
                print(f"  Error processing pair {idx}: {str(e)}")
                self.df.at[idx, prediction_column] = "ERROR"
                error_count += 1
        
        # Save updated CSV
        self.df.to_csv(self.csv_path, index=False)
        print(f"  Saved predictions to {self.csv_path}")
        
        # Statistics
        pred_counts = Counter(predictions)
        stats = {
            'total_predictions': len(predictions),
            'error_count': error_count,
            'prediction_distribution': dict(pred_counts)
        }
        
        print(f"\n  Prediction Statistics:")
        print(f"    Total predictions: {stats['total_predictions']}")
        print(f"    Errors: {stats['error_count']}")
        print(f"    Distribution: {stats['prediction_distribution']}")
        
        return stats
    
    def calculate_metrics(self, prediction_column: str) -> Dict[str, float]:
        """
        Calculate evaluation metrics for a baseline.
        
        Only calculates metrics when ground truth exists.
        
        Args:
            prediction_column: Column containing predictions
        
        Returns:
            Dictionary with accuracy, precision, recall, f1
        """
        print(f"\n{'='*60}")
        print(f"Calculating metrics for {prediction_column}")
        print(f"{'='*60}")
        
        # Filter to rows with valid ground truth
        valid_mask = (
            self.df['ground_truth_eligibility'].notna() & 
            (self.df['ground_truth_eligibility'] != '') &
            (self.df[prediction_column] != 'ERROR')
        )
        
        valid_df = self.df[valid_mask]
        
        if len(valid_df) == 0:
            print("  No valid ground truth samples available for metric calculation")
            return {
                'accuracy': None,
                'precision': None,
                'recall': None,
                'f1': None,
                'samples': 0
            }
        
        print(f"  Using {len(valid_df)} samples with valid ground truth")
        
        # Normalize labels
        ground_truth = valid_df['ground_truth_eligibility'].str.upper().str.strip()
        predictions = valid_df[prediction_column].str.upper().str.strip()
        
        # Calculate accuracy
        correct = (ground_truth == predictions).sum()
        accuracy = correct / len(valid_df)
        
        # Calculate precision, recall, F1 for binary classification
        # Treat "ELIGIBLE" as positive class
        tp = ((ground_truth == 'ELIGIBLE') & (predictions == 'ELIGIBLE')).sum()
        fp = ((ground_truth != 'ELIGIBLE') & (predictions == 'ELIGIBLE')).sum()
        fn = ((ground_truth == 'ELIGIBLE') & (predictions != 'ELIGIBLE')).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'samples': len(valid_df),
            'true_positives': int(tp),
            'false_positives': int(fp),
            'false_negatives': int(fn)
        }
        
        print(f"\n  Metrics:")
        print(f"    Accuracy: {accuracy:.4f}")
        print(f"    Precision: {precision:.4f}")
        print(f"    Recall: {recall:.4f}")
        print(f"    F1-Score: {f1:.4f}")
        print(f"    Samples: {metrics['samples']}")
        
        return metrics
    
    def run_full_evaluation(self):
        """Run complete evaluation on all baselines."""
        print(f"\n{'='*60}")
        print(f"CLINICAL TRIAL MATCHING EVALUATION")
        print(f"{'='*60}")
        
        # Load data
        self.load_evaluation_data()
        
        # Validate ground truth
        gt_stats = self.validate_ground_truth()
        
        if gt_stats['valid_ground_truth'] == 0:
            print("\nWARNING: No valid ground truth labels found.")
            print("Please manually annotate ground truth before calculating metrics.")
            print("Proceeding with prediction generation only...")
        
        # Run baselines
        baselines = [
            ('single_llm', 'single_llm_prediction'),
            ('rag_llm', 'rag_llm_prediction'),
            ('mediator_llm', 'mediator_llm_prediction')
        ]
        
        all_metrics = {}
        
        for baseline_type, prediction_column in baselines:
            try:
                # Run baseline
                pred_stats = self.run_baseline(baseline_type, prediction_column)
                
                # Calculate metrics if ground truth exists
                if gt_stats['valid_ground_truth'] > 0:
                    metrics = self.calculate_metrics(prediction_column)
                    all_metrics[baseline_type] = {
                        'prediction_stats': pred_stats,
                        'metrics': metrics
                    }
                else:
                    all_metrics[baseline_type] = {
                        'prediction_stats': pred_stats,
                        'metrics': None
                    }
                    
            except Exception as e:
                print(f"Error running {baseline_type}: {str(e)}")
                all_metrics[baseline_type] = {'error': str(e)}
        
        # Print summary
        self.print_summary(all_metrics, gt_stats)
        
        return all_metrics
    
    def print_summary(self, all_metrics: Dict, gt_stats: Dict):
        """Print evaluation summary."""
        print(f"\n{'='*60}")
        print(f"EVALUATION SUMMARY")
        print(f"{'='*60}")
        
        print(f"\nDataset:")
        print(f"  Total patient-trial pairs: {gt_stats['total_pairs']}")
        print(f"  Valid ground truth: {gt_stats['valid_ground_truth']}")
        print(f"  Invalid/missing ground truth: {gt_stats['invalid_ground_truth']}")
        
        if gt_stats['valid_ground_truth'] > 0:
            print(f"\nBaseline Performance:")
            for baseline_type, results in all_metrics.items():
                if 'error' in results:
                    print(f"  {baseline_type}: ERROR - {results['error']}")
                    continue
                
                if results['metrics']:
                    metrics = results['metrics']
                    print(f"  {baseline_type}:")
                    print(f"    Accuracy: {metrics['accuracy']:.4f}")
                    print(f"    Precision: {metrics['precision']:.4f}")
                    print(f"    Recall: {metrics['recall']:.4f}")
                    print(f"    F1-Score: {metrics['f1']:.4f}")
                else:
                    print(f"  {baseline_type}: Predictions generated, no metrics (no ground truth)")
        else:
            print(f"\nBaseline Predictions Generated:")
            for baseline_type, results in all_metrics.items():
                if 'error' in results:
                    print(f"  {baseline_type}: ERROR - {results['error']}")
                else:
                    pred_stats = results['prediction_stats']
                    print(f"  {baseline_type}: {pred_stats['total_predictions']} predictions")
        
        print(f"\n{'='*60}")
        print(f"Results saved to: {self.csv_path}")
        print(f"{'='*60}")


def main():
    """Main evaluation function."""
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    
    evaluator = TrialMatchingEvaluator(csv_path)
    results = evaluator.run_full_evaluation()
    
    return results


if __name__ == "__main__":
    main()
