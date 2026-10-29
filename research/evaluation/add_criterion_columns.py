"""
Add criterion-level annotation columns to CSV.
This script initializes the new columns without modifying existing data.
"""

import pandas as pd
from pathlib import Path

csv_path = "research/evaluation/trial_matching_evaluation.csv"
df = pd.read_csv(csv_path)

# Add new columns if missing
if 'inclusion_criteria_annotation' not in df.columns:
    df['inclusion_criteria_annotation'] = ''
    print("Added column: inclusion_criteria_annotation")
else:
    print("Column already exists: inclusion_criteria_annotation")

if 'exclusion_criteria_annotation' not in df.columns:
    df['exclusion_criteria_annotation'] = ''
    print("Added column: exclusion_criteria_annotation")
else:
    print("Column already exists: exclusion_criteria_annotation")

# Save
df.to_csv(csv_path, index=False)
print(f"\nCSV updated: {csv_path}")
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
