import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from './Navbar';

const InputPage = () => {
  const [formData, setFormData] = useState({
    videoIdea: ''
  });

  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const payload = {
        video_idea: formData.videoIdea
      };

      const baseUrl = import.meta.env.BACKEND_BASE_URL || '';
      const response = await fetch(`${baseUrl}/api/analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      
      // Cache the analysis response instantly to endure browser page reloads!
      localStorage.setItem('dimenziq_analysis', JSON.stringify(data));
      setSuccess(true);
      
      // Navigate to the results dashboard generically
      navigate('/results');
    } catch (err) {
      console.error('Failed to submit analysis:', err);
      setError(err.message || 'Failed to connect to the analysis engine.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#0A0A0A] text-[#e5e2e1] font-body min-h-screen selection:bg-spectre-red/30 selection:text-on-primary flex flex-col">
      <Navbar />

      <main className="flex-grow flex flex-col items-center justify-center pt-[100px] pb-20 px-4 relative overflow-hidden">
        {/* Background Decor */}
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_50%,rgba(255,0,0,0.02)_50%)] bg-[length:100%_4px] pointer-events-none opacity-[0.3]"></div>
        <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-spectre-red/5 blur-[120px] rounded-full pointer-events-none"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[30%] h-[30%] bg-secondary-container/5 blur-[100px] rounded-full pointer-events-none"></div>
        
        <div className="w-full max-w-[800px] space-y-12 relative z-10">
          {/* Header */}
          <div className="text-center space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="font-headline text-5xl md:text-6xl font-bold tracking-tighter uppercase text-on-surface">
                Analysis <span className="text-spectre-red">Input</span>
              </h1>
              <p className="font-body text-on-surface/40 text-xs tracking-[0.5em] uppercase mt-4">Initialize Market Penetration Scan</p>
            </motion.div>
          </div>

          {/* Form Section */}
          <motion.form 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            onSubmit={handleSubmit} 
            className="space-y-5"
          >
            {/* Primary Input: Video Idea */}
            <div className="space-y-6">
              <label className="block font-headline text-xs font-bold uppercase tracking-[0.3em] text-spectre-red/70 ml-1">Video Objective / Hypothesis</label>
              <div className="bg-white/[0.03] backdrop-blur-[12px] border border-white/10 relative corner-accent group transition-all duration-300 focus-within:border-spectre-red/50 focus-within:bg-white/[0.05]">
                <textarea 
                  className="w-full bg-transparent border-none text-on-surface p-8 text-2xl font-light placeholder:text-on-surface/10 focus:ring-0 transition-all resize-none font-headline leading-relaxed min-h-[200px]" 
                  name="videoIdea" 
                  placeholder="Paste your video idea, title hypothesis, or script outline..." 
                  value={formData.videoIdea}
                  onChange={handleChange}
                  required
                ></textarea>
                <div className="absolute bottom-0 left-0 h-[1px] bg-spectre-red w-0 group-focus-within:w-full transition-all duration-700 ease-out"></div>
              </div>
            </div>

            {/* Submit Action */}
            <div className="flex flex-col items-center pt-2">
              {error && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mb-2 px-6 py-3 border border-red-500/50 bg-red-500/10 text-red-500 font-label text-[10px] rounded-sm tracking-widest uppercase"
                >
                  [SYSTEM_ERROR] {error}
                </motion.div>
              )}
              
              {success && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mb-2 px-6 py-3 border border-green-500/50 bg-green-500/10 text-green-500 font-label text-[10px] rounded-sm tracking-widest uppercase"
                >
                  [LINK_ESTABLISHED] Processing payload
                </motion.div>
              )}
              
              <button 
                disabled={isLoading}
                className="group relative w-full md:w-auto md:min-w-[180px] bg-[#BDBDBD] text-black py-2.5 px-6 rounded-sm font-headline font-black text-xs uppercase tracking-[0.3em] transition-all active:scale-[0.98] flex items-center justify-center disabled:opacity-50 hover:bg-white hover:shadow-[0_0_40px_rgba(255,0,0,0.3)] hover:text-[#970100]" 
                type="submit"
              >
                {isLoading ? (
                  <span className="flex items-center gap-3">
                    <span className="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin"></span>
                    Processing
                  </span>
                ) : (
                  <span>Execute Analysis</span>
                )}
              </button>
            </div>
          </motion.form>

          <style dangerouslySetInnerHTML={{__html: `
            .corner-accent::before, .corner-accent::after {
              content: '';
              position: absolute;
              width: 8px;
              height: 8px;
              border-color: rgba(255, 255, 255, 0.4);
              pointer-events: none;
            }
            .corner-accent::before {
              top: 0;
              left: 0;
              border-top: 2px solid;
              border-left: 2px solid;
            }
            .corner-accent::after {
              bottom: 0;
              right: 0;
              border-bottom: 2px solid;
              border-right: 2px solid;
            }
          `}} />
        </div>
      </main>

      <footer className="w-full py-6 md:py-8 px-4 md:px-6 flex flex-col md:flex-row justify-between items-center gap-4 border-t border-[#1C1B1B] bg-[#0E0E0E] dark:bg-[#0E0E0E] z-20">
        <div className="font-['Space_Grotesk'] font-bold text-[#FF0000] dark:text-[#FF0000] uppercase tracking-widest text-lg">
          DimenzIq
        </div>
        <div className="flex flex-wrap justify-center gap-6 font-['Inter'] text-[10px] uppercase tracking-widest text-zinc-500">
          <a className="text-zinc-600 hover:text-zinc-400 transition-colors" href="#">Security</a>
          <a className="text-zinc-600 hover:text-zinc-400 transition-colors" href="#">API</a>
          <a className="text-zinc-600 hover:text-zinc-400 transition-colors" href="#">Terms</a>
          <a className="text-zinc-600 hover:text-zinc-400 transition-colors" href="#">Privacy</a>
        </div>
        <div className="font-['Inter'] text-[10px] uppercase tracking-widest text-zinc-500 text-center md:text-right">
          © {new Date().getFullYear()} DimenzIq. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default InputPage;
