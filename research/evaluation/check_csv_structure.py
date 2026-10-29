import pandas as pd

df = pd.read_csv('research/evaluation/trial_matching_evaluation.csv')
print('Columns:', list(df.columns))
print('\nSample row (row 0):')
row = df.iloc[0]
for col in df.columns:
    val = row[col]
    if pd.isna(val) or val == '':
        val = '[empty]'
    print(f'  {col}: {val}')
