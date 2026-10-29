import { useState, useEffect } from 'react';
import { Search, ChevronRight } from 'lucide-react';
import { getPatients } from '../api/mediatorApi';

export default function PatientSelector({ onSelect }) {
  const [patients, setPatients] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPatients()
      .then(data => { setPatients(data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, []);

  const filtered = patients.filter(p => {
    const text = (p.patient_id + ' ' + p.brats_id + ' ' + p.diagnosis + ' ' + p.sex + ' ' + p.grade).toLowerCase();
    return text.includes(filter.toLowerCase());
  });

  if (loading) return <div className='p-6 text-slate-500'>Loading patients...</div>;
  if (error) return <div className='p-6 text-red-600'>Error: {error}</div>;

  return (
    <div className='max-w-4xl mx-auto p-6'>
      <h2 className='text-lg font-semibold text-slate-800 mb-4'>Step 1: Select Patient</h2>
      <div className='relative mb-4'>
        <Search className='absolute left-3 top-2.5 w-4 h-4 text-slate-400' />
        <input
          type='text'
          placeholder='Search by ID, diagnosis, sex, grade...'
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className='w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
        />
      </div>
      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        {filtered.map(p => (
          <div key={p.patient_id} className='bg-white border border-slate-200 rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer'
               onClick={() => onSelect(p)}>
            <div className='flex items-center justify-between'>
              <div>
                <div className='font-semibold text-slate-900'>{p.patient_id}</div>
                {p.brats_id && <div className='text-xs text-slate-500'>{p.brats_id}</div>}
                <div className='text-sm text-slate-600'>Age: {p.age ?? 'N/A'} | Sex: {p.sex ?? 'N/A'}</div>
                <div className='text-sm text-slate-600'>Diagnosis: {p.diagnosis ?? 'N/A'}</div>
                <div className='text-xs text-slate-500'>Grade: {p.grade ?? 'N/A'} | MGMT: {p.MGMT_status ?? 'N/A'} | IDH: {p.IDH_status ?? 'N/A'}</div>
              </div>
              <ChevronRight className='w-5 h-5 text-slate-400' />
            </div>
          </div>
        ))}
      </div>
      {filtered.length === 0 && <div className='text-sm text-slate-500 mt-4'>No patients found.</div>}
    </div>
  );
}
