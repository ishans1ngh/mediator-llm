import { CheckCircle, XCircle, HelpCircle } from 'lucide-react';

function CriterionItem({ item }) {
  const statusConfig = {
    YES: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
    NO: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
    UNKNOWN: { icon: HelpCircle, color: 'text-amber-600', bg: 'bg-amber-50' },
  };
  const config = statusConfig[item.status] || statusConfig.UNKNOWN;
  const Icon = config.icon;

  return (
    <div className={'border rounded-lg p-3 mb-2 ' + (item.status === 'YES' ? 'border-green-200' : item.status === 'NO' ? 'border-red-200' : 'border-amber-200')}>
      <div className='flex items-start gap-2'>
        <Icon className={'w-4 h-4 mt-0.5 ' + config.color} />
        <div className='flex-1'>
          <div className='text-sm text-slate-800 font-medium'>{item.criterion}</div>
          <div className='text-xs text-slate-500 mt-1'>Patient: {item.patient_value === null || item.patient_value === undefined ? 'N/A' : String(item.patient_value)}</div>
          <div className='text-xs text-slate-500'>Reason: {item.reason}</div>
          <div className='text-[10px] text-slate-400 mt-1'>Source: {item.evidence_source}</div>
        </div>
        <span className={'text-xs font-semibold px-2 py-0.5 rounded ' + config.bg + ' ' + config.color}>{item.status}</span>
      </div>
    </div>
  );
}

export default function EligibilityCriteria({ result }) {
  if (!result) return null;

  return (
    <div className='space-y-4'>
      {result.inclusion && result.inclusion.length > 0 && (
        <div>
          <h4 className='text-sm font-semibold text-slate-700 mb-2'>Inclusion Criteria</h4>
          {result.inclusion.map((item, i) => <CriterionItem key={'inc-' + i} item={item} />)}
        </div>
      )}
      {result.exclusion && result.exclusion.length > 0 && (
        <div>
          <h4 className='text-sm font-semibold text-slate-700 mb-2'>Exclusion Criteria</h4>
          {result.exclusion.map((item, i) => <CriterionItem key={'exc-' + i} item={item} />)}
        </div>
      )}
      {result.unknown && result.unknown.length > 0 && (
        <div>
          <h4 className='text-sm font-semibold text-slate-700 mb-2'>Unknown Criteria</h4>
          {result.unknown.map((item, i) => <CriterionItem key={'unk-' + i} item={item} />)}
        </div>
      )}
    </div>
  );
}
