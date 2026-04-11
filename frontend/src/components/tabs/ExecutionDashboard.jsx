import React from 'react';
import { useOutletContext } from 'react-router-dom';

const ExecutionDashboard = () => {
  const { apiPayload } = useOutletContext();
  if (!apiPayload) return null;

  const execution = apiPayload.execution || {};

  const exactHookScript = execution.exact_hook_script;
  const pacingList = Array.isArray(execution.pacing_timeline) 
    ? execution.pacing_timeline 
    : [];
  
  const retentionTraps = Array.isArray(execution.retention_traps) ? execution.retention_traps : [];
  const winConditions = Array.isArray(execution.win_conditions) ? execution.win_conditions : [];
  const failConditions = Array.isArray(execution.fail_conditions) ? execution.fail_conditions : [];

  const shortsRecommended = execution.shorts_test_recommended === true;

  // Mock timestamps for the dynamic timeline rendering
  const getTimelineStamp = (index, total) => {
    if (index === 0) return "00:00";
    if (index === total - 1) return "08:30+"; 
    const minutes = Math.floor(index * 1.5);
    const seconds = Math.floor((index * 45) % 60);
    return `0${Math.min(minutes, 9)}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div 
      className="w-full min-h-screen pb-20"
      style={{
        backgroundColor: '#0a0a0a',
        backgroundImage: 'radial-gradient(at 0% 0%, rgba(151, 1, 0, 0.05) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(20, 20, 20, 1) 0px, transparent 50%)'
      }}
    >
      <div className="max-w-6xl mx-auto px-12 py-12 space-y-12 w-full">
        {/* Section Header */}
      <header className="flex items-end justify-between border-b border-[#E5E2E1]/20 pb-4">
        <div className="space-y-1">
          <h1 className="text-5xl font-headline font-extrabold tracking-tighter text-[#FFFFFF]">EXECUTION GUIDE</h1>
        </div>
      </header>

      {/* THE HOOK */}
      {exactHookScript && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-[#E5E2E1]">anchor</span>
            <h2 className="text-lg font-headline font-bold text-[#FFFFFF] tracking-tight uppercase">Hook Strategy</h2>
          </div>
          <div className="bg-[#0e0e0e] border border-[#E5E2E1]/10 p-10 relative group overflow-hidden shadow-[0_4px_30px_rgba(0,0,0,0.5)]">
            <div className="absolute top-0 left-0 w-1 h-full bg-[#970100]"></div>
            <div className="flex justify-between items-start mb-8">
              <span className="text-[10px] font-black text-[#970100] uppercase tracking-widest">HOOK SCRIPT</span>
            </div>
            <div className="space-y-6">
              <p className="text-2xl md:text-4xl font-mono font-medium leading-[1.4] text-[#E5E2E1]/90 text-center tracking-tight">
                "{exactHookScript}"
              </p>
              <div className="flex justify-center pt-8 border-t border-[#E5E2E1]/10">
                <span className="text-sm font-body italic text-[#E5E2E1]/40 text-center max-w-2xl px-8">
                  psychology: Deploy immediately at frame 0. Designed to create instant cognitive resonance and force a retention decision before the 5-second swipe threshold.
                </span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* PACING TIMELINE */}
      {pacingList.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-[#E5E2E1]">hourglass_top</span>
            <h2 className="text-lg font-headline font-bold text-[#FFFFFF] tracking-tight uppercase">Pacing Timeline</h2>
          </div>
          <div className="relative pl-8 space-y-0">
            {/* Vertical Line */}
            <div className="absolute left-[3.75rem] top-0 bottom-0 w-[1px] bg-[#970100]/30"></div>
            
            {pacingList.map((step, index) => (
              <div key={index} className="relative flex items-center py-6 group">
                <div className="w-24 text-right pr-12 font-mono text-[#FFFFFF] font-bold text-sm">
                  {getTimelineStamp(index, pacingList.length)}
                </div>
                <div className="absolute left-[3.5rem] w-2 h-2 rounded-full bg-[#970100] border-4 border-[#0a0a0a] z-10 transition-transform group-hover:scale-150"></div>
                <div className="flex-1 pl-12 flex justify-between items-center bg-[#1c1b1b]/50 hover:bg-[#1c1b1b] p-4 transition-colors border border-transparent hover:border-[#603e39]/30 rounded-sm cursor-default">
                  <span className="text-[#E5E2E1] font-headline font-bold text-sm md:text-base tracking-tight leading-relaxed line-clamp-2 md:line-clamp-none">
                    {step}
                  </span>
                  <span className="hidden md:inline-block ml-4 text-[#E5E2E1]/40 text-[10px] font-mono uppercase tracking-widest shrink-0">
                    Phase 0{index + 1}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* RETENTION TRAPS */}
      {retentionTraps.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-[#E5E2E1]">warning</span>
            <h2 className="text-lg font-headline font-bold text-[#FFFFFF] tracking-tight uppercase">Retention Traps & Fixes</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {retentionTraps.map((trap, index) => (
              <div key={index} className="bg-[#1c1b1b] p-6 border border-[#E5E2E1]/10 space-y-4 hover:border-[#970100]/50 transition-colors">
                <div className="flex items-center gap-2 text-[#FFA000]">
                  <span className="material-symbols-outlined text-xl">warning</span>
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#E5E2E1]/60">Risk at: {trap.moment}</span>
                </div>
                <h3 className="text-[#E5E2E1] font-headline font-bold text-sm leading-tight">
                  <span className="text-[#FF0000]">Risk:</span> {trap.reason}
                </h3>
                <div className="pt-4 flex items-start gap-2 text-[#4CAF50] border-t border-white/5">
                  <span className="material-symbols-outlined text-sm mt-0.5">build_circle</span>
                  <span className="text-[10px] font-bold uppercase tracking-widest leading-relaxed">Fix: {trap.fix}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* THE RULES */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Win Conditions */}
        {(winConditions.length > 0) && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-[#4CAF50]">
              <span className="material-symbols-outlined">verified</span>
              <h2 className="text-[11px] font-black uppercase tracking-[0.2em]">Win Conditions</h2>
            </div>
            <ul className="space-y-3">
              {winConditions.map((condition, idx) => (
                <li key={idx} className="flex items-start gap-4 p-4 bg-[#4CAF50]/5 border border-[#4CAF50]/10 rounded-sm">
                  <span className="material-symbols-outlined text-[#4CAF50] text-sm mt-0.5">check_circle</span>
                  <span className="text-sm font-medium text-[#E5E2E1]">{condition}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {/* Fail Conditions */}
        {(failConditions.length > 0) && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-[#970100]">
              <span className="material-symbols-outlined">cancel</span>
              <h2 className="text-[11px] font-black uppercase tracking-[0.2em]">Fail Conditions</h2>
            </div>
            <ul className="space-y-3">
              {failConditions.map((condition, idx) => (
                <li key={idx} className="flex items-start gap-4 p-4 bg-[#970100]/5 border border-[#970100]/10 rounded-sm">
                  <span className="material-symbols-outlined text-[#970100] text-sm mt-0.5">close</span>
                  <span className="text-sm font-medium text-[#E5E2E1]">{condition}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* SHORTS TEST BOUNDARY (Dynamic) */}
      {shortsRecommended && (
        <section>
          <div className="bg-[#0e0e0e] p-8 border border-[#E5E2E1]/10 border-l-4 border-l-[#970100] relative overflow-hidden shadow-2xl">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-3 h-3 bg-[#970100] rounded-full animate-pulse shadow-[0_0_8px_rgba(151,1,0,0.8)]"></div>
              <span className="text-[#E5E2E1] font-headline font-black text-xs uppercase tracking-widest">TACTICAL ALERT: SHORTS TEST RECOMMENDED</span>
            </div>
            <div className="flex flex-col md:flex-row gap-8 items-center">
              <div className="flex-1 space-y-4">
                <p className="text-[#E5E2E1] text-lg font-medium leading-relaxed">
                    Current hook metrics suggest high resonance for vertical displacement. Isolate the first 58 seconds and deploy as a 'Vertical Teaser' 2 hours prior to the main mission launch.
                </p>
                <div className="flex flex-wrap gap-4 pt-2">
                  <button className="bg-[#2a2a2a] hover:bg-[#3a3939] px-6 py-3 border border-[#603e39]/30 text-[10px] font-black uppercase tracking-widest transition-colors text-[#E5E2E1] rounded-sm">Download Segment</button>
                  <button className="bg-[#970100] hover:bg-[#c00100] text-white px-8 py-3 text-[10px] font-black uppercase tracking-widest shadow-lg shadow-[#970100]/20 transition-colors rounded-sm">Initiate Deploy</button>
                </div>
              </div>
              <div className="w-full md:w-64 h-32 bg-[#1c1b1b] rounded-sm relative group overflow-hidden border border-[#E5E2E1]/5">
                <img alt="Vertical Teaser Metric Map" className="w-full h-full object-cover opacity-50 grayscale group-hover:grayscale-0 group-hover:scale-110 transition-all duration-700" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDOs59IyLU96PssPdpnSy1M_2bVEOLXzSEZFD6t-pZ0zjn0uCFR9vB258TEXAWf5iGiHhE-O8wiodOxmKy2ze2SUPUlPy7UDBdSwidEhoEYkRqwUZyDZDadsOinCO1H7ubwpy4ZVi28mIGal7uIinJJaGHArfg5SjuoyNh4J4n2v_8m4jVGQrB5cUTlGhob8lgbCsOU2YZ3DXVid5CyVNgodV0q7z5rZwXTjsgYaDshzcyILLuk8455V-MevsCbHQeBJM0cm3igfgg"/>
                <div className="absolute inset-0 bg-gradient-to-t from-[#0e0e0e] to-transparent flex items-end p-4">
                  <span className="text-[9px] font-bold text-[#E5E2E1]/80 tracking-widest uppercase">Target: 1.2M Reach Est.</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      </div>
    </div>
  );
};

export default ExecutionDashboard;
