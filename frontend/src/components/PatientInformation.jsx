import { useState } from 'react';
import { Edit2, Save, X, Info } from 'lucide-react';

function SectionCard({ title, children }) {
  return (
    <div className='bg-white border border-slate-200 rounded-xl p-4 mb-4'>
      <h3 className='text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide'>{title}</h3>
      {children}
    </div>
  );
}

function EditableField({ label, value, source, onChange, editMode }) {
  const [editing, setEditing] = useState(false);
  const [localValue, setLocalValue] = useState(value);

  const displayValue = value === null || value === undefined ? 'Not available' : String(value);
  const sourceLabel = source || 'Not available';

  if (!editMode) {
    return (
      <div className='mb-2'>
        <div className='text-xs text-slate-500'>{label}</div>
        <div className='text-sm text-slate-900'>{displayValue}</div>
        <div className='text-[10px] text-slate-400'>Source: {sourceLabel}</div>
      </div>
    );
  }

  return (
    <div className='mb-2'>
      <div className='text-xs text-slate-500 flex items-center gap-1'>
        {label}
        {!editing && (
          <button onClick={() => setEditing(true)} className='text-blue-500 hover:text-blue-700'>
            <Edit2 className='w-3 h-3' />
          </button>
        )}
      </div>
      {!editing ? (
        <>
          <div className='text-sm text-slate-900'>{displayValue}</div>
          <div className='text-[10px] text-slate-400'>Source: {sourceLabel}</div>
        </>
      ) : (
        <div className='flex items-center gap-2 mt-1'>
          <input
            type='text'
            value={localValue === null || localValue === undefined ? '' : localValue}
            onChange={e => setLocalValue(e.target.value)}
            className='flex-1 text-sm border border-slate-300 rounded px-2 py-1'
          />
          <button onClick={() => { onChange(localValue); setEditing(false); }} className='text-green-600'>
            <Save className='w-4 h-4' />
          </button>
          <button onClick={() => { setLocalValue(value); setEditing(false); }} className='text-red-600'>
            <X className='w-4 h-4' />
          </button>
        </div>
      )}
    </div>
  );
}

