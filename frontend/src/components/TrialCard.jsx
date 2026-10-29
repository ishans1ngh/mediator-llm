import { CheckCircle, XCircle, HelpCircle } from 'lucide-react';

export default function TrialCard({ trial, onClick }) {
  const status = trial.final_status;
  const summary = trial.criteria_summary || {};

  // Map backend status (YES/NO/UNKNOWN) to UI labels (ELIGIBLE/NOT_ELIGIBLE/UNKNOWN)
  const statusMapping = {
    'YES': 'ELIGIBLE',
    'NO': 'NOT_ELIGIBLE',
    'UNKNOWN': 'UNKNOWN',
    'ELIGIBLE': 'ELIGIBLE',
    'NOT_ELIGIBLE': 'NOT_ELIGIBLE',
  };

  const mappedStatus = statusMapping[status] || 'UNKNOWN';

  const statusConfig = {
    ELIGIBLE: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', label: 'ELIGIBLE' },
    NOT_ELIGIBLE: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', label: 'NOT ELIGIBLE' },
    UNKNOWN: { icon: HelpCircle, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', label: 'UNKNOWN' },
  };

  const config = statusConfig[mappedStatus] || statusConfig.UNKNOWN;
  const Icon = config.icon;

  return (
    <div onClick={onClick} className={'bg-white border rounded-xl p-4 cursor-pointer hover:shadow-md transition-shadow ' + config.border}>
      <div className='flex items-start justify-between mb-2'>
        <div>
          <div className='text-xs font-medium text-slate-500 mb-0.5'>{trial.trial_id}</div>
          <div className='text-sm font-semibold text-slate-900 leading-tight'>{trial.title}</div>
        </div>
        <div className={'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ' + config.bg + ' ' + config.color}>
          <Icon className='w-3.5 h-3.5' />
          {config.label}
        </div>
      </div>
      <div className='text-xs text-slate-500 mb-2'>
        Status: {trial.status || 'Unknown'} | Conditions: {(trial.conditions || []).join(', ') || 'N/A'}
      </div>
      <div className='flex gap-3 text-xs'>
        <span className='text-green-600'>{summary.yes || 0} satisfied</span>
        <span className='text-red-600'>{summary.no || 0} failed</span>
        <span className='text-amber-600'>{summary.unknown || 0} unknown</span>
      </div>
    </div>
  );
}
