# Clinical Trial Matching Evaluation

This directory contains the evaluation infrastructure for comparing clinical trial eligibility matching approaches:

1. **Single LLM Baseline** - Direct LLM prediction without specialized architecture
2. **RAG + LLM Baseline** - Retrieval-augmented generation with clinical trial context
3. **Mediator-LLM** - Full multi-agent system with Matcher, Verification, and Explainer agents

## Dataset Structure

### CSV Format

The evaluation dataset is stored in `trial_matching_evaluation.csv` with the following columns:

- `patient_id` - Unique patient identifier from the clinical dataset
- `trial_id` - ClinicalTrials.gov NCT identifier
- `trial_title` - Title of the clinical trial
- `ground_truth_eligibility` - Manual annotation (ELIGIBLE/NOT_ELIGIBLE/UNCERTAIN)
- `single_llm_prediction` - Single LLM baseline prediction
- `rag_llm_prediction` - RAG + LLM baseline prediction  
- `mediator_llm_prediction` - Mediator-LLM prediction

### Initial Dataset

The initial dataset contains **50 patient-trial pairs**:
- 10 patients from the clinical dataset (243 total patients available)
- 5 relevant clinical trials per patient
- Total: 50 unique patient-trial combinations

The dataset can be expanded by modifying `create_evaluation_dataset.py` to include more patients or trials per patient.

## Ground Truth Establishment

### Current Status

**No verified ground truth labels currently exist.** The initial dataset has empty `ground_truth_eligibility` values.

### Manual Annotation Process

Ground truth labels must be established through manual review by clinical experts:

1. Run the manual annotation tool:
   ```bash
   venv\Scripts\activate
   python research/evaluation/manual_annotation_tool.py
   ```

2. For each patient-trial pair, the tool displays:
   - Patient ID and clinical information
   - Trial ID and title
   - Current annotation status

3. Annotator chooses one of:
   - **ELIGIBLE** - Patient meets all inclusion criteria and no exclusion criteria
   - **NOT_ELIGIBLE** - Patient fails inclusion criteria or meets exclusion criteria
   - **UNCERTAIN** - Insufficient information to determine eligibility
   - **SKIP** - Leave current annotation unchanged
   - **QUIT** - Save progress and exit

4. Progress is saved automatically after each annotation

### Reference Standard

Manually verified eligibility labels serve as the reference standard for this evaluation. This approach is necessary because:

- Clinical trial eligibility determination requires clinical judgment
- Automated systems may miss nuanced criteria
- Complex cases often require expert interpretation
- No existing public dataset with verified labels for this specific task

## Running the Evaluation

### Prerequisites

1. Ensure the virtual environment is activated:
   ```bash
   venv\Scripts\activate
   ```

2. Ensure Ollama is running if using LLM baselines

### Step 1: Create/Update Dataset (Optional)

If you need to create a new evaluation dataset or expand the existing one:

```bash
python research/evaluation/create_evaluation_dataset.py
```

This will:
- Load patients from the clinical dataset
- Retrieve relevant clinical trials from ClinicalTrials.gov
- Create patient-trial pairs
- Save to `trial_matching_evaluation.csv`

### Step 2: Annotate Ground Truth (Required for Metrics)

If ground truth labels are not already annotated:

```bash
python research/evaluation/manual_annotation_tool.py
```

Follow the interactive prompts to annotate each patient-trial pair.

### Step 3: Run Evaluation

Run the complete evaluation on all baselines:

```bash
python research/evaluation/evaluate_trial_matching.py
```

This will:
1. Load the evaluation dataset
2. Validate ground truth labels
3. Run each baseline system on all patient-trial pairs
4. Save predictions to the CSV
5. Calculate metrics (if ground truth exists)
6. Print comprehensive summary

### Step 4: Review Results

Results are saved to `trial_matching_evaluation.csv` with predictions filled in for each baseline.

The evaluation script prints:
- Dataset statistics (total pairs, valid ground truth)
- Prediction statistics for each baseline
- Accuracy, precision, recall, F1-score (if ground truth exists)
- Error reports for any failed predictions

## Prediction Generation

### Single LLM Baseline

The single LLM baseline:
1. Constructs a prompt with patient information and trial criteria
2. Sends prompt to the LLM (Ollama)
3. Parses the response to extract ELIGIBLE/NOT_ELIGIBLE/UNKNOWN
4. No specialized agents or verification

