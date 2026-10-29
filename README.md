# Mediator-LLM

## Agentic Clinical Trial Matching System

A research prototype demonstrating a multi-agent framework for matching patients to clinical trials using structured criterion evaluation, evidence extraction, verification, and deterministic eligibility logic.

---

## Architecture

```
React + Vite + Tailwind
         |
         | REST API
         v
    FastAPI Backend
         |
    +----+----+
    |         |
    v         v
Patient    MRI Pipeline
Dataset    MONAI/PyTorch
Excel       |
            +----+----+
            |         |
         SegResNet  ResNet
         (BraTS)   (optional)
            |
            v
      Patient Profile
            |
            v
      Trial Pipeline
            |
    ClinicalTrials.gov
            |
            v
      Trial Retrieval
            |
            v
           RAG
            |
            v
      Matcher Agent
            |
            v
    Verification Agent
            |
            v
    Explainer Agent
            |
            v
    YES / NO / UNKNOWN
```

---

## Tech Stack

- **Frontend**: React 18, Vite 5.4.21, Tailwind CSS, Lucide React
- **Backend**: Python 3.10, FastAPI 0.109.0, Pydantic 2.5.3, Uvicorn 0.27.0
- **Data**: Pandas 2.1.4, OpenPyXL 3.1.2, SQLite
- **ML**: PyTorch 2.8.0, MONAI 1.6.0, Nibabel 5.2.0
- **RAG**: Sentence Transformers 2.2.2, FAISS-CPU 1.7.4
- **APIs**: ClinicalTrials.gov v2

---

## Folder Structure

```
backend/
  main.py
  config.py
  database.py
  api/
    patients.py
    mri.py
    trials.py
    patient_profile.py
  agents/
    reader_agent.py
    matcher_agent.py
    verification_agent.py
    explainer_agent.py
  mri/
    preprocessing.py
    unet.py (SegResNet)
    resnet.py
  trials/
    clinicaltrials_api.py
    retriever.py
    eligibility.py
  rag/
    embeddings.py
    vector_store.py
  models/
    patient.py
    trial.py
    eligibility.py
  services/
    patient_service.py
  data/
    patient_dataset.xlsx
  storage/
    uploads/
    processed/
    results/
    vector_store/
    cache/
    mediator.db
  tests/
    test_eligibility.py

frontend/
  src/
    App.jsx
    main.jsx
    index.css
    api/
      mediatorApi.js
    components/
      Header.jsx
      PatientSelector.jsx
      MRIUploader.jsx
      PatientInformation.jsx
      TrialList.jsx
      TrialCard.jsx
      TrialDetails.jsx
      EligibilityCriteria.jsx
      LoadingState.jsx
  package.json
  vite.config.js
  index.html
  tailwind.config.js
  postcss.config.js

models/
  brats_mri_segmentation/
    configs/
      inference.json
    models/
      model.pt (SegResNet weights)

.env
.env.example
.gitignore
requirements.txt
```

---

## Dataset

The system expects patient data at:

```
backend/data/patient_dataset.xlsx
```

**Sheet**: "Cinical info" (note the typo - preserved from original dataset)

The current dataset contains **243 patient records** with columns including:

- `ID`, `BraTS ID`
- `Patient's Age`, `Sex at birth`, `Race`, `Ethnicity`
- `Primary Diagnosis`, `WHO 2021 Diagnosis`, `Non WHO 2021 Diagnosis`, `Grade`
- `MGMT`, `IDH`, `1p19q`, `ATRX`
- `Surgery`, `Surgery extend`, `Number of surgeries`
- `Radiation`, `Number of radiation courses`
- `1st Chemo type`, `Avastin (bevacizumab)`, `Other treatment prior to scan`
- `Overall survival`, `Progression Free survival`
- `Manufacturer`, `Manufacturer's Model Name`, `Magnetic Field Strength`

---

## Installation

### Backend

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Download MONAI BraTS Bundle

```bash
cd D:\mediator-llm
python -m monai.bundle download brats_mri_segmentation --bundle_dir ./models
```

