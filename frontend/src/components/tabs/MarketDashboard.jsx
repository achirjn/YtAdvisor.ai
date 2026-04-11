import React from 'react';
import { useOutletContext } from 'react-router-dom';

const MarketDashboard = () => {
  const { apiPayload } = useOutletContext();
  
  if (!apiPayload) return null;

  const market = apiPayload.market || {};

  const marketTruth = market.market_truth;
  const dominantForce = market.dominant_force;
  const competitorWeakness = market.competitor_weakness;
  const audienceCraving = market.audience_craving;
  const rawContentGaps = market.content_gaps || [];
  let contentGapsList = [];
  if (Array.isArray(rawContentGaps)) {
    contentGapsList = rawContentGaps.map(g => typeof g === 'string' ? g : g.gap || JSON.stringify(g)).filter(Boolean);
  } else if (typeof rawContentGaps === 'string') {
    contentGapsList = rawContentGaps.split(/,\s*|\s+and\s+/).filter(Boolean);
  }
  
  const contentArchetype = market.content_archetype;
  const satisfactionRisk = market.satisfaction_risk;

  return (
    <div className="pt-8 pb-16 px-10 max-w-7xl mx-auto flex gap-12 w-full">
      {/* Tab Side Nav (Inner) */}
      <div className="w-1 flex-shrink-0 border-r border-[#1C1B1B] relative">
        <div className="sticky top-24 rotate-90 origin-left translate-x-4 whitespace-nowrap">
          <span className="text-[0.625rem] font-bold tracking-[0.4em] text-[#FF0000] uppercase font-headline">MARKET ANALYSIS</span>
        </div>
      </div>

      {/* Main Content Body */}
      <div className="flex-1 space-y-12">
        {/* Header Section */}
        <section>
          <span className="text-[#FF0000] font-headline font-bold tracking-[0.25em] text-[0.65rem] uppercase">ANALYSIS FEED</span>
          <h2 className="text-4xl md:text-5xl font-black font-headline text-[#E5E2E1] mt-2 tracking-tighter uppercase">MARKET ANALYSIS</h2>
        </section>

        {/* MARKET TRUTH */}
        {marketTruth && (
          <section className="p-10 rounded-sm relative overflow-hidden group bg-[#1C1B1B]">
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#FF0000]/5 rounded-full -mr-20 -mt-20 blur-3xl transition-all group-hover:bg-[#FF0000]/10"></div>
            <div className="relative z-10">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <span className="material-symbols-outlined text-9xl">radar</span>
              </div>
              <p className="text-2xl md:text-4xl font-headline font-black text-[#E5E2E1] leading-tight max-w-4xl uppercase">
                 "{marketTruth}"
              </p>
              <div className="mt-8 flex items-center gap-3">
                <span className="w-8 h-[1px] bg-[#FF0000]"></span>
                <span className="text-[0.6875rem] font-headline font-black text-[#FF0000] tracking-widest uppercase">CORE MARKET FACTOR</span>
              </div>
            </div>
          </section>
        )}

        {/* DOMINANT FORCE & COMPETITOR WEAKNESS (Render conditionally in flex grid) */}
        {(dominantForce || competitorWeakness) && (
          <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {dominantForce && (
              <div className="bg-[#1C1B1B] p-8 rounded-sm border-l-2 border-[#1C1B1B] flex flex-col justify-between min-h-[180px]">
                <div className="space-y-1 mb-4">
                  <span className="text-[#FF0000] font-headline font-black text-[0.6875rem] tracking-widest uppercase">PRIMARY DRIVER</span>
                </div>
                <p className="text-xl font-bold text-[#E5E2E1] leading-tight font-headline">{dominantForce}</p>
              </div>
            )}
            
            {competitorWeakness && (
              <div className="bg-[#1C1B1B] p-8 rounded-sm border-l-2 border-[#1C1B1B] flex flex-col justify-between min-h-[180px]">
                <div className="space-y-1 mb-4">
                  <span className="text-[#FF0000] font-headline font-black text-[0.6875rem] tracking-widest uppercase">COMPETITOR WEAKNESS</span>
                </div>
                <p className="text-xl font-bold text-[#E5E2E1] leading-tight font-headline">{competitorWeakness}</p>
              </div>
            )}
          </section>
        )}

        {/* AUDIENCE CRAVING */}
        {audienceCraving && (
          <section className="bg-[#1C1B1B] p-10 rounded-sm">
            <span className="text-[#FF0000] font-headline font-black text-[0.6875rem] tracking-widest uppercase block mb-8">AUDIENCE CRAVING</span>
            <p className="text-3xl md:text-4xl font-headline font-medium italic text-[#E5E2E1] leading-tight uppercase tracking-tight">
              "{audienceCraving}"
            </p>
          </section>
        )}

        {/* CONTENT GAPS */}
        {contentGapsList.length > 0 && (
          <section className="space-y-4">
             <span className="text-[#FF0000] font-headline font-bold tracking-[0.25em] text-[0.65rem] uppercase">IDENTIFIED CONTENT GAPS</span>
             <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {contentGapsList.map((gap, index) => (
                <div key={index} className="bg-[#1C1B1B] p-8 rounded-sm space-y-6 border border-[#2A2A2A]">
                  <span className="material-symbols-outlined text-[#FF0000] text-2xl">gps_fixed</span>
                  <p className="text-[#E5E2E1] font-headline font-bold text-lg leading-tight capitalize">{gap.trim()}</p>
                  <p className="text-[#E5E2E1]/40 font-mono text-[0.625rem] uppercase tracking-wider">Source: Market Scan</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* CONTENT ARCHETYPE */}
        {contentArchetype && (
          <section className="bg-[#1C1B1B] p-10 rounded-sm">
            <div className="flex flex-wrap gap-4 mb-8">
              <div className={`px-3 py-1 rounded-sm flex items-center gap-2 border-none transition-all ${contentArchetype.includes('VIRAL') ? 'bg-[#FF0000]/20' : 'bg-[#FF0000]/5 opacity-50'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${contentArchetype.includes('VIRAL') ? 'bg-[#FF0000] animate-[pulse_2s_ease-in-out_infinite]' : 'bg-[#FF0000]/30'}`}></div>
                <span className={`text-[0.65rem] font-headline font-bold uppercase tracking-widest ${contentArchetype.includes('VIRAL') ? 'text-[#FF0000]' : 'text-[#FF0000]/50'}`}>VIRAL REACH</span>
              </div>
              <div className={`px-3 py-1 rounded-sm flex items-center gap-2 border-none transition-all ${contentArchetype.includes('SEARCH') || contentArchetype.includes('EVERGREEN') ? 'bg-green-900/40' : 'bg-green-900/10 opacity-50'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${contentArchetype.includes('SEARCH') || contentArchetype.includes('EVERGREEN') ? 'bg-green-400 animate-[pulse_2s_ease-in-out_infinite]' : 'bg-green-700'}`}></div>
                <span className={`text-[0.65rem] font-headline font-bold uppercase tracking-widest ${contentArchetype.includes('SEARCH') || contentArchetype.includes('EVERGREEN') ? 'text-green-300' : 'text-green-700'}`}>SEARCH EVERGREEN</span>
              </div>
              <div className={`px-3 py-1 rounded-sm flex items-center gap-2 border-none transition-all ${contentArchetype.includes('CORE') || contentArchetype.includes('AUDIENCE') ? 'bg-blue-900/40' : 'bg-blue-900/10 opacity-50'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${contentArchetype.includes('CORE') || contentArchetype.includes('AUDIENCE') ? 'bg-blue-400 animate-[pulse_2s_ease-in-out_infinite]' : 'bg-blue-700'}`}></div>
                <span className={`text-[0.65rem] font-headline font-bold uppercase tracking-widest ${contentArchetype.includes('CORE') || contentArchetype.includes('AUDIENCE') ? 'text-blue-300' : 'text-blue-700'}`}>CORE AUDIENCE</span>
              </div>
            </div>
            <p className="text-2xl font-headline font-black text-[#E5E2E1] leading-tight mb-3 uppercase tracking-tight">CONTENT FORMAT: {contentArchetype}</p>
            <p className="text-[0.6875rem] font-mono text-[#E5E2E1]/40 uppercase tracking-[0.2em]">Format recommended by AI engine based on current market parameters.</p>
          </section>
        )}

        {/* SATISFACTION RISK */}
        {satisfactionRisk !== undefined && satisfactionRisk !== null && (
          <section className="max-w-md">
            <div className="bg-[#1C1B1B] p-8 rounded-sm flex items-center gap-8 border-l-2 border-[#1C1B1B]">
              <div className="flex flex-col items-center">
                <span className="text-5xl font-black font-headline text-[#FF0000] tracking-tighter">{satisfactionRisk}.0</span>
                <span className="text-[0.5rem] font-headline font-black text-[#E5E2E1]/40 uppercase tracking-widest mt-1">SCORE</span>
              </div>
              <div className="h-16 w-px bg-[#2A2A2A]"></div>
              <div className="flex-1">
                <span className="text-[#FF0000] font-headline font-black text-[0.6875rem] tracking-widest uppercase block mb-2">SATISFACTION RISK</span>
                <p className="text-xs text-[#E5E2E1]/80 leading-snug font-body">Algorithm identified an index drop-off threat level of {satisfactionRisk}/10 if pacing falls behind market standard.</p>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default MarketDashboard;