**Prompt includes:**
- Patient demographics (age, sex)
- Clinical information (diagnosis, grade, biomarkers)
- Treatment history (surgery, radiation, chemotherapy)
- Trial title and summary
- Inclusion and exclusion criteria

### RAG + LLM Baseline

The RAG + LLM baseline:
1. Retrieves relevant clinical trial context using vector similarity
2. Constructs enhanced prompt with retrieved context
3. Sends prompt to the LLM
4. Parses response to extract eligibility status

**Note:** Current implementation uses the same prompt as single LLM baseline. Full RAG integration requires vector store setup and is marked for future implementation.

### Mediator-LLM Baseline

The Mediator-LLM baseline uses the full production system:
1. **Matcher Agent** - Deterministic rule-based criterion matching
2. **Verification Agent** - Cross-checks and validates matches
3. **Explainer Agent** - Generates human-readable explanations
4. **Eligibility Engine** - Combines agent outputs into final determination

**Key differences from baselines:**
- Rule-based matching for common criteria (age, diagnosis, biomarkers)
- Handles UNKNOWN states when data is insufficient
- Provides detailed explanations for each decision
- Maintains clinical safety by avoiding guesses

## Metric Calculation

### When Metrics Are Calculated

Metrics are **only calculated when ground truth labels exist**. If the dataset has no verified labels, the evaluation script will:
- Generate predictions for all baselines
- Save predictions to CSV
- Skip metric calculation with appropriate warning

### Accuracy Formula

```
Accuracy = Correct Predictions / Total Valid Ground Truth Samples
```

### Precision, Recall, F1-Score

Treat "ELIGIBLE" as the positive class:

```
True Positives (TP) = Ground Truth ELIGIBLE AND Prediction ELIGIBLE
False Positives (FP) = Ground Truth NOT_ELIGIBLE AND Prediction ELIGIBLE  
False Negatives (FN) = Ground Truth ELIGIBLE AND Prediction NOT_ELIGIBLE

Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1-Score = 2 * (Precision * Recall) / (Precision + Recall)
```

### Handling Special Cases

- **UNKNOWN predictions** - Treated as incorrect if ground truth is ELIGIBLE or NOT_ELIGIBLE
- **ERROR predictions** - Excluded from metric calculation
- **UNCERTAIN ground truth** - Excluded from metric calculation
- **Empty/missing ground truth** - Excluded from metric calculation

## Limitations

### Dataset Limitations

1. **Sample Size** - Initial dataset contains only 50 patient-trial pairs
2. **Patient Population** - Limited to glioblastoma patients from UCSD dataset
3. **Trial Diversity** - Trials retrieved based on diagnosis keywords only
4. **Ground Truth** - Requires manual annotation by clinical experts

### Baseline Limitations

1. **Single LLM** - No specialized medical knowledge or verification
2. **RAG + LLM** - Currently equivalent to single LLM (full RAG not implemented)
3. **Mediator-LLM** - May be conservative (prefers UNKNOWN over guesses)

### Evaluation Limitations

1. **Binary Classification** - Reduces complex eligibility to binary decision
2. **Criteria Granularity** - Does not evaluate per-criterion performance
3. **Temporal Changes** - Clinical trials may change criteria over time
4. **Geographic Scope** - Does not consider trial location/availability

### Safety Considerations

1. **Clinical Use** - This evaluation is for research purposes only
2. **Not for Diagnosis** - Results should not be used for clinical decisions
3. **Expert Review Required** - All predictions should be reviewed by clinicians
4. **System Limitations** - Automated systems may miss nuanced criteria

## File Structure

```
research/evaluation/
├── README.md                          # This documentation
├── trial_matching_evaluation.csv     # Evaluation dataset
├── create_evaluation_dataset.py      # Script to create patient-trial pairs
├── manual_annotation_tool.py          # Interactive ground truth annotation
├── evaluate_trial_matching.py        # Main evaluation script
└── baselines.py                      # Baseline implementations
```

## Next Steps

1. **Expand Dataset** - Increase number of patients and trials for statistical power
2. **Complete RAG Integration** - Implement full vector store and retrieval
3. **Clinical Expert Review** - Have domain experts annotate ground truth
4. **Per-Criterion Analysis** - Evaluate performance on specific criterion types
5. **Error Analysis** - Investigate common failure modes across baselines
6. **A/B Testing** - Compare against production clinical trial matching systems

## Contact

For questions about this evaluation framework, please refer to the main Mediator-LLM project documentation.