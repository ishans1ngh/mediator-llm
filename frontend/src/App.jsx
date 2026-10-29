import { useState } from 'react';
import Header from './components/Header';
import PatientSelector from './components/PatientSelector';
import MRIUploader from './components/MRIUploader';
import PatientInformation from './components/PatientInformation';
import TrialList from './components/TrialList';
import TrialDetails from './components/TrialDetails';
import LoadingState from './components/LoadingState';
import { getPatient, buildProfile, searchTrials, matchTrial } from './api/mediatorApi';

const STEPS = {
  SELECT_PATIENT: 'SELECT_PATIENT',
  UPLOAD_MRI: 'UPLOAD_MRI',
  REVIEW_PROFILE: 'REVIEW_PROFILE',
  FIND_TRIALS: 'FIND_TRIALS',
  VIEW_TRIALS: 'VIEW_TRIALS',
  TRIAL_DETAIL: 'TRIAL_DETAIL',
};

function unwrap(field) {
  if (field && typeof field === 'object' && 'value' in field) {
    return field.value;
  }
  return field;
}

export default function App() {
  const [step, setStep] = useState(STEPS.SELECT_PATIENT);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientProfile, setPatientProfile] = useState(null);
  const [mriAnalysis, setMriAnalysis] = useState(null);
  const [trials, setTrials] = useState([]);
  const [selectedTrial, setSelectedTrial] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePatientSelect = async (patient) => {
    setSelectedPatient(patient);
    setError(null);
    try {
      const full = await getPatient(patient.patient_id);
      setSelectedPatient(full);
      setStep(STEPS.UPLOAD_MRI);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleMRIComplete = (analysis) => {
    setMriAnalysis(analysis);
  };

  const handleContinueToProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = await buildProfile({
        clinical_data: selectedPatient,
        mri_data: mriAnalysis,
      });
      setPatientProfile(profile);
      setStep(STEPS.REVIEW_PROFILE);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = (updated) => {
    setPatientProfile(updated);
  };

  const handleFindTrials = async () => {
    setLoading(true);
    setError(null);
    try {
      const flatPatient = {
        patient_id: patientProfile.patient_id,
        brats_id: patientProfile.brats_id,
        age: unwrap(patientProfile.demographics?.age),
        sex: unwrap(patientProfile.demographics?.sex),
        race: unwrap(patientProfile.demographics?.race),
        ethnicity: unwrap(patientProfile.demographics?.ethnicity),
        diagnosis: unwrap(patientProfile.diagnosis?.primary_diagnosis),
        who_diagnosis: unwrap(patientProfile.diagnosis?.who_diagnosis),
        non_who_diagnosis: unwrap(patientProfile.diagnosis?.non_who_diagnosis),
        tumor_type: unwrap(patientProfile.diagnosis?.tumor_type),
        disease: unwrap(patientProfile.diagnosis?.disease),
        grade: unwrap(patientProfile.diagnosis?.grade),
        IDH_status: unwrap(patientProfile.biomarkers?.IDH_status),
        MGMT_status: unwrap(patientProfile.biomarkers?.MGMT_status),
        ATRX_status: unwrap(patientProfile.biomarkers?.ATRX_status),
        status_1p19q: unwrap(patientProfile.biomarkers?.status_1p19q),
        biomarkers: unwrap(patientProfile.biomarkers?.other),
        surgery: unwrap(patientProfile.treatment_history?.surgery),
        surgery_extend: unwrap(patientProfile.treatment_history?.surgery_extend),
        number_of_surgeries: unwrap(patientProfile.treatment_history?.number_of_surgeries),
        radiation: unwrap(patientProfile.treatment_history?.radiation),
        number_of_radiation_courses: unwrap(patientProfile.treatment_history?.number_of_radiation_courses),
        chemotherapy: unwrap(patientProfile.treatment_history?.chemotherapy),
        immunotherapy: unwrap(patientProfile.treatment_history?.immunotherapy),
        other_treatment: unwrap(patientProfile.treatment_history?.other_treatment),
        overall_survival: unwrap(patientProfile.treatment_history?.overall_survival),
        progression_free_survival: unwrap(patientProfile.treatment_history?.progression_free_survival),
        performance_status: unwrap(patientProfile.clinical_data?.performance_status),
        comorbidities: unwrap(patientProfile.clinical_data?.comorbidities),
        medications: unwrap(patientProfile.clinical_data?.medications),
        days_to_initial_surgery: unwrap(patientProfile.clinical_data?.days_to_initial_surgery),
        days_to_last_followup: unwrap(patientProfile.clinical_data?.days_to_last_followup),
        manufacturer: unwrap(patientProfile.imaging_metadata?.manufacturer),
        manufacturer_model: unwrap(patientProfile.imaging_metadata?.manufacturer_model),
        magnetic_field_strength: unwrap(patientProfile.imaging_metadata?.magnetic_field_strength),
      };

      const searchRes = await searchTrials({ patient_profile: flatPatient, max_results: 20 });
      const rawTrials = searchRes.trials || [];

      const matchedTrials = [];
      for (const trial of rawTrials) {
        try {
          const matchRes = await matchTrial({ patient_profile: flatPatient, trial });
          console.log(`Match response for ${trial.trial_id}:`, matchRes.result);
          matchedTrials.push(matchRes.result);
        } catch (e) {
          console.error(`Match request failed for trial ${trial.trial_id}:`, e);
          console.error('Trial object:', trial);
          matchedTrials.push({
            trial_id: trial.trial_id,
            title: trial.title,
            final_status: 'UNKNOWN',
            criteria_summary: { yes: 0, no: 0, unknown: 0 },
            inclusion: [],
            exclusion: [],
            unknown: [],
            verification: { verified: false, issues: [e.message] },
            source_url: trial.source_url,
            status: trial.status,
            conditions: trial.conditions,
          });
        }
      }
      setTrials(matchedTrials);
      setStep(STEPS.VIEW_TRIALS);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTrial = (trial) => {
    setSelectedTrial(trial);
    setStep(STEPS.TRIAL_DETAIL);
  };

  const handleBackToTrials = () => {
    setSelectedTrial(null);
    setStep(STEPS.VIEW_TRIALS);
  };

  const renderStep = () => {
    if (loading) {
      return <LoadingState message={
        step === STEPS.FIND_TRIALS ? 'Searching ClinicalTrials.gov...' :
        step === STEPS.REVIEW_PROFILE ? 'Building patient profile...' :
        'Loading...'
      } />;
    }

    switch (step) {
      case STEPS.SELECT_PATIENT:
        return <PatientSelector onSelect={handlePatientSelect} />;
      case STEPS.UPLOAD_MRI:
        return (
          <div>
            <MRIUploader patientId={selectedPatient?.patient_id} onAnalysisComplete={handleMRIComplete} />
            <div className='max-w-4xl mx-auto px-6 pb-6'>
              <button onClick={handleContinueToProfile} className='w-full py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium'>
                Continue to Patient Profile
              </button>
            </div>
          </div>
        );
      case STEPS.REVIEW_PROFILE:
        return <PatientInformation profile={patientProfile} onUpdate={handleProfileUpdate} onContinue={handleFindTrials} />;
      case STEPS.VIEW_TRIALS:
        return <TrialList trials={trials} onSelectTrial={handleSelectTrial} />;
      case STEPS.TRIAL_DETAIL:
        return <TrialDetails trial={selectedTrial} onBack={handleBackToTrials} />;
      default:
        return <PatientSelector onSelect={handlePatientSelect} />;
    }
  };

  return (
    <div className='min-h-screen bg-slate-50'>
      <Header />
      <main className='pb-12'>
        {error && (
          <div className='max-w-4xl mx-auto p-6'>
            <div className='bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3'>
              Error: {error}
            </div>
          </div>
        )}
        {renderStep()}
      </main>
    </div>
  );
}