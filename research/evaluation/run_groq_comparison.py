"""
Main script to run Groq baseline vs Mediator-LLM comparison experiment.

This script orchestrates the complete experiment:
1. Loads the evaluation dataset
2. Runs Groq baseline on all patient-trial pairs
3. Runs Mediator-LLM on all patient-trial pairs
4. Compares results at overall and criterion levels
5. Saves results to JSON/CSV
6. Generates Figure 4 visualizations
7. Prints summary statistics
"""

import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from research.evaluation.groq_baseline import GroqBaseline
from research.evaluation.mediator_adapter import MediatorAdapter
from research.evaluation.compare_groq_mediator import GroqMediatorComparator
from backend.config import GROQ_API_KEY, GROQ_MODEL


class GroqComparisonExperiment:
    """
    Main experiment orchestrator for Groq vs Mediator-LLM comparison.
    """
    
    def __init__(self, csv_path: str, results_dir: str = None):
        """
        Initialize the experiment.
        
        Args:
            csv_path: Path to evaluation CSV
            results_dir: Directory to save results (default: research/evaluation/results/)
        """
        self.csv_path = Path(csv_path)
        self.results_dir = Path(results_dir) if results_dir else Path(__file__).parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.df = None
        self.groq_baseline = None
        self.mediator_adapter = None
        self.comparator = GroqMediatorComparator()
        
        # Result storage
        self.groq_results = {}
        self.mediator_results = {}
        self.overall_comparisons = []
        self.criterion_comparisons = []
    
    def load_dataset(self):
        """Load the evaluation dataset from CSV."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Evaluation CSV not found: {self.csv_path}")
        
        self.df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(self.df)} patient-trial pairs from {self.csv_path}")
        
        # Validate required columns
        required_columns = ['patient_id', 'trial_id']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    def initialize_baselines(self):
        """Initialize Groq baseline and Mediator adapter."""
        print("\nInitializing baselines...")
        
        # Initialize Groq baseline
        try:
            self.groq_baseline = GroqBaseline()
            print(f"  Groq baseline initialized with model: {GROQ_MODEL}")
        except ValueError as e:
            print(f"  ERROR: {e}")
            print("  Please set GROQ_API_KEY in your .env file")
            raise
        
        # Initialize Mediator adapter
        self.mediator_adapter = MediatorAdapter()
        print("  Mediator-LLM adapter initialized")
    
    def run_groq_baseline(self) -> Dict[str, Any]:
        """Run Groq baseline on all patient-trial pairs."""
        print("\n" + "="*60)
        print("RUNNING GROQ BASELINE")
        print("="*60)
        
        groq_results = {}
        error_count = 0
        
        for idx, row in self.df.iterrows():
            patient_id = row['patient_id']
            trial_id = row['trial_id']
            pair_key = f"{patient_id}_{trial_id}"
            
            print(f"  [{idx+1}/{len(self.df)}] Evaluating {patient_id} / {trial_id}")
            
            try:
                result = self.groq_baseline.evaluate_pair(patient_id, trial_id)
                groq_results[pair_key] = result
                
                if result.get("overall_eligibility") == "ERROR":
                    error_count += 1
                    print(f"    ERROR: {result.get('error', 'Unknown error')}")
                else:
                    print(f"    Result: {result.get('overall_eligibility')}")
                    
            except Exception as e:
                print(f"    EXCEPTION: {str(e)}")
                groq_results[pair_key] = {
                    "overall_eligibility": "ERROR",
                    "criteria": [],
                    "reasoning_summary": f"Exception: {str(e)}",
                    "error": str(e)
                }
                error_count += 1
        
        print(f"\nGroq baseline complete: {len(groq_results)} pairs evaluated, {error_count} errors")
        self.groq_results = groq_results
        return groq_results
    
    def run_mediator_adapter(self) -> Dict[str, Any]:
        """Run Mediator-LLM adapter on all patient-trial pairs."""
        print("\n" + "="*60)
        print("RUNNING MEDIATOR-LLM")
        print("="*60)
        
        mediator_results = {}
        error_count = 0
        
        for idx, row in self.df.iterrows():
            patient_id = row['patient_id']
            trial_id = row['trial_id']
            pair_key = f"{patient_id}_{trial_id}"
            
            print(f"  [{idx+1}/{len(self.df)}] Evaluating {patient_id} / {trial_id}")
            
            try:
                result = self.mediator_adapter.evaluate_pair(patient_id, trial_id)
                mediator_results[pair_key] = result
                
                if result.get("overall_eligibility") == "ERROR":
                    error_count += 1
                    print(f"    ERROR: {result.get('error', 'Unknown error')}")
                else:
                    print(f"    Result: {result.get('overall_eligibility')}")
                    
            except Exception as e:
                print(f"    EXCEPTION: {str(e)}")
                mediator_results[pair_key] = {
                    "overall_eligibility": "ERROR",
                    "criteria": [],
                    "reasoning_summary": f"Exception: {str(e)}",
                    "error": str(e)
                }
                error_count += 1
        
        print(f"\nMediator-LLM complete: {len(mediator_results)} pairs evaluated, {error_count} errors")
        self.mediator_results = mediator_results
        return mediator_results
    
    def compare_results(self):
        """Compare Groq and Mediator-LLM results."""
        print("\n" + "="*60)
        print("COMPARING RESULTS")
        print("="*60)
        
        overall_comparisons = []
        criterion_comparisons = []
        
        for idx, row in self.df.iterrows():
            patient_id = row['patient_id']
            trial_id = row['trial_id']
            pair_key = f"{patient_id}_{trial_id}"
            
            groq_result = self.groq_results.get(pair_key, {})
            mediator_result = self.mediator_results.get(pair_key, {})
            
            # Compare overall decisions
            overall_comp = self.comparator.compare_overall(groq_result, mediator_result)
            overall_comparisons.append(overall_comp)
            
            # Compare criterion-level decisions
            criterion_comp = self.comparator.compare_criteria(groq_result, mediator_result)
            criterion_comparisons.append(criterion_comp)
        
        self.overall_comparisons = overall_comparisons
        self.criterion_comparisons = criterion_comparisons
        
        print(f"Comparison complete: {len(overall_comparisons)} pairs compared")
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comparison statistics."""
        patient_trial_pairs = [
            (row['patient_id'], row['trial_id']) 
            for _, row in self.df.iterrows()
        ]
        
        stats = self.comparator.calculate_statistics(
            self.overall_comparisons,
            self.criterion_comparisons
        )
        
        return stats
    
    def save_results(self, stats: Dict[str, Any]):
        """Save all results to files."""
        print("\n" + "="*60)
        print("SAVING RESULTS")
        print("="*60)
        
        # Save raw Groq results
        groq_results_path = self.results_dir / "groq_results.json"
        with open(groq_results_path, 'w') as f:
            json.dump(self.groq_results, f, indent=2)
        print(f"  Saved Groq results to: {groq_results_path}")
        
        # Save raw Mediator results
        mediator_results_path = self.results_dir / "mediator_results.json"
        with open(mediator_results_path, 'w') as f:
            json.dump(self.mediator_results, f, indent=2)
        print(f"  Saved Mediator results to: {mediator_results_path}")
        
        # Save detailed comparison CSV
        patient_trial_pairs = [
            (row['patient_id'], row['trial_id']) 
            for _, row in self.df.iterrows()
        ]
        comparison_df = self.comparator.create_comparison_csv(
            patient_trial_pairs,
            self.overall_comparisons,
            self.criterion_comparisons
        )
        comparison_csv_path = self.results_dir / "groq_vs_mediator_comparison.csv"
        comparison_df.to_csv(comparison_csv_path, index=False)
        print(f"  Saved comparison CSV to: {comparison_csv_path}")
        
        # Save summary statistics
        summary_path = self.results_dir / "groq_vs_mediator_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  Saved summary statistics to: {summary_path}")
    
    def generate_figure_4(self, stats: Dict[str, Any]):
        """Generate Figure 4: Criterion-level agreement visualization."""
        print("\n" + "="*60)
        print("GENERATING FIGURE 4")
        print("="*60)
        
        import matplotlib.pyplot as plt
        
        # Data for criterion-level agreement
        categories = ['Agreement', 'Disagreement', 'Both Unknown']
        values = [
            stats['criterion_agreements'],
            stats['criterion_disagreements'],
            stats['both_unknown']
        ]
        total = sum(values)
        percentages = [v/total*100 if total > 0 else 0 for v in values]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.bar(categories, values, color=['#2ecc71', '#e74c3c', '#95a5a6'])
        
        # Add percentage labels on bars
        for bar, pct in zip(bars, percentages):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{pct:.1f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # Add count labels
        for bar, count in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height/2,
                   f'n={count}',
                   ha='center', va='center', fontsize=11, color='white', fontweight='bold')
        
        ax.set_xlabel('Criterion-Level Comparison', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('Criterion-Level Agreement: Groq Baseline vs Mediator-LLM', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Add grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Set y-axis to start from 0
        ax.set_ylim(0, max(values) * 1.2 if values else 1)
        
        plt.tight_layout()
        
        # Save figure
        figure_4_path = self.results_dir / "figure_4_groq_vs_mediator.png"
        plt.savefig(figure_4_path, dpi=300, bbox_inches='tight')
        print(f"  Saved Figure 4 to: {figure_4_path}")
        
        plt.close()
        
        # Print Figure 4 statistics
        print(f"\nFigure 4 statistics:")
        print(f"  Total criterion comparisons: {stats['criterion_comparisons']}")
        print(f"  Agreement: {stats['criterion_agreements']} ({stats['criterion_agreement_rate']:.1f}%)")
        print(f"  Disagreement: {stats['criterion_disagreements']}")
        print(f"  Both Unknown: {stats['both_unknown']}")
        print(f"  Agreement rate: {stats['criterion_agreement_rate']:.1f}%")
    
    def generate_figure_4b(self, stats: Dict[str, Any]):
        """Generate Figure 4b: Overall eligibility agreement visualization."""
        print("\n" + "="*60)
        print("GENERATING FIGURE 4B (Overall Agreement)")
        print("="*60)
        
        import matplotlib.pyplot as plt
        
        # Data for overall agreement
        categories = ['Agreement', 'Disagreement']
        values = [stats['same_overall'], stats['different_overall']]
        total = sum(values)
        percentages = [v/total*100 if total > 0 else 0 for v in values]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        bars = ax.bar(categories, values, color=['#2ecc71', '#e74c3c'])
        
        # Add percentage labels on bars
        for bar, pct in zip(bars, percentages):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{pct:.1f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # Add count labels
        for bar, count in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height/2,
                   f'n={count}',
                   ha='center', va='center', fontsize=11, color='white', fontweight='bold')
        
        ax.set_xlabel('Overall Eligibility Decision', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('Overall Eligibility Agreement: Groq Baseline vs Mediator-LLM', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Add grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Set y-axis to start from 0
        ax.set_ylim(0, max(values) * 1.2 if values else 1)
        
        plt.tight_layout()
        
        # Save figure
        figure_4b_path = self.results_dir / "figure_4b_overall_agreement.png"
        plt.savefig(figure_4b_path, dpi=300, bbox_inches='tight')
        print(f"  Saved Figure 4b to: {figure_4b_path}")
        
        plt.close()
        
        # Print Figure 4b statistics
        print(f"\nFigure 4b statistics:")
        print(f"  Valid comparisons: {stats['valid_pairs']}")
        print(f"  Agreement: {stats['same_overall']} ({stats['overall_agreement_rate']:.1f}%)")
        print(f"  Disagreement: {stats['different_overall']}")
        print(f"  Overall agreement rate: {stats['overall_agreement_rate']:.1f}%")
    
    def generate_report(self, stats: Dict[str, Any]):
        """Generate comprehensive comparison report."""
        print("\n" + "="*60)
        print("GENERATING REPORT")
        print("="*60)
        
        report_path = self.results_dir / "GROQ_COMPARISON_REPORT.txt"
        
        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("GROQ BASELINE VS MEDIATOR-LLM COMPARISON REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write("EXPERIMENT CONFIGURATION\n")
            f.write("-" * 70 + "\n")
            f.write(f"Dataset: {self.csv_path}\n")
            f.write(f"Groq Model: {GROQ_MODEL}\n")
            f.write(f"Results Directory: {self.results_dir}\n\n")
            
            f.write("DATASET STATISTICS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total patient-trial pairs: {stats['n_pairs']}\n")
            f.write(f"Valid comparisons: {stats['valid_pairs']}\n\n")
            
            f.write("OVERALL ELIGIBILITY AGREEMENT\n")
            f.write("-" * 70 + "\n")
            f.write(f"Same overall decision: {stats['same_overall']}\n")
            f.write(f"Different overall decision: {stats['different_overall']}\n")
            f.write(f"Overall agreement rate: {stats['overall_agreement_rate']:.2f}%\n")
            f.write(f"Groq errors: {stats['groq_errors']}\n")
            f.write(f"Mediator errors: {stats['mediator_errors']}\n\n")
            
            f.write("CRITERION-LEVEL AGREEMENT\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total criterion comparisons: {stats['criterion_comparisons']}\n")
            f.write(f"Criterion agreements: {stats['criterion_agreements']}\n")
            f.write(f"Criterion disagreements: {stats['criterion_disagreements']}\n")
            f.write(f"Both UNKNOWN: {stats['both_unknown']}\n")
            f.write(f"Criterion agreement rate: {stats['criterion_agreement_rate']:.2f}%\n\n")
            
            f.write("GENERATED FILES\n")
            f.write("-" * 70 + "\n")
            f.write(f"1. Groq results: {self.results_dir / 'groq_results.json'}\n")
            f.write(f"2. Mediator results: {self.results_dir / 'mediator_results.json'}\n")
            f.write(f"3. Comparison CSV: {self.results_dir / 'groq_vs_mediator_comparison.csv'}\n")
            f.write(f"4. Summary statistics: {self.results_dir / 'groq_vs_mediator_summary.json'}\n")
            f.write(f"5. Figure 4: {self.results_dir / 'figure_4_groq_vs_mediator.png'}\n")
            f.write(f"6. Figure 4b: {self.results_dir / 'figure_4b_overall_agreement.png'}\n")
            f.write(f"7. This report: {report_path}\n\n")
            
            f.write("="*70 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*70 + "\n")
        
        print(f"  Saved report to: {report_path}")
    
    def print_summary(self, stats: Dict[str, Any]):
        """Print concise summary to console."""
        print("\n" + "="*60)
        print("GROQ vs MEDIATOR-LLM")
        print("="*60)
        print(f"Patient-trial pairs: {stats['n_pairs']}")
        print(f"Valid comparisons: {stats['valid_pairs']}")
        print(f"Overall agreement: {stats['overall_agreement_rate']:.1f}%")
        print(f"Criterion comparisons: {stats['criterion_comparisons']}")
        print(f"Criterion agreement: {stats['criterion_agreement_rate']:.1f}%")
        print(f"Criterion disagreement: {stats['criterion_disagreements']}")
        print(f"Both UNKNOWN: {stats['both_unknown']}")
        print("="*60)
    
    def run_experiment(self):
        """Run the complete experiment."""
        print("="*60)
        print("GROQ BASELINE VS MEDIATOR-LLM COMPARISON EXPERIMENT")
        print("="*60)
        
        # Load dataset
        self.load_dataset()
        
        # Initialize baselines
        self.initialize_baselines()
        
        # Run Groq baseline
        self.run_groq_baseline()
        
        # Run Mediator-LLM
        self.run_mediator_adapter()
        
        # Compare results
        self.compare_results()
        
        # Calculate statistics
        stats = self.calculate_statistics()
        
        # Save results
        self.save_results(stats)
        
        # Generate figures
        self.generate_figure_4(stats)
        self.generate_figure_4b(stats)
        
        # Generate report
        self.generate_report(stats)
        
        # Print summary
        self.print_summary(stats)
        
        return stats


def main():
    """Main entry point."""
    csv_path = "research/evaluation/trial_matching_evaluation.csv"
    
    experiment = GroqComparisonExperiment(csv_path)
    stats = experiment.run_experiment()
    
    return stats


if __name__ == "__main__":
    main()
