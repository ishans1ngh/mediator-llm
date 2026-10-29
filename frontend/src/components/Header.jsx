import { useState, useEffect } from 'react';

export default function Header() {
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    // Check demo mode status from backend
    fetch('/api/models/status')
      .then(res => res.json())
      .then(data => setDemoMode(data.demo_mode))
      .catch(() => setDemoMode(true)); // Default to demo mode if check fails
  }, []);

  return (
    <header className='bg-white border-b border-slate-200 sticky top-0 z-50'>
      <div className='max-w-6xl mx-auto px-6 py-4 flex items-center justify-between'>
        <div>
          <h1 className='text-xl font-bold text-slate-900 tracking-tight'>MEDIATOR-LLM</h1>
          <p className='text-xs text-slate-500'>Agentic Clinical Trial Matching System</p>
        </div>
        <div className='flex items-center gap-3'>
          {demoMode && (
            <div className='text-[10px] text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1 rounded-full'>
              DEMO MODE
            </div>
          )}
          <div className='text-[10px] text-amber-600 bg-amber-50 border border-amber-200 px-3 py-1 rounded-full'>
            Research prototype - not for clinical diagnosis or treatment decisions.
          </div>
        </div>
      </div>
    </header>
  );
}
