import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAccessibilitySettings } from '../context/AccessibilitySettingsContext';

const SettingsModal = ({ open, onClose }) => {
  const { colorVision, setColorVision, reduceMotion, setReduceMotion, highContrast, setHighContrast, fontSize, setFontSize, theme, setTheme } = useAccessibilitySettings();

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return createPortal(
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 'min(720px, 95vw)', background: 'rgba(255,255,255,0.98)', borderRadius: 16, border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 12px 36px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', padding: 14, borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#111827', flex: 1 }}>Settings</h3>
          <button onClick={onClose} aria-label="Close settings" style={{ border: 'none', background: 'transparent', fontSize: '1.5rem', cursor: 'pointer', color: '#6b7280' }}>×</button>
        </div>
        <div style={{ padding: 16, display: 'grid', gap: 16 }}>
          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a' }}>Accessibility</h4>
            <label htmlFor="colorVision" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>Color vision mode</label>
            <select id="colorVision" value={colorVision} onChange={(e) => setColorVision(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a' }}>
              <option value="normal">Normal</option>
              <option value="deuteranopia">Deuteranopia (green-weak)</option>
              <option value="protanopia">Protanopia (red-weak)</option>
              <option value="tritanopia">Tritanopia (blue-weak)</option>
            </select>
            <p style={{ margin: '8px 0 0 0', color: '#475569', fontSize: '0.9rem' }}>We’ll adapt UI colours and contrasts to improve distinguishability for common colour-vision deficiencies.</p>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a' }}>Motion & Contrast</h4>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="checkbox" checked={reduceMotion} onChange={(e) => setReduceMotion(e.target.checked)} />
              <span>Reduce motion/animations</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
              <input type="checkbox" checked={highContrast} onChange={(e) => setHighContrast(e.target.checked)} />
              <span>High contrast mode</span>
            </label>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a' }}>Typography</h4>
            <label htmlFor="fontSize" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>Font size</label>
            <select id="fontSize" value={fontSize} onChange={(e) => setFontSize(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a' }}>
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a' }}>Theme</h4>
            <label htmlFor="theme" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>Appearance</label>
            <select id="theme" value={theme} onChange={(e) => setTheme(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a' }}>
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </section>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default SettingsModal;