export default function PatientInformation({ profile, onUpdate, onContinue }) {
  const [editMode, setEditMode] = useState(false);

  if (!profile) return null;

  const handleFieldChange = (section, field, value) => {
    const updated = { ...profile };
    if (!updated[section]) updated[section] = {};
    if (!updated[section][field]) updated[section][field] = {};
    updated[section][field] = { ...updated[section][field], value, source: 'Modified by user', modified_by_user: true };
    if (onUpdate) onUpdate(updated);
  };

  return (
    <div className='max-w-4xl mx-auto p-6'>
      <div className='flex items-center justify-between mb-4'>
        <h2 className='text-lg font-semibold text-slate-800'>Step 3: Review Patient Information</h2>
        <button
          onClick={() => setEditMode(!editMode)}
          className={'px-3 py-1.5 text-xs rounded-lg font-medium ' + (editMode ? 'bg-slate-200 text-slate-800' : 'bg-blue-600 text-white hover:bg-blue-700')}
        >
          {editMode ? 'Done Editing' : 'Edit Data'}
        </button>
      </div>

      <SectionCard title='Identifiers'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='Patient ID' value={profile.patient_id} source='Clinical Dataset' editMode={false} onChange={() => {}} />
          <EditableField label='BraTS ID' value={profile.brats_id} source='Clinical Dataset' editMode={false} onChange={() => {}} />
        </div>
      </SectionCard>

      <SectionCard title='Demographics'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='Age' value={profile.demographics?.age?.value} source={profile.demographics?.age?.source}
            editMode={editMode} onChange={v => handleFieldChange('demographics', 'age', v)} />
          <EditableField label='Sex' value={profile.demographics?.sex?.value} source={profile.demographics?.sex?.source}
            editMode={editMode} onChange={v => handleFieldChange('demographics', 'sex', v)} />
          <EditableField label='Race' value={profile.demographics?.race?.value} source={profile.demographics?.race?.source}
            editMode={editMode} onChange={v => handleFieldChange('demographics', 'race', v)} />
          <EditableField label='Ethnicity' value={profile.demographics?.ethnicity?.value} source={profile.demographics?.ethnicity?.source}
            editMode={editMode} onChange={v => handleFieldChange('demographics', 'ethnicity', v)} />
        </div>
      </SectionCard>

      <SectionCard title='Diagnosis'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='Primary Diagnosis' value={profile.diagnosis?.primary_diagnosis?.value} source={profile.diagnosis?.primary_diagnosis?.source}
            editMode={editMode} onChange={v => handleFieldChange('diagnosis', 'primary_diagnosis', v)} />
          <EditableField label='WHO 2021 Diagnosis' value={profile.diagnosis?.who_diagnosis?.value} source={profile.diagnosis?.who_diagnosis?.source}
            editMode={editMode} onChange={v => handleFieldChange('diagnosis', 'who_diagnosis', v)} />
          <EditableField label='Non-WHO Diagnosis' value={profile.diagnosis?.non_who_diagnosis?.value} source={profile.diagnosis?.non_who_diagnosis?.source}
            editMode={editMode} onChange={v => handleFieldChange('diagnosis', 'non_who_diagnosis', v)} />
          <EditableField label='Tumor Type' value={profile.diagnosis?.tumor_type?.value} source={profile.diagnosis?.tumor_type?.source}
            editMode={editMode} onChange={v => handleFieldChange('diagnosis', 'tumor_type', v)} />
          <EditableField label='Grade' value={profile.diagnosis?.grade?.value} source={profile.diagnosis?.grade?.source}
            editMode={editMode} onChange={v => handleFieldChange('diagnosis', 'grade', v)} />
          <EditableField label='Disease' value={profile.diagnosis?.disease?.value} source={profile.diagnosis?.disease?.source}
            editMode={editMode} onChange={v => handleFieldChange('diagnosis', 'disease', v)} />
        </div>
      </SectionCard>

      <SectionCard title='Biomarkers'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='IDH Status' value={profile.biomarkers?.IDH_status?.value} source={profile.biomarkers?.IDH_status?.source}
            editMode={editMode} onChange={v => handleFieldChange('biomarkers', 'IDH_status', v)} />
          <EditableField label='MGMT Status' value={profile.biomarkers?.MGMT_status?.value} source={profile.biomarkers?.MGMT_status?.source}
            editMode={editMode} onChange={v => handleFieldChange('biomarkers', 'MGMT_status', v)} />
          <EditableField label='ATRX Status' value={profile.biomarkers?.ATRX_status?.value} source={profile.biomarkers?.ATRX_status?.source}
            editMode={editMode} onChange={v => handleFieldChange('biomarkers', 'ATRX_status', v)} />
          <EditableField label='1p/19q Status' value={profile.biomarkers?.status_1p19q?.value} source={profile.biomarkers?.status_1p19q?.source}
            editMode={editMode} onChange={v => handleFieldChange('biomarkers', 'status_1p19q', v)} />
          <EditableField label='Biomarkers' value={profile.biomarkers?.other?.value} source={profile.biomarkers?.other?.source}
            editMode={editMode} onChange={v => handleFieldChange('biomarkers', 'other', v)} />
        </div>
      </SectionCard>

      <SectionCard title='Treatment History'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='Surgery' value={profile.treatment_history?.surgery?.value} source={profile.treatment_history?.surgery?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'surgery', v)} />
          <EditableField label='Surgery Extend' value={profile.treatment_history?.surgery_extend?.value} source={profile.treatment_history?.surgery_extend?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'surgery_extend', v)} />
          <EditableField label='Number of Surgeries' value={profile.treatment_history?.number_of_surgeries?.value} source={profile.treatment_history?.number_of_surgeries?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'number_of_surgeries', v)} />
          <EditableField label='Radiation' value={profile.treatment_history?.radiation?.value} source={profile.treatment_history?.radiation?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'radiation', v)} />
          <EditableField label='Radiation Courses' value={profile.treatment_history?.number_of_radiation_courses?.value} source={profile.treatment_history?.number_of_radiation_courses?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'number_of_radiation_courses', v)} />
          <EditableField label='Chemotherapy' value={profile.treatment_history?.chemotherapy?.value} source={profile.treatment_history?.chemotherapy?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'chemotherapy', v)} />
          <EditableField label='Immunotherapy' value={profile.treatment_history?.immunotherapy?.value} source={profile.treatment_history?.immunotherapy?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'immunotherapy', v)} />
          <EditableField label='Other Treatment' value={profile.treatment_history?.other_treatment?.value} source={profile.treatment_history?.other_treatment?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'other_treatment', v)} />
          <EditableField label='Overall Survival' value={profile.treatment_history?.overall_survival?.value} source={profile.treatment_history?.overall_survival?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'overall_survival', v)} />
          <EditableField label='Progression-Free Survival' value={profile.treatment_history?.progression_free_survival?.value} source={profile.treatment_history?.progression_free_survival?.source}
            editMode={editMode} onChange={v => handleFieldChange('treatment_history', 'progression_free_survival', v)} />
        </div>
      </SectionCard>

      <SectionCard title='Clinical Data'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='Performance Status' value={profile.clinical_data?.performance_status?.value} source={profile.clinical_data?.performance_status?.source}
            editMode={editMode} onChange={v => handleFieldChange('clinical_data', 'performance_status', v)} />
          <EditableField label='Days to Initial Surgery' value={profile.clinical_data?.days_to_initial_surgery?.value} source={profile.clinical_data?.days_to_initial_surgery?.source}
            editMode={editMode} onChange={v => handleFieldChange('clinical_data', 'days_to_initial_surgery', v)} />
          <EditableField label='Days to Last Follow-up' value={profile.clinical_data?.days_to_last_followup?.value} source={profile.clinical_data?.days_to_last_followup?.source}
            editMode={editMode} onChange={v => handleFieldChange('clinical_data', 'days_to_last_followup', v)} />
          <EditableField label='Comorbidities' value={profile.clinical_data?.comorbidities?.value} source={profile.clinical_data?.comorbidities?.source}
            editMode={editMode} onChange={v => handleFieldChange('clinical_data', 'comorbidities', v)} />
          <EditableField label='Medications' value={profile.clinical_data?.medications?.value} source={profile.clinical_data?.medications?.source}
            editMode={editMode} onChange={v => handleFieldChange('clinical_data', 'medications', v)} />
        </div>
      </SectionCard>

      <SectionCard title='Imaging Metadata'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='Manufacturer' value={profile.imaging_metadata?.manufacturer?.value} source={profile.imaging_metadata?.manufacturer?.source}
            editMode={editMode} onChange={v => handleFieldChange('imaging_metadata', 'manufacturer', v)} />
          <EditableField label='Model' value={profile.imaging_metadata?.manufacturer_model?.value} source={profile.imaging_metadata?.manufacturer_model?.source}
            editMode={editMode} onChange={v => handleFieldChange('imaging_metadata', 'manufacturer_model', v)} />
          <EditableField label='Field Strength' value={profile.imaging_metadata?.magnetic_field_strength?.value} source={profile.imaging_metadata?.magnetic_field_strength?.source}
            editMode={editMode} onChange={v => handleFieldChange('imaging_metadata', 'magnetic_field_strength', v)} />
        </div>
      </SectionCard>

      <SectionCard title='MRI Analysis'>
        <div className='grid grid-cols-2 gap-4'>
          <EditableField label='Scan Status' value={profile.mri?.scan_status?.value} source={profile.mri?.scan_status?.source}
            editMode={false} onChange={() => {}} />
          <EditableField label='Segmentation Status' value={profile.mri?.segmentation_status?.value} source={profile.mri?.segmentation_status?.source}
            editMode={false} onChange={() => {}} />
          <EditableField label='Tumor Detected' value={profile.mri?.tumor_detected?.value} source={profile.mri?.tumor_detected?.source}
            editMode={false} onChange={() => {}} />
          <EditableField label='Feature Vector Available' value={profile.mri?.feature_vector_available?.value} source={profile.mri?.feature_vector_available?.source}
            editMode={false} onChange={() => {}} />
        </div>
      </SectionCard>

      {profile.source_info?.demo_mode && (
        <div className='flex items-center gap-2 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4'>
          <Info className='w-4 h-4' /> Demo mode enabled. MRI results are simulated.
        </div>
      )}

      <button onClick={onContinue} className='w-full py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium'>
        Find Clinical Trials
      </button>
    </div>
  );
}
