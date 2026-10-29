import { ArrowLeft, ExternalLink, CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import EligibilityCriteria from './EligibilityCriteria';

export default function TrialDetails({ trial, onBack }) {
  if (!trial) return null;

  const statusConfig = {
    ELIGIBLE: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', label: 'ELIGIBLE' },
    NOT_ELIGIBLE: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', label: 'NOT ELIGIBLE' },
    UNKNOWN: { icon: HelpCircle, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', label: 'UNKNOWN' },
  };

  const config = statusConfig[trial.final_status] || statusConfig.UNKNOWN;
  const Icon = config.icon;

  return (
    <div className='max-w-4xl mx-auto p-6'>
      <button onClick={onBack} className='flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mb-4'>
        <ArrowLeft className='w-4 h-4' /> Back to results
      </button>

      <div className={'bg-white border rounded-xl p-5 mb-4 ' + config.border}>
        <div className='flex items-center gap-2 mb-2'>
          <Icon className={'w-5 h-5 ' + config.color} />
          <span className={'text-sm font-bold uppercase tracking-wide ' + config.color}>{config.label}</span>
        </div>
        <div className='text-xs text-slate-500 mb-1'>{trial.trial_id}</div>
        <h2 className='text-lg font-semibold text-slate-900 mb-2'>{trial.title}</h2>
        <div className='text-sm text-slate-600 mb-3'>{trial.brief_summary || 'No summary available.'}</div>
        <div className='flex flex-wrap gap-2 text-xs text-slate-500 mb-3'>
          <span>Status: {trial.status || 'Unknown'}</span>
          <span>Phase: {trial.phase || 'N/A'}</span>
          <span>Type: {trial.study_type || 'N/A'}</span>
        </div>
        {trial.source_url && (
          <a href={trial.source_url} target='_blank' rel='noopener noreferrer'
             className='inline-flex items-center gap-1 text-xs text-blue-600 hover:underline'>
            View on ClinicalTrials.gov <ExternalLink className='w-3 h-3' />
          </a>
        )}
      </div>

      <div className='bg-white border border-slate-200 rounded-xl p-5'>
        <h3 className='text-sm font-semibold text-slate-700 mb-3'>Eligibility Evaluation</h3>
        <EligibilityCriteria result={trial} />
      </div>

      {trial.verification && trial.verification.issues && trial.verification.issues.length > 0 && (
        <div className='mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4'>
          <h4 className='text-xs font-semibold text-amber-700 mb-2'>Verification Issues</h4>
          <ul className='list-disc list-inside text-xs text-amber-700 space-y-1'>
            {trial.verification.issues.map((issue, i) => <li key={i}>{issue}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
