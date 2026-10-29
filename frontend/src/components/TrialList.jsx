import TrialCard from './TrialCard';

export default function TrialList({ trials, onSelectTrial }) {
  if (!trials || trials.length === 0) {
    return <div className='p-6 text-slate-500 text-sm'>No trials found.</div>;
  }

  return (
    <div className='max-w-4xl mx-auto p-6'>
      <h2 className='text-lg font-semibold text-slate-800 mb-4'>Step 4: Trial Results</h2>
      <div className='grid grid-cols-1 gap-4'>
        {trials.map((trial, idx) => (
          <TrialCard key={trial.trial_id || idx} trial={trial} onClick={() => onSelectTrial(trial)} />
        ))}
      </div>
    </div>
  );
}
