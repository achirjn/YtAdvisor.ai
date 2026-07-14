import React, { useEffect, useRef } from 'react';
import Navbar from './Navbar';

const LoginPage = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let dots = [];
    const spacing = 32;
    const mouse = { x: -1000, y: -1000 };
    let animationFrameId;

    const init = () => {
      canvas.width = window.innerWidth * window.devicePixelRatio;
      canvas.height = window.innerHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      
      dots = [];
      for (let x = spacing / 2; x < window.innerWidth; x += spacing) {
          for (let y = spacing / 2; y < window.innerHeight; y += spacing) {
              dots.push({ x, y, baseRadius: 1 });
          }
      }
    };

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      dots.forEach(dot => {
          const dx = mouse.x - dot.x;
          const dy = mouse.y - dot.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDist = 180;
          
          let ratio = 0;
          if (dist < maxDist) {
              ratio = (maxDist - dist) / maxDist;
          }

          const radius = dot.baseRadius + (ratio * 2);
          const opacity = 0.08 + (ratio * 0.4);
          
          // Transition to #FF0000 accents on hover
          const r = Math.floor(53 + (255 - 53) * ratio);
          const g = Math.floor(53 + (0 - 53) * ratio);
          const b = Math.floor(52 + (0 - 52) * ratio);

          ctx.beginPath();
          ctx.arc(dot.x, dot.y, radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${opacity})`;
          ctx.fill();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    window.addEventListener('resize', init);
    window.addEventListener('mousemove', handleMouseMove);
    
    init();
    animate();

    return () => {
      window.removeEventListener('resize', init);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  const handleLogin = () => {
    const baseUrl = import.meta.env.BACKEND_BASE_URL || '';
    window.location.href = `${baseUrl}/oauth2/authorization/google`;
  };

  return (
    <div className="text-[#e5e2e1] flex flex-col min-h-screen selection:bg-[#ff5540] selection:text-[#5c0000] bg-[#0A0A0A] font-body relative overflow-hidden">
      <style dangerouslySetInnerHTML={{__html: `
        .glow-effect {
            background: radial-gradient(circle at center, rgba(151, 1, 0, 0.15) 0%, rgba(10, 10, 10, 0) 70%);
        }
        .spectral-glow {
            background: radial-gradient(circle at 50% 50%, rgba(255, 0, 0, 0.05) 0%, transparent 70%);
        }
      `}} />

      <Navbar />

      {/* Tactical Background Architecture */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-50"></canvas>
        <div className="absolute inset-0 spectral-glow"></div>
      </div>

      {/* Login Container */}
      <main className="flex-grow flex items-center justify-center relative overflow-hidden px-4 pt-40 pb-20 z-10 w-full">
        {/* Ambient Glow Background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] glow-effect pointer-events-none"></div>
        
        <div className="z-10 w-full max-w-lg">
          {/* Strategic Header */}
          <div className="text-center mb-10">
            <span className="inline-block font-label text-[0.6875rem] uppercase tracking-[0.2em] text-[#ffb4a8] mb-4 opacity-80">Terminal ID: K-092 — V.4.0.2</span>
            <h1 className="font-headline text-5xl md:text-7xl font-black tracking-tighter text-[#e5e2e1] mb-2 leading-none uppercase">LOG_IN</h1>
            <p className="font-body text-[#e5e2e1]/50 text-sm tracking-widest uppercase">Operative Authentication Required</p>
          </div>

          {/* Main Login Card (Elite Stealth Tech Styling) */}
          <div className="bg-[rgba(28,27,27,0.4)] backdrop-blur-[12px] border border-white/5 p-8 md:p-12 relative group transition-all duration-500 hover:border-white/10 shadow-2xl">
            {/* Inner Tonal Depth */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#1c1b1b]/50 to-transparent pointer-events-none"></div>
            
            <div className="relative z-10 space-y-8">
              <div className="space-y-4">
                <p className="font-label text-[0.625rem] uppercase tracking-widest text-[#e5e2e1]/40 text-center">Identity Verification Required</p>
                {/* Primary OAuth Action */}
                <button 
                  onClick={handleLogin}
                  className="w-full flex items-center justify-center gap-4 py-4 px-6 bg-[#970100] hover:bg-[#b50100] text-white font-headline font-bold transition-all duration-300 group/btn active:scale-95 border-b-2 border-black/20"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#FFFFFF"></path>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#FFFFFF"></path>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FFFFFF"></path>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#FFFFFF"></path>
                  </svg>
                  <span className="tracking-tight uppercase">Continue with Google</span>
                  <div className="absolute right-6 opacity-0 group-hover/btn:opacity-100 transition-opacity">
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </div>
                </button>
              </div>
              
              {/* Status Metadata */}
              <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/5">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]"></span>
                  <span className="font-label text-[0.6rem] uppercase tracking-tighter text-[#e5e2e1]/40">Encryption: Active</span>
                </div>
                <div className="flex items-center gap-2 justify-end">
                  <span className="material-symbols-outlined text-[0.8rem] text-[#e5e2e1]/40">verified_user</span>
                  <span className="font-label text-[0.6rem] uppercase tracking-tighter text-[#e5e2e1]/40">Secured: OAUTH 2.0</span>
                </div>
              </div>
            </div>

            {/* Corner Accents */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#ffb4a8]/30"></div>
            <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-[#ffb4a8]/30"></div>
            <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-[#ffb4a8]/30"></div>
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#ffb4a8]/30"></div>
          </div>

          {/* Signup Redirect */}
          <div className="mt-8 text-center">
            <p className="font-body text-xs text-[#e5e2e1]/40 uppercase tracking-widest">
                New Operative? 
                <a className="text-[#ffb4a8] hover:text-[#e5e2e1] transition-colors duration-300 font-bold ml-2 underline underline-offset-4" href="#">Initialize Enrollment</a>
            </p>
          </div>
        </div>
      </main>

      {/* Strategic Footer */}
      <footer className="w-full border-t border-white/5 relative bg-transparent z-10">
        <div className="w-full py-12 px-8 flex flex-col md:flex-row justify-between items-center gap-6 max-w-7xl mx-auto">
          <div className="flex flex-col items-center md:items-start gap-1">
            <span className="text-lg font-black text-[#E5E2E1] font-headline tracking-tighter uppercase">Kinetic Instrument</span>
            <p className="text-[0.6875rem] font-headline uppercase text-[#e5e2e1]/40 tracking-wider">© 2024 STRATEGY ENGINE. KINETIC INSTRUMENT STATUS: ACTIVE.</p>
          </div>
          <nav className="flex gap-8">
            <a className="text-[0.6875rem] font-headline uppercase tracking-widest text-[#E5E2E1]/40 hover:text-[#FF0000] transition-colors" href="#">Security</a>
            <a className="text-[0.6875rem] font-headline uppercase tracking-widest text-[#E5E2E1]/40 hover:text-[#FF0000] transition-colors" href="#">Terms</a>
            <a className="text-[0.6875rem] font-headline uppercase tracking-widest text-[#E5E2E1]/40 hover:text-[#FF0000] transition-colors" href="#">Privacy</a>
            <a className="text-[0.6875rem] font-headline uppercase tracking-widest text-[#E5E2E1]/40 hover:text-[#FF0000] transition-colors" href="#">Support</a>
          </nav>
        </div>
      </footer>
    </div>
  );
};

export default LoginPage;
