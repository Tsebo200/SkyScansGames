import React, { useState, useCallback, useEffect, Suspense, lazy } from 'react';
// ...existing code...
import { AISettingsProvider, useAISettings } from './context/AISettingsContext';
import { AccessibilitySettingsProvider, useAccessibilitySettings } from './context/AccessibilitySettingsContext';
import axios from 'axios';
import sfx from './utils/sfx';
import Switch from './components/Switch';
import SettingsModal from './components/SettingsModal';
import RubricModal from './components/RubricModal';
import './App.css';

// Lazy load components for better performance
const SearchBar = lazy(() => import('./components/SearchBar'));
const ScoreDashboard = lazy(() => import('./components/ScoreDashboard'));

const Toolbar = ({ inline = false }) => {
  const { aiFeedbackEnabled, setAIFeedbackEnabled } = useAISettings();
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' ? window.innerWidth < 768 : false);
  
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return (
    <div style={{ 
      display: inline ? 'inline-flex' : 'flex', 
      justifyContent: inline ? 'flex-start' : 'center', 
      marginBottom: inline ? 0 : (isMobile ? 8 : 12) 
    }}>
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: isMobile ? 8 : 16 }}>
        <div style={{ color: '#fff', background: 'rgba(255,255,255,0.12)', padding: isMobile ? '4px 8px' : '6px 10px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.2)', display: 'inline-flex', alignItems: 'center', gap: isMobile ? 8 : 10 }}>
          <Switch
            checked={aiFeedbackEnabled}
            onChange={setAIFeedbackEnabled}
            label="Show AI feedback"
            size={isMobile ? "sm" : "md"}
          />
        </div>
      </div>
    </div>
  );
};

// Select palettes adapted for common colour-vision deficiencies, with optional high-contrast boost and theme-aware mixing
const usePalette = () => {
  const { colorVision, highContrast, theme } = useAccessibilitySettings?.() || { colorVision: 'normal', highContrast: false, theme: 'dark' };
  const palettes = {
    normal: { C1: '#667eea', C2: '#764ba2', C3: '#f093fb', rubric: ['#45b7d1','#eb4d4b','#4ecdc4','#ff9f43','#f0932b','#6c5ce7','#9980FA'] },
    deuteranopia: { C1: '#6c8ae4', C2: '#7b6fc0', C3: '#f0a7ff', rubric: ['#3aa7dd','#d96b6b','#60d5c6','#f2a65a','#f0a85e','#7a6be7','#b3a0ff'] },
    protanopia: { C1: '#6a8ae8', C2: '#7a70c8', C3: '#f0a3ff', rubric: ['#3cb8d8','#b86f6f','#58d0c2','#f0a55a','#f0a05a','#7267e0','#aea0ff'] },
    tritanopia: { C1: '#6b91d9', C2: '#7b6fb7', C3: '#e6a8d7', rubric: ['#3fb2c8','#d36e6e','#58caa8','#f0a55a','#ee9b4e','#6a62d8','#a294ef'] }
  };
  const base = palettes[colorVision] || palettes.normal;
  const boost = (hex) => {
    if (!highContrast) return hex;
    try {
      const t = hex.replace('#','');
      const r = parseInt(t.slice(0,2),16), g = parseInt(t.slice(2,4),16), b = parseInt(t.slice(4,6),16);
      const mix = theme === 'light' ? 255 : 0; // toward white in light theme, toward black in dark theme
      const f = 0.15;
      const mm = (c) => Math.max(0, Math.min(255, Math.round(c + (mix - c) * f)));
      return `#${mm(r).toString(16).padStart(2,'0')}${mm(g).toString(16).padStart(2,'0')}${mm(b).toString(16).padStart(2,'0')}`;
    } catch { return hex; }
  };
  return { C1: boost(base.C1), C2: boost(base.C2), C3: boost(base.C3), rubric: base.rubric.map(boost) };
};

