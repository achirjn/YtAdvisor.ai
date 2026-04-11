import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const ResultsDashboard = () => {
  const { state } = useLocation();
  const data = state?.data || {};

  // The backend wraps the response payload inside a "data" property and splits into 3 categories
  const apiPayload = data?.data || {};
  const analyst = apiPayload.analyst || {};
  const strategist = apiPayload.strategist || {};
  const optimizer = apiPayload.optimizer || {};

  // Directly mapping backend properties 
  const finalVerdict = optimizer.final_verdict || "Awaiting API...";
  const verdictReasoning = analyst.market_truth || "[API Data Missing: market_truth]";
  const exactHookScript = strategist.exact_hook_script || "[API Data Missing: exact_hook_script]";
  const thumbnailStrategy = strategist.thumbnail_contrast_prompt || "[API Data Missing: thumbnail_contrast_prompt]";
  
  const titlePsychologyDesc = strategist.title_psychology || "[API Data Missing: title_psychology]";
  const satisfactionRisk = analyst.satisfaction_risk || 0;
  const metrics = optimizer.performance_outlook || "[API Data Missing: performance_outlook]";
  
  const pacingGuide = optimizer.pacing_guide || "[API Data Missing: pacing_guide]";
  const dominantForce = analyst.dominant_force || "[API Data Missing: dominant_force]";
  const channelLeverage = analyst.channel_leverage || "[API Data Missing: channel_leverage]";
  
  const showShortsWarning = optimizer.shorts_test_recommended === true;

  // The UI designed arrays for these, but backend sent paragraphs. We'll split by sentences/commas for a clean UI layout.
  const qualityUpgradesList = (optimizer.quality_upgrades || "").split('. ').filter(Boolean);
  const postPublishList = (optimizer.post_publish_strategy || "").split('. ').filter(Boolean);
  const contentGapsList = (analyst.content_gaps || "").split(/,\s*|\s+and\s+/).filter(Boolean);

  return (
    <div className="bg-[#0A0A0A] text-[#e5e2e1] font-body selection:bg-primary/30 min-h-screen relative">
      
      {/* Top Navigation Bar */}
      <nav className="sticky top-0 z-50 bg-[#0A0A0A] border-b border-white/5 flex justify-between items-center w-full px-6 h-16">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-xl font-bold tracking-tighter text-[#E5E2E1] font-headline uppercase">DimenzIq</Link>
          <div className="hidden md:flex gap-6 ml-8">
            <a className="text-[#FF0000] font-bold text-[0.6875rem] uppercase tracking-wider font-label transition-colors" href="#verdict">Verdict</a>
            <a className="text-[#A5A2A1] hover:bg-white/5 text-[0.6875rem] uppercase tracking-wider font-label transition-colors px-2 py-1" href="#attack-plan">Tactical</a>
            <a className="text-[#A5A2A1] hover:bg-white/5 text-[0.6875rem] uppercase tracking-wider font-label transition-colors px-2 py-1" href="#market-math">Market</a>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="material-symbols-outlined text-[#A5A2A1] hover:text-[#FF0000] transition-colors" data-icon="notifications">notifications</button>
          <button className="material-symbols-outlined text-[#A5A2A1] hover:text-[#FF0000] transition-colors" data-icon="settings">settings</button>
          <div className="w-8 h-8 rounded-full overflow-hidden border border-white/5">
            <img alt="User Profile" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCsd3TGImHKL7XsQsYsVMcMoXvd0vd-a44wpmaKFHd5wshKDkQU1Jth6RYKR8f9OdRVHnLrIuFsMCzyskkaNFDyvNMskwfR8U0BEZgGZRWJjLRxhMyBracGHWuhnEGy238g825V34biQgeWFsWay9XkdCA-d8nQAUZ6SRbg1LH80McYfRZhs5gmdxCP8ijGMOPrC3-f6mdWIPhPSWESGe32mcLaNrIZR-NzJjIHzHvGzEInYWk80uIXi9KittKoQ5D3M0hce4f_jJQ"/>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-12 space-y-24">
        {/* 1. THE EXECUTIVE VERDICT */}
        <section id="verdict">
          <div className="flex flex-col md:flex-row md:items-baseline gap-6 mb-8">
            <h1 className="text-8xl md:text-[12rem] font-headline font-bold tracking-tighter text-on-surface text-glow leading-none uppercase" style={{ textShadow: "0 0 20px rgba(255, 0, 0, 0.3)" }}>
              {finalVerdict}
            </h1>
            <span className="inline-flex items-center px-4 py-2 bg-[#FF0000] text-white text-xs font-bold uppercase tracking-[0.25em] rounded-sm transform md:-translate-y-12">
              Educational Storytelling
            </span>
          </div>
          <div className="max-w-4xl">
            <p className="text-2xl md:text-4xl text-on-surface leading-tight font-light font-headline">
              {verdictReasoning.split('"The Kinetic Instrument"').map((part, index, array) => (
                <span key={index}>
                  {part}
                  {index !== array.length - 1 && <span className="text-[#FF0000] italic">"The Kinetic Instrument"</span>}
                </span>
              ))}
            </p>
          </div>
        </section>

        {/* 2. THE ATTACK PLAN */}
        <section className="space-y-8" id="attack-plan">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-headline font-bold uppercase tracking-[0.4em] text-[#FF0000]">The Attack Plan</h2>
            <div className="flex-grow h-[1px] bg-white/5"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-white/5 border border-white/5">
            {/* Hook Script */}
            <div className="bg-[#0A0A0A] p-10 space-y-6">
              <label className="text-[10px] font-label font-bold uppercase tracking-widest text-on-surface-variant block">Exact Hook Script</label>
              <div className="bg-white/5 p-8 font-mono text-xl leading-relaxed border border-white/5 text-on-surface select-all">
                "{exactHookScript}"
              </div>
            </div>

            {/* Thumbnail Concept */}
            <div className="bg-[#0A0A0A] p-10 flex flex-col">
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-[#FF0000] text-xl" data-icon="brush">brush</span>
                  <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#a5a2a1] block">Thumbnail Concept</label>
                </div>
                
                <div className="bg-white/5 p-8 border border-white/5 space-y-4">
                  <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#FF0000]/70 block">Visual Hook Prompt</label>
                  <p className="text-sm text-[#a5a2a1] leading-relaxed">
                    {thumbnailStrategy.split('Matte Charcoal (#0E0E0E)').map((part1, index1, array1) => (
                      <span key={index1}>
                        {part1}
                        {index1 !== array1.length - 1 && <span className="text-on-surface font-medium">Matte Charcoal (#0E0E0E)</span>}
                      </span>
                    )).map((node, index) => {
                      if (typeof node?.props?.children[0] === 'string' && node.props.children[0].includes('Laser Red')) {
                        const subParts = node.props.children[0].split('Laser Red');
                        return <span key={index}>
                          {subParts[0]}
                          <span className="text-[#FF0000] font-medium">Laser Red</span>
                          {subParts[1]}
                          {node.props.children.length > 1 && node.props.children.slice(1)}
                        </span>
                      }
                      return node;
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Title Psychology */}
          <div className="bg-white/[0.02] backdrop-blur-[20px] border border-white/5 p-10">
            <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#FF0000] mb-4 block">Title Psychology</label>
            <div className="flex flex-col md:flex-row gap-8 items-start">
              <h3 className="text-3xl font-headline font-bold text-on-surface uppercase tracking-tight">Psychological Leverage</h3>
              <p className="text-base text-[#a5a2a1] leading-relaxed max-w-2xl">
                {titlePsychologyDesc}
              </p>
            </div>
          </div>
        </section>

        {/* 3. THE EXECUTION RULES */}
        <section className="space-y-8" id="execution-rules">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-headline font-bold uppercase tracking-[0.4em] text-[#FF0000]">Execution Rules</h2>
            <div className="flex-grow h-[1px] bg-white/5"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Pacing Guide */}
            <div className="bg-white/[0.02] backdrop-blur-[20px] border border-white/5 p-8 space-y-6">
              <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#a5a2a1] block">Pacing Guide</label>
              <div className="bg-white/5 p-4 border border-white/5">
                <p className="text-xs text-on-surface leading-relaxed uppercase tracking-wide">{pacingGuide}</p>
              </div>
            </div>
            
            {/* Quality Upgrades */}
            <div className="bg-white/[0.02] backdrop-blur-[20px] border border-white/5 p-8 space-y-6">
              <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#a5a2a1] block">Quality Upgrades</label>
              <ul className="space-y-4">
                {qualityUpgradesList.length > 0 ? qualityUpgradesList.map((upgrade, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-xs uppercase tracking-wide text-[#a5a2a1]">
                    <span className="material-symbols-outlined text-[#FF0000] text-lg leading-none" data-icon="bolt">bolt</span>
                    {upgrade.endsWith('.') ? upgrade : upgrade + '.'}
                  </li>
                )) : <p className="text-xs text-on-surface/50">No upgrades flagged.</p>}
              </ul>
            </div>

            {/* Post-Publish Strategy */}
            <div className="bg-white/[0.02] backdrop-blur-[20px] border border-white/5 p-8 space-y-6">
              <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#a5a2a1] block">Post-Publish</label>
              <ul className="space-y-4">
                {postPublishList.length > 0 ? postPublishList.map((postP, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-xs uppercase tracking-wide text-[#a5a2a1]">
                    <span className="material-symbols-outlined text-[#FF0000] text-lg leading-none" data-icon="share">share</span>
                    {postP.endsWith('.') ? postP : postP + '.'}
                  </li>
                )) : <p className="text-xs text-on-surface/50">No post-publish strategy supplied.</p>}
              </ul>
            </div>
          </div>
        </section>

        {/* 4. THE MARKET MATH */}
        <section className="space-y-12" id="market-math">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-headline font-bold uppercase tracking-[0.4em] text-[#FF0000]">Market Math</h2>
            <div className="flex-grow h-[1px] bg-white/5"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            {/* Left Column: Risk and Analysis */}
            <div className="md:col-span-4 space-y-8">
              <div className="bg-white/[0.02] backdrop-blur-[20px] border border-white/5 p-8 flex flex-col items-center">
                <label className="text-[10px] font-label font-bold uppercase tracking-[0.3em] text-[#a5a2a1] mb-8">Satisfaction Risk</label>
                <div className="relative w-40 h-40 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle className="text-white/5" cx="80" cy="80" fill="transparent" r="75" stroke="currentColor" strokeWidth="4"></circle>
                    <circle className="text-[#FF0000]" cx="80" cy="80" fill="transparent" r="75" stroke="currentColor" strokeDasharray="471" strokeDashoffset={471 - (471 * (satisfactionRisk / 10))} strokeWidth="6"></circle>
                  </svg>
                  <div className="absolute flex items-baseline gap-1">
                    <span className="text-5xl font-headline font-bold">{satisfactionRisk}</span>
                    <span className="text-xl font-headline text-[#a5a2a1]">/ 10</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Content Gaps & Intelligence */}
            <div className="md:col-span-8 space-y-8">
              <div className="bg-white/5 p-10 border border-white/5">
                <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#a5a2a1] mb-6 block">Targeted Content Gaps</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {contentGapsList.length > 0 ? contentGapsList.map((gap, idx) => (
                    <div key={idx} className="flex items-center gap-4 group">
                      <span className="material-symbols-outlined text-[#FF0000]">{idx % 2 === 0 ? 'target' : 'warning'}</span>
                      <span className="text-sm text-[#a5a2a1] group-hover:text-on-surface transition-colors capitalize">{gap.trim()}</span>
                    </div>
                  )) : <p className="text-xs text-[#a5a2a1]">No targeted content gaps found.</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-white/[0.02] backdrop-blur-[20px] border border-white/5 p-6 space-y-4">
                  <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#FF0000] block">Dominant Force</label>
                  <p className="text-sm text-[#a5a2a1] leading-relaxed">
                    {dominantForce}
                  </p>
                </div>
                <div className="bg-white/[0.02] backdrop-blur-[20px] border border-white/5 p-6 space-y-4">
                  <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#FF0000] block">Channel Leverage</label>
                  <p className="text-sm text-[#a5a2a1] leading-relaxed">
                    {channelLeverage}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Shorts Warning (Conditional) */}
          {showShortsWarning && (
            <div className="p-8 bg-[#FF0000]/10 border border-[#FF0000]/30 flex flex-col md:flex-row items-center gap-8 mt-12">
              <span className="material-symbols-outlined text-[#FF0000] text-5xl" data-icon="crisis_alert" data-weight="fill" style={{fontVariationSettings: "'FILL' 1"}}>crisis_alert</span>
              <div className="space-y-1 text-center md:text-left">
                <h4 className="font-headline font-bold text-[#FF0000] uppercase tracking-tighter text-xl">Tactical Alert: Shorts Test Recommended</h4>
                <p className="text-sm text-on-surface/80">Historical data indicates high drop-off at 0:45. Run a 15-second "Hook Variant" on Shorts before the main upload to validate retention logic.</p>
              </div>
            </div>
          )}

          {/* Performance Outlook (Capstone) */}
          <div className="pt-12 border-t border-white/5 flex flex-col items-center">
            <label className="text-[10px] font-label font-bold uppercase tracking-widest text-[#a5a2a1] mb-4">Final Capstone</label>
            <div className="text-center">
              <h5 className="text-4xl md:text-6xl font-headline font-bold uppercase tracking-tighter text-[#FF0000]">Performance Outlook</h5>
              <p className="text-xl text-on-surface mt-2 font-light">{metrics}</p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-[#0A0A0A]">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex flex-col gap-1">
            <span className="text-[#FF0000] font-black tracking-tighter text-lg font-headline">STRAT-INTEL</span>
            <span className="text-[10px] font-label text-[#a5a2a1] uppercase tracking-widest">Version Alpha-01.82 | Deployment Unit 402</span>
          </div>
          <div className="flex gap-8">
             <Link className="text-[10px] font-label text-[#a5a2a1] uppercase tracking-[0.2em] hover:text-[#FF0000] transition-colors" to="/">Terminal</Link>
             <Link className="text-[10px] font-label text-[#a5a2a1] uppercase tracking-[0.2em] hover:text-[#FF0000] transition-colors" to="/analyze">Input</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ResultsDashboard;
