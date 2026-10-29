import pandas as pd

df = pd.read_csv('research/evaluation/trial_matching_evaluation.csv')
print('Total pairs:', len(df))
print('Annotated:', df['ground_truth_eligibility'].notna().sum())
print('\nAnnotated pairs:')
annotated = df[df['ground_truth_eligibility'].notna()]
for idx, row in annotated.iterrows():
    print(f'  Row {idx}: {row["patient_id"]} / {row["trial_id"]} -> {row["ground_truth_eligibility"]}')
