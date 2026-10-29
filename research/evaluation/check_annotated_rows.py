import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_csv('research/evaluation/trial_matching_evaluation.csv')
print('Annotated rows:')
annotated = df[df['ground_truth_eligibility'].notna()]
for idx, row in annotated.iterrows():
    print(f'\nRow {idx}:')
    print(f'  patient_id: {row["patient_id"]}')
    print(f'  trial_id: {row["trial_id"]}')
    print(f'  ground_truth_eligibility: {row["ground_truth_eligibility"]}')
    notes = row["annotation_notes"]
    if pd.isna(notes) or notes == '':
        notes = "[empty]"
    print(f'  annotation_notes: {notes}')
    ts = row["annotation_timestamp"]
    if pd.isna(ts) or ts == '':
        ts = "[empty]"
    print(f'  annotation_timestamp: {ts}')
    aid = row["annotator_id"]
    if pd.isna(aid) or aid == '':
        aid = "[empty]"
    print(f'  annotator_id: {aid}')