const AppInner = React.memo(() => {
  const [selectedGame, setSelectedGame] = useState(null);
  const [scores, setScores] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hideVariants, setHideVariants] = useState(true);
  const [openPreviewTick, setOpenPreviewTick] = useState(0);
  const [pendingOpenPreview, setPendingOpenPreview] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [rubricModalOpen, setRubricModalOpen] = useState(false);
  // Parallax state
  const [scrollY, setScrollY] = useState(0);
  const [viewportH, setViewportH] = useState(typeof window !== 'undefined' ? window.innerHeight : 0);
  const [viewportW, setViewportW] = useState(typeof window !== 'undefined' ? window.innerWidth : 0);
  const [reduceMotion, setReduceMotion] = useState(false);
  const [docH, setDocH] = useState(typeof document !== 'undefined' ? (document.documentElement?.scrollHeight || document.body?.scrollHeight || 0) : 0);
  const { reduceMotion: reduceMotionSetting, fontSize, theme } = useAccessibilitySettings?.() || { reduceMotion: false, fontSize: 'medium', theme: 'dark' };
  
  // Responsive breakpoints
  const isMobile = viewportW < 768;
  const isSmallMobile = viewportW < 480;

  // Color interpolation helpers
  const hexToRgb = useCallback((hex) => {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : { r: 0, g: 0, b: 0 };
  }, []);
  const rgbToHex = useCallback(({ r, g, b }) => {
    const toHex = (v) => v.toString(16).padStart(2, '0');
    return `#${toHex(Math.max(0, Math.min(255, Math.round(r))))}${toHex(Math.max(0, Math.min(255, Math.round(g))))}${toHex(Math.max(0, Math.min(255, Math.round(b))))}`;
  }, []);
  const lerp = useCallback((a, b, t) => a + (b - a) * t, []);
  const lerpColor = useCallback((c1, c2, t) => {
    const A = hexToRgb(c1);
    const B = hexToRgb(c2);
    return rgbToHex({ r: lerp(A.r, B.r, t), g: lerp(A.g, B.g, t), b: lerp(A.b, B.b, t) });
  }, [hexToRgb, rgbToHex, lerp]);

  // Setup reduced motion preference and listeners
  useEffect(() => {
    let mql;
    try {
      mql = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
      const onChange = () => setReduceMotion(!!mql.matches);
      if (mql) {
        setReduceMotion(!!mql.matches);
        mql.addEventListener ? mql.addEventListener('change', onChange) : mql.addListener(onChange);
      }
      const onResize = () => {
        setViewportH(window.innerHeight || 0);
        setViewportW(window.innerWidth || 0);
        setDocH(document.documentElement?.scrollHeight || document.body?.scrollHeight || 0);
      };
      window.addEventListener('resize', onResize, { passive: true });
      let raf = null;
      const onScroll = () => {
        if (raf) return;
        raf = requestAnimationFrame(() => {
          setScrollY(window.scrollY || 0);
          // Keep doc height in sync opportunistically
          setDocH(document.documentElement?.scrollHeight || document.body?.scrollHeight || 0);
          raf = null;
        });
      };
      window.addEventListener('scroll', onScroll, { passive: true });
      return () => {
        window.removeEventListener('resize', onResize);
        window.removeEventListener('scroll', onScroll);
        if (mql) {
          mql.removeEventListener ? mql.removeEventListener('change', onChange) : mql.removeListener(onChange);
        }
        if (raf) cancelAnimationFrame(raf);
      };
    } catch {
      // no-op for non-browser
    }
  }, []);

  // Compute scroll progress 0..1 and gradient colors
  const scrollProgress = (() => {
    const total = Math.max(1, docH - viewportH);
    const p = Math.max(0, Math.min(1, total > 0 ? scrollY / total : 0));
    return p;
  })();
  // Brand palette (colour-vision aware)
  const { C1, C2, C3, rubric: rubricPalette } = usePalette();
  // Ease the transition for a smoother feel
  const ease = (t) => 0.5 - 0.5 * Math.cos(Math.PI * Math.min(1, Math.max(0, t)));
  const t1 = ease(scrollProgress);
  const motionOff = reduceMotionSetting || reduceMotion;
  const leftColor = lerpColor(C1, C2, motionOff ? 0 : t1);
  const rightColor = lerpColor(C2, C3, motionOff ? 0 : t1);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const isLight = theme === 'light';
  const fontScale = fontSize === 'small' ? 0.95 : fontSize === 'large' ? 1.08 : 1.0;

  // Unlock audio on first user interaction (click anywhere on page)
  useEffect(() => {
    const unlockAudio = () => {
      try { sfx.unlock(); } catch {}
    };
    // Try to unlock on page load
    unlockAudio();
    // Also unlock on first click anywhere
    document.addEventListener('click', unlockAudio, { once: true });
    document.addEventListener('touchstart', unlockAudio, { once: true });
    return () => {
      document.removeEventListener('click', unlockAudio);
      document.removeEventListener('touchstart', unlockAudio);
    };
  }, []);

  // If user clicked the bubble before scores finished loading, open preview once ready
  useEffect(() => {
    if (selectedGame && pendingOpenPreview && scores) {
      setOpenPreviewTick(t => t + 1);
      setPendingOpenPreview(false);
    }
  }, [selectedGame, pendingOpenPreview, scores]);

  const handleGameSelect = useCallback(async (game) => {
    setSelectedGame(game);
    setLoading(true);
    try { sfx.unlock(); sfx.scanStart(); } catch {}
    try {
      const apiBase = process.env.REACT_APP_API_BASE || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api');
      const response = await axios.post(`${apiBase}/games/${game.id}/scan`);
      setScores(response.data.scores);
      
      // Fetch updated game object with release_year and release_date from database
      // Merge with existing game object to preserve all fields (like cover_image, title, etc.)
      try {
        const gameResponse = await axios.get(`${apiBase}/games/${game.id}`);
        if (gameResponse.data) {
          // Merge updated fields with existing game object to preserve all data
          setSelectedGame(prevGame => ({
            ...prevGame,
            ...gameResponse.data,
            // Preserve important fields that might be missing in API response
            cover_image: gameResponse.data.cover_image || prevGame?.cover_image,
            title: gameResponse.data.title || prevGame?.title,
            platforms: gameResponse.data.platforms || prevGame?.platforms,
            rawg_id: gameResponse.data.rawg_id || prevGame?.rawg_id
          }));
        }
      } catch (gameError) {
        console.warn('Could not fetch updated game object:', gameError);
        // Continue with original game object if fetch fails
      }
      
      try { sfx.scanDone(); sfx.scoreReveal(); } catch {}
    } catch (error) {
      console.error('Scan error:', error);
    }
    setLoading(false);
  }, []);

  return (
    <div className="App" style={{
      minHeight: '100vh',
      background: `linear-gradient(135deg, ${leftColor} 0%, ${rightColor} 100%)`,
      color: isLight ? '#0f172a' : '#fff',
      padding: isMobile ? (isSmallMobile ? '8px' : '10px') : '20px',
      position: 'relative',
      overflow: 'hidden',
      fontSize: `${fontScale}rem`,
      width: '100%',
      boxSizing: 'border-box'
    }} data-theme={isLight ? 'light' : 'dark'}>
      {/* Sky Logo - Top Left */}
      <div style={{ position: 'fixed', top: isMobile ? 8 : 12, left: isMobile ? 8 : 12, zIndex: 50 }}>
        <img 
          src="/SkyLogo.png" 
          alt="SkyScansGames Logo" 
          style={{
            width: '70px',
            height: '70px',
            borderRadius: '360px',
            objectFit: 'cover',
            border: isLight ? '2px solid rgba(0,0,0,0.1)' : '2px solid rgba(255,255,255,0.2)',
            boxShadow: isLight ? '0 2px 8px rgba(0,0,0,0.1)' : '0 2px 8px rgba(0,0,0,0.3)',
            background: isLight ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.1)',
            backdropFilter: 'blur(4px)'
          }}
        />
      </div>

      {/* Settings shortcut */}
      <div style={{ position: 'fixed', top: isMobile ? 8 : 12, right: isMobile ? 8 : 12, zIndex: 50 }}>
        <button onClick={() => setSettingsOpen(true)} aria-label="Open settings" style={{ 
          background: isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)', 
          border: isLight ? '1px solid rgba(0,0,0,0.2)' : '1px solid rgba(255,255,255,0.35)', 
          color: isLight ? '#0f172a' : '#fff', 
          padding: isMobile ? '6px 10px' : '8px 12px', 
          borderRadius: 10, 
          cursor: 'pointer', 
          backdropFilter: 'blur(4px)', 
          fontSize: isMobile ? '14px' : '16px',
          fontWeight: 500,
          textShadow: isLight ? 'none' : '0 1px 2px rgba(0,0,0,0.3)'
        }}>
          Settings
        </button>
      </div>

      {/* Reduced number of floating orbs and optimized animations */}
      <div style={{
        position: 'absolute',
  top: `${Math.round((viewportH * 0.10) + (motionOff ? 0 : scrollY * 0.15))}px`,
        left: isMobile ? '5%' : '10%',
        width: isMobile ? (isSmallMobile ? '80px' : '100px') : '150px',
        height: isMobile ? (isSmallMobile ? '80px' : '100px') : '150px',
        background: 'rgba(255, 255, 255, 0.08)',
        borderRadius: '50%',
        border: '1px solid rgba(255, 255, 255, 0.15)',
  animation: motionOff ? 'none' : 'float 8s ease-in-out infinite',
        cursor: selectedGame ? 'pointer' : 'default',
        zIndex: 20,
        visibility: isPreviewOpen ? 'hidden' : 'visible'
      }}
      onClick={() => {
        if (!selectedGame) return;
        if (scores) {
          setOpenPreviewTick(t => t + 1);
        } else {
          setPendingOpenPreview(true);
        }
      }}
      onKeyDown={(e) => {
        if (!selectedGame) return;
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (scores) {
            setOpenPreviewTick(t => t + 1);
          } else {
            setPendingOpenPreview(true);
          }
        }
      }}
      title={selectedGame ? 'View game details' : undefined}
      aria-label={selectedGame ? 'Open game details' : undefined}
      role={selectedGame ? 'button' : undefined}
      tabIndex={selectedGame ? 0 : -1}
      >
        {selectedGame?.cover_image && (
          <img
            src={selectedGame.cover_image}
            alt={`${selectedGame.title} cover`}
            style={{
              width: isMobile ? (isSmallMobile ? 32 : 40) : 56,
              height: isMobile ? (isSmallMobile ? 32 : 40) : 56,
              borderRadius: 10,
              objectFit: 'cover',
              border: '1px solid rgba(255, 255, 255, 0.5)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              pointerEvents: 'none'
            }}
          />
        )}
      </div>
      <div style={{
        position: 'absolute',
  bottom: `${Math.round((viewportH * 0.20) - (motionOff ? 0 : scrollY * 0.10))}px`,
        left: isMobile ? '75%' : '70%',
        width: isMobile ? (isSmallMobile ? '60px' : '80px') : '120px',
        height: isMobile ? (isSmallMobile ? '60px' : '80px') : '120px',
        background: 'rgba(255, 255, 255, 0.06)',
        borderRadius: '50%',
        border: '1px solid rgba(255, 255, 255, 0.12)',
  animation: motionOff ? 'none' : 'float 12s ease-in-out infinite reverse',
        pointerEvents: 'none'
      }}>
        {selectedGame?.cover_image && (
          <img
            src={selectedGame.cover_image}
            alt={`${selectedGame.title} cover`}
            style={{
              width: isMobile ? (isSmallMobile ? 24 : 32) : 44,
              height: isMobile ? (isSmallMobile ? 24 : 32) : 44,
              borderRadius: 8,
              objectFit: 'cover',
              border: '1px solid rgba(255, 255, 255, 0.5)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              pointerEvents: 'none'
            }}
          />
        )}
      </div>

      <div style={{
        position: 'relative',
        zIndex: 10,
        maxWidth: '1200px',
        margin: '0 auto',
        padding: isMobile ? (isSmallMobile ? '0 8px' : '0 12px') : '0',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        <h1 style={{
          color: isLight ? '#0f172a' : '#fff',
          textAlign: 'center',
          marginBottom: isMobile ? '20px' : '30px',
          fontSize: isMobile ? (isSmallMobile ? '1.5rem' : '2rem') : '3rem',
          fontWeight: '300',
          textShadow: isLight ? 'none' : '0 0 20px rgba(255, 255, 255, 0.5)',
          background: isLight ? 'rgba(255,255,255,0.6)' : 'rgba(255, 255, 255, 0.1)',
          padding: isMobile ? (isSmallMobile ? '12px 8px' : '15px 12px') : '20px',
          borderRadius: '20px',
          border: isLight ? '1px solid rgba(0,0,0,0.08)' : '1px solid rgba(255, 255, 255, 0.2)',
          display: 'inline-block',
          width: isMobile ? '100%' : 'auto',
          maxWidth: '100%',
          boxSizing: 'border-box'
        }}>
          SkyScansGames
        </h1>

        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexWrap: isMobile ? 'wrap' : 'nowrap',
          gap: isMobile ? '12px' : '75px',
          marginBottom: '16px',
          width: '100%',
          boxSizing: 'border-box'
        }}>
          <Suspense fallback={
            <div style={{
              color: '#fff',
              fontSize: '1.2rem',
              padding: '20px',
              textAlign: 'center'
            }}>
              Loading search component...
            </div>
          }>
            <SearchBar onGameSelect={handleGameSelect} hideVariants={hideVariants} onChangeHideVariants={setHideVariants} />
          </Suspense>
          {!isMobile && <Toolbar inline={true} />}
        </div>

        {/* AI feedback toggle for mobile - shown below search bar */}
        {isMobile && <Toolbar inline={false} />}

        {/* Rubric button - shown below search bar */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: isMobile ? '12px' : '16px', marginBottom: '16px' }}>
          <button 
            onClick={() => setRubricModalOpen(true)} 
            aria-label="View scoring rubric"
            style={{
              background: isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.15)',
              border: isLight ? '1px solid rgba(0,0,0,0.2)' : '1px solid rgba(255,255,255,0.3)',
              color: isLight ? '#0f172a' : '#fff',
              padding: isMobile ? '8px 14px' : '10px 18px',
              borderRadius: 12,
              cursor: 'pointer',
              backdropFilter: 'blur(4px)',
              fontSize: isMobile ? '14px' : '15px',
              fontWeight: 500,
              textShadow: isLight ? 'none' : '0 1px 2px rgba(0,0,0,0.3)',
              transition: 'all 0.2s ease',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.25)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.15)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <span>📊</span>
            <span>View Scoring Rubric</span>
          </button>
        </div>

        {loading && (
          <div style={{
            textAlign: 'center',
            color: '#fff',
            background: 'rgba(255, 255, 255, 0.1)',
            padding: '20px',
            borderRadius: '15px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            display: 'inline-block'
          }}>
            Scanning game quality...
          </div>
        )}

        {selectedGame && scores && (
          <Suspense fallback={
            <div style={{
              textAlign: 'center',
              color: '#fff',
              fontSize: '1.2rem',
              padding: '40px'
            }}>
              Loading analysis dashboard...
            </div>
          }>
            <ScoreDashboard scores={scores} game={selectedGame} externalOpenPreview={openPreviewTick} onPreviewOpenChange={setIsPreviewOpen} rubricPalette={rubricPalette} />
          </Suspense>
        )}

        {/* If user clicked bubble before scores loaded, open preview as soon as scores are ready */}
        {/* queued preview opening handled via useEffect above */}

        {/* Copyright notice */}
        <div style={{
          textAlign: 'center',
          padding: isMobile ? '20px 10px' : '30px 20px',
          marginTop: isMobile ? '30px' : '50px',
          color: isLight ? 'rgba(15, 23, 42, 0.7)' : 'rgba(255, 255, 255, 0.7)',
          fontSize: isMobile ? '0.85rem' : '0.9rem',
          fontFamily: 'inherit'
        }}>
          Copyright 2025 © SkyScansGames | Creative T
        </div>
      </div>
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <RubricModal open={rubricModalOpen} onClose={() => setRubricModalOpen(false)} rubricPalette={rubricPalette} />
    </div>
  );
});

const App = () => (
  <AISettingsProvider>
    <AccessibilitySettingsProvider>
      <AppInner />
    </AccessibilitySettingsProvider>
  </AISettingsProvider>
);

export default App;
