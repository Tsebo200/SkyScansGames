import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAccessibilitySettings } from '../context/AccessibilitySettingsContext';

const RubricModal = ({ open, onClose, rubricPalette }) => {
  const { theme } = useAccessibilitySettings?.() || { theme: 'dark' };
  const isLight = theme === 'light';

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const rc = Array.isArray(rubricPalette) && rubricPalette.length >= 7 ? rubricPalette : ['#45b7d1','#eb4d4b','#4ecdc4','#ff9f43','#f0932b','#6c5ce7','#9980FA'];
  
  const rubricItems = [
    { 
      label: 'Core Gameplay', 
      color: rc[0], 
      description: 'Evaluates the fundamental mechanics, controls, responsiveness, and overall gameplay experience. Considers how engaging and polished the core interactions are.',
      weight: '25%'
    },
    { 
      label: 'Story & Immersion', 
      color: rc[1], 
      description: 'Assesses narrative quality, character development, world-building, and how well the game immerses players in its universe.',
      weight: '20%'
    },
    { 
      label: 'Presentation', 
      color: rc[2], 
      description: 'Evaluates visual design, art style, audio quality, UI/UX, and overall aesthetic appeal of the game.',
      weight: '15%'
    },
    { 
      label: 'Technical Performance', 
      color: rc[3], 
      description: 'Measures frame rate stability, optimization, bug frequency, load times, and overall technical polish.',
      weight: '15%'
    },
    { 
      label: 'Completeness', 
      color: rc[4], 
      description: 'Assesses content volume, feature completeness, post-launch support, and whether the game feels finished.',
      weight: '10%'
    },
    { 
      label: 'Innovation & Creativity', 
      color: rc[5], 
      description: 'Evaluates unique mechanics, creative design choices, originality, and how the game pushes boundaries.',
      weight: '10%'
    },
    { 
      label: 'Community & Longevity', 
      color: rc[6], 
      description: 'Considers active player base, online community health, ongoing support, and long-term engagement potential.',
      weight: '5%'
    }
  ];

  if (!open) return null;
  return createPortal(
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 'min(800px, 95vw)', maxHeight: '90vh', background: isLight ? '#ffffff' : '#1e293b', borderRadius: 16, border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.1)'}`, boxShadow: '0 12px 36px rgba(0,0,0,0.3)', overflow: 'hidden', color: isLight ? '#0f172a' : '#fff', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', padding: 14, borderBottom: `1px solid ${isLight ? '#e5e7eb' : 'rgba(255,255,255,0.1)'}`, flexShrink: 0 }}>
          <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: isLight ? '#111827' : '#fff', flex: 1, fontFamily: 'inherit' }}>Scoring Rubric</h3>
          <button onClick={onClose} aria-label="Close rubric" style={{ border: 'none', background: 'transparent', fontSize: '1.5rem', cursor: 'pointer', color: isLight ? '#6b7280' : '#cbd5e1', fontFamily: 'inherit' }}>×</button>
        </div>
        <div style={{ padding: 20, overflowY: 'auto', flex: 1 }}>
          <p style={{ margin: '0 0 20px 0', color: isLight ? '#475569' : '#cbd5e1', fontSize: '0.95rem', fontFamily: 'inherit', lineHeight: 1.6 }}>
            Games are evaluated across seven key dimensions. Each metric contributes to the overall quality score with the weights shown below.
          </p>
          <div style={{ display: 'grid', gap: 16 }}>
            {rubricItems.map((item, index) => (
              <div key={index} style={{ 
                background: isLight ? '#f8fafc' : 'rgba(255,255,255,0.05)', 
                border: `1px solid ${isLight ? '#e5e7eb' : 'rgba(255,255,255,0.1)'}`, 
                borderRadius: 12, 
                padding: 16,
                display: 'flex',
                gap: 12,
                alignItems: 'flex-start'
              }}>
                <div style={{ 
                  width: 40, 
                  height: 40, 
                  borderRadius: 8, 
                  background: item.color, 
                  flexShrink: 0,
                  boxShadow: `0 2px 8px ${item.color}55`
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <h4 style={{ margin: 0, color: isLight ? '#0f172a' : '#fff', fontWeight: 600, fontSize: '16px', fontFamily: 'inherit' }}>{item.label}</h4>
                    <span style={{ 
                      padding: '2px 8px', 
                      borderRadius: 6, 
                      background: isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.1)', 
                      color: isLight ? '#475569' : '#cbd5e1', 
                      fontSize: '0.75rem', 
                      fontWeight: 600,
                      fontFamily: 'inherit'
                    }}>
                      {item.weight}
                    </span>
                  </div>
                  <p style={{ margin: 0, color: isLight ? '#64748b' : '#94a3b8', fontSize: '0.9rem', fontFamily: 'inherit', lineHeight: 1.5 }}>
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default RubricModal;