---

## Environment Variables

Create `.env` file with:

```env
# Demo Mode
DEMO_MODE=true

# MONAI Bundle Configuration
MONAI_BUNDLE_DIR=./models/brats_mri_segmentation
MRI_DEVICE=cpu

# ResNet Configuration
RESNET50_MODEL_PATH=./backend/models/resnet/model.pt

# RAG Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_STORE_PATH=./backend/storage/vector_store
CACHE_PATH=./backend/storage/cache

# Trial Matching Configuration
MAX_TRIALS_PER_QUERY=20
```

---

## How to Run

### Start Backend

```bash
cd D:\mediator-llm
.\venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8000
- Health Check: http://127.0.0.1:8000/api/health
- Model Status: http://127.0.0.1:8000/api/models/status

---

## Demo Mode

Set `DEMO_MODE=true` in `.env`. When enabled:

- MRI analysis returns simulated results clearly labeled "DEMO MODE — MRI results are simulated"
- ClinicalTrials.gov API failures are handled gracefully
- The complete workflow remains functional without real model files
- Frontend shows "DEMO MODE" indicator in header

To use real MONAI inference:
1. Download the MONAI BraTS bundle (see Installation)
2. Set `DEMO_MODE=false` in `.env`
3. Restart backend server

---

## MRI Processing

### MONAI BraTS Bundle

The system uses the official MONAI **brats_mri_segmentation** bundle:

- **Architecture**: SegResNet (3D)
- **Input**: 4 modalities (T1, T1c, T2, FLAIR)
- **Output**: 3 tumor regions (necrotic core, edema, enhancing tumor)
- **Pretrained**: BraTS 2018 dataset

### Required Modalities

For real MRI analysis, the system requires:
- T1
- T1c (contrast-enhanced)
- T2
- FLAIR

Missing modalities will result in an error message. In demo mode, single files will use simulated results.

### Medical Disclaimer

MRI segmentation is for research purposes only. Not for clinical diagnosis or treatment decisions.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/patients` | List all patients |
| GET | `/api/patients/{id}` | Get patient by ID |
| POST | `/api/mri/upload` | Upload MRI file |
| POST | `/api/mri/analyze` | Analyze MRI with segmentation |
| POST | `/api/patient/profile` | Build unified patient profile |
| POST | `/api/trials/search` | Search ClinicalTrials.gov |
| POST | `/api/trials/match` | Match patient to trial |
| GET | `/api/trials/{trial_id}` | Get trial details |
| GET | `/api/models/status` | Check model availability |

---

## Agents

The system uses deterministic rule-based agents for trial matching:

- **Reader Agent**: Reads and structures patient data from clinical datasets and MRI results
- **Matcher Agent**: Compares patient profile against trial eligibility criteria using deterministic rules
- **Verification Agent**: Verifies eligibility decisions against trial requirements
- **Explainer Agent**: Produces human-readable explanations of eligibility results

All agents use rule-based logic and do not rely on external LLM services.

---

## Testing

```bash
cd backend
python -m pytest tests/
# or
python tests/test_eligibility.py
```

---

## Current Status

✅ **Fully Functional**
- Backend and frontend running
- MONAI BraTS bundle downloaded and integrated
- 243 patient records loaded
- ClinicalTrials.gov API integration working
- Demo mode functional
- Deterministic rule-based matching

---

## Limitations

- This is a **research prototype**, not a clinical decision support system.
- MRI analysis requires 4 modalities (T1, T1c, T2, FLAIR) for real inference.
- ClinicalTrials.gov API requires internet access.
- ResNet feature extraction is optional and not currently implemented.
- Eligibility matching uses rule-based heuristics and may not cover all criterion types.
- GPU support is available but currently configured for CPU.

---

## Research Disclaimer

**Mediator-LLM is a research prototype.** It is not intended for clinical diagnosis, treatment decisions, or patient care. Always consult qualified healthcare professionals for medical decisions.

---

## License

Research use.
