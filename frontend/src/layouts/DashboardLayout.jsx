import React, { useMemo } from 'react';
import { Navigate, Outlet, NavLink, Link } from 'react-router-dom';

const DashboardLayout = () => {
  // Read exactly from local cache to endure user browser reloads!
  const cachedDataStr = localStorage.getItem('dimenziq_analysis');
  
  const parsedData = useMemo(() => {
    try {
      return cachedDataStr ? JSON.parse(cachedDataStr) : null;
    } catch {
      return null;
    }
  }, [cachedDataStr]);

  // If there's literally no data, send them straight back to input
  if (!parsedData) {
    return <Navigate to="/analyze" replace />;
  }

  // Spring Boot maps the Python output to tab-named keys directly
  const apiPayload = parsedData || {};

  // Sidebar values from the correct keys
  const finalVerdict = apiPayload.verdict?.final_verdict || '';
  const confidence = apiPayload.verdict?.confidence || '';
  const confidenceReason = apiPayload.verdict?.confidence_reason || '';
  const satisfactionRisk = apiPayload.market?.satisfaction_risk;
  const smallCreatorVerdict = apiPayload.market?.small_creator_verdict || '';

  return (
    <div className="bg-[#0A0A0A] text-[#E5E2E1] font-body flex overflow-hidden h-screen selection:bg-primary/30">
      
      {/* Sidebar Wrapper */}
      <aside className="h-screen w-64 flex-shrink-0 border-r border-[#1C1B1B] bg-[#0A0A0A] flex flex-col py-6 px-4 z-50 overflow-hidden relative">
        {/* Brand Header */}
        <div className="mb-6 px-2">
          <Link to="/" className="block">
            <h1 className="text-xl font-black text-[#E5E2E1] tracking-tighter uppercase font-headline">DASHBOARD</h1>
            <p className="text-[0.6875rem] font-bold uppercase tracking-wider text-[#FF0000] font-headline">DIMENZIQ ANALYTICS</p>
          </Link>
        </div>

        {/* Tactical Stats Sections */}
        <nav className="flex-1 space-y-5 overflow-y-auto pb-4" style={{scrollbarWidth: 'none'}}>
          {/* Final Verdict */}
          {finalVerdict && (
            <div className="space-y-0.5">
              <span className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-[#E5E2E1]/40 font-headline">VERDICT</span>
              <div className="text-5xl font-black text-[#00FF41] font-headline tracking-tighter">{finalVerdict}</div>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="space-y-6">
            {/* Confidence */}
            <div className="space-y-1.5">
              <span className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-[#E5E2E1]/40 font-headline">CONFIDENCE</span>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full animate-[pulse_2s_ease-in-out_infinite] ${confidence.toUpperCase() === 'HIGH' ? 'bg-[#00FF41]' : 'bg-[#FF0000]'}`}></span>
                <span className={`text-sm font-bold tracking-widest uppercase ${confidence.toUpperCase() === 'HIGH' ? 'text-[#00FF41]' : 'text-[#E5E2E1]'}`}>
                  {confidence || 'PENDING'}
                </span>
              </div>
              <p className="text-[0.6875rem] font-mono text-[#E5E2E1]/40 leading-tight">
                {confidenceReason}
              </p>
            </div>

            {/* Satisfaction Risk Gauge */}
            {satisfactionRisk !== undefined && satisfactionRisk !== null && (
              <div className="space-y-2">
                <span className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-[#E5E2E1]/40 font-headline">SATISFACTION RISK</span>
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle className="text-[#1C1B1B]" cx="32" cy="32" fill="transparent" r="28" stroke="currentColor" strokeWidth="4"></circle>
                    <circle className="text-[#FF0000]" cx="32" cy="32" fill="transparent" r="28" stroke="currentColor" strokeDasharray="175.9" strokeDashoffset={175.9 - (175.9 * (satisfactionRisk / 10))} strokeWidth="4"></circle>
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center font-headline font-bold text-lg text-[#FF0000]">{satisfactionRisk}.0</span>
                </div>
              </div>
            )}

            {/* Creator Verdict */}
            <div className="space-y-1">
              <span className="text-[0.625rem] font-bold uppercase tracking-[0.2em] text-[#E5E2E1]/40 font-headline">SMALL CHANNEL VERDICT</span>
              <div>
                <span className={`inline-block px-2 py-0.5 border text-[0.6875rem] font-black uppercase tracking-widest rounded-sm ${smallCreatorVerdict === 'HARD' || smallCreatorVerdict === 'AVOID' ? 'bg-[#FF0000]/10 border-[#FF0000]/30 text-[#FF0000]' : 'bg-[#00FF41]/10 border-[#00FF41]/30 text-[#00FF41]'}`}>
                  {smallCreatorVerdict || 'AWAITING DATA'}
                </span>
              </div>
            </div>
          </div>
        </nav>

        {/* Bottom Alert (Conditional feature) */}
        {apiPayload.execution?.shorts_test_recommended && (
          <div className="mt-auto pt-4 border-t border-[#1C1B1B]">
            <div className="bg-[#FF0000]/10 border border-[#FF0000]/20 p-3 rounded-sm flex items-start gap-3">
              <span className="material-symbols-outlined text-[#FF0000] text-lg animate-[pulse_2s_ease-in-out_infinite]" style={{fontVariationSettings: "'FILL' 1"}}>error</span>
              <div className="space-y-0.5">
                <p className="text-[0.625rem] font-bold text-[#FF0000] uppercase tracking-wider">SYSTEM RECOMMENDATION</p>
                <p className="text-[0.75rem] font-medium leading-tight text-[#E5E2E1]">Shorts test recommended</p>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content Area (Scrolls independently) */}
      <div className="flex-1 flex flex-col min-w-0 relative h-screen bg-[#0A0A0A]">
        {/* Top Navigation */}
        <header className="h-16 flex-shrink-0 bg-[#131313]/80 backdrop-blur-xl border-b border-[#1C1B1B] flex justify-between items-center px-8 z-40 sticky top-0">
          <div className="flex items-center gap-8">
            <span className="text-2xl font-black text-[#E5E2E1] font-headline tracking-tighter">DIMENZIQ</span>
            <div className="h-4 w-px bg-[#1C1B1B]"></div>
            <div className="flex gap-6">
              <NavLink to="/results/verdict" className={({isActive}) => isActive ? "text-[#FF0000] border-b-2 border-[#FF0000] pb-2 font-headline font-bold text-sm tracking-widest" : "text-[#E5E2E1]/40 hover:text-[#E5E2E1] transition-all font-headline font-bold text-sm tracking-widest pb-2"}>VERDICT</NavLink>
              <NavLink to="/results/market" className={({isActive}) => isActive ? "text-[#FF0000] border-b-2 border-[#FF0000] pb-2 font-headline font-bold text-sm tracking-widest" : "text-[#E5E2E1]/40 hover:text-[#E5E2E1] transition-all font-headline font-bold text-sm tracking-widest pb-2"}>MARKET</NavLink>
              <NavLink to="/results/creative" className={({isActive}) => isActive ? "text-[#FF0000] border-b-2 border-[#FF0000] pb-2 font-headline font-bold text-sm tracking-widest" : "text-[#E5E2E1]/40 hover:text-[#E5E2E1] transition-all font-headline font-bold text-sm tracking-widest pb-2"}>CREATIVE</NavLink>
              <NavLink to="/results/execution" className={({isActive}) => isActive ? "text-[#FF0000] border-b-2 border-[#FF0000] pb-2 font-headline font-bold text-sm tracking-widest" : "text-[#E5E2E1]/40 hover:text-[#E5E2E1] transition-all font-headline font-bold text-sm tracking-widest pb-2"}>EXECUTION</NavLink>
              <NavLink to="/results/growth" className={({isActive}) => isActive ? "text-[#FF0000] border-b-2 border-[#FF0000] pb-2 font-headline font-bold text-sm tracking-widest" : "text-[#E5E2E1]/40 hover:text-[#E5E2E1] transition-all font-headline font-bold text-sm tracking-widest pb-2"}>GROWTH</NavLink>
            </div>
          </div>
          <div className="flex items-center gap-6">
            {/* Navigates cleanly back to InputPage */}
            <Link to="/analyze" className="bg-[#970100] text-[#E5E2E1] px-5 py-2 text-xs font-black uppercase tracking-widest rounded-sm hover:shadow-[0_0_15px_rgba(255,0,0,0.3)] transition-all active:scale-95">NEW ANALYSIS</Link>
            <img alt="Commander Avatar" className="w-8 h-8 rounded-full border border-[#FF0000]/50 object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBqO240ldX39QP_R_0hXR20ke2jhaGm0Yix6q1SDP8UMs2692PGodfYIRl1e8yAIylpfiK4VWaD1jmnn5Zt00Bv6PVKQeYIWf-JpVYkRh_O14RP6tzyg5zfSZwR5bD92-i39Rkc0iJs_af-f89xoXDixC825XSAAbbA9IS49b7Pq5psZnOdkOofm8bZ7Hiz_YdZD-Im70NJUouEz9Uk8glzyG7qPCwmunQmrVzAwxwMoMLb02I7jcbrJUKqu52dvO-VFbYpDRQWE3g"/>
          </div>
        </header>

        {/* Tab Outlet wrapped in a flex layout to ensure footer stays at the bottom */}
        <div className="flex-1 overflow-y-auto w-full flex flex-col bg-[#0A0A0A] scroll-smooth">
           <Outlet context={{ apiPayload }} />
           
           {/* Global Tab Footer (Does NOT overlap sidebar because it's in this flex-1 column) */}
           <footer className="w-full border-t border-[#1C1B1B] py-8 bg-[#0A0A0A] mt-auto">
             <div className="px-8 flex flex-col md:flex-row justify-between items-center gap-8">
               <div className="flex flex-col gap-1">
                 <span className="text-[#FF0000] font-black tracking-tighter text-sm font-headline uppercase">DIMENZIQ ANALYSIS</span>
                 <span className="text-[9px] font-mono text-[#E5E2E1]/30 uppercase tracking-widest">Version Alpha-01.82</span>
               </div>
               <div className="flex gap-8">
                  <Link className="text-[10px] font-mono text-[#E5E2E1]/40 uppercase tracking-[0.2em] hover:text-[#FF0000] transition-colors" to="/">Main</Link>
                  <Link className="text-[10px] font-mono text-[#E5E2E1]/40 uppercase tracking-[0.2em] hover:text-[#FF0000] transition-colors" to="/analyze">Configure Input</Link>
               </div>
             </div>
           </footer>
        </div>


      </div>
    </div>
  );
};

export default DashboardLayout;
