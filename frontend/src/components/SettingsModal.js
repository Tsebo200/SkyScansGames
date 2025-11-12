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
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 'min(720px, 95vw)', background: '#ffffff', borderRadius: 16, border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 12px 36px rgba(0,0,0,0.3)', overflow: 'hidden', color: '#0f172a' }}>
        <div style={{ display: 'flex', alignItems: 'center', padding: 14, borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#111827', flex: 1, fontFamily: 'inherit' }}>Settings</h3>
          <button onClick={onClose} aria-label="Close settings" style={{ border: 'none', background: 'transparent', fontSize: '1.5rem', cursor: 'pointer', color: '#6b7280', fontFamily: 'inherit' }}>×</button>
        </div>
        <div style={{ padding: 16, display: 'grid', gap: 16, color: '#0f172a', fontFamily: 'inherit' }}>
          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, color: '#0f172a' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600, fontSize: '16px', fontFamily: 'inherit' }}>Accessibility</h4>
            <label htmlFor="colorVision" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6, fontSize: '14px', fontFamily: 'inherit' }}>Color vision mode</label>
            <select id="colorVision" value={colorVision} onChange={(e) => setColorVision(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a', width: '100%', fontSize: '14px', fontFamily: 'inherit' }}>
              <option value="normal" style={{ color: '#0f172a', background: '#fff' }}>Normal</option>
              <option value="deuteranopia" style={{ color: '#0f172a', background: '#fff' }}>Deuteranopia (green-weak)</option>
              <option value="protanopia" style={{ color: '#0f172a', background: '#fff' }}>Protanopia (red-weak)</option>
              <option value="tritanopia" style={{ color: '#0f172a', background: '#fff' }}>Tritanopia (blue-weak)</option>
            </select>
            <p style={{ margin: '8px 0 0 0', color: '#475569', fontSize: '0.9rem', fontFamily: 'inherit' }}>We'll adapt UI colours and contrasts to improve distinguishability for common colour-vision deficiencies.</p>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, color: '#0f172a' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600, fontSize: '16px', fontFamily: 'inherit' }}>Motion & Contrast</h4>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontFamily: 'inherit' }}>
              <input type="checkbox" checked={reduceMotion} onChange={(e) => setReduceMotion(e.target.checked)} style={{ cursor: 'pointer', width: '18px', height: '18px' }} />
              <span style={{ color: '#0f172a', fontWeight: 500, fontSize: '14px', fontFamily: 'inherit' }}>Reduce motion/animations</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8, cursor: 'pointer', fontFamily: 'inherit' }}>
              <input type="checkbox" checked={highContrast} onChange={(e) => setHighContrast(e.target.checked)} style={{ cursor: 'pointer', width: '18px', height: '18px' }} />
              <span style={{ color: '#0f172a', fontWeight: 500, fontSize: '14px', fontFamily: 'inherit' }}>High contrast mode</span>
            </label>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, color: '#0f172a' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600, fontSize: '16px', fontFamily: 'inherit' }}>Typography</h4>
            <label htmlFor="fontSize" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6, fontSize: '14px', fontFamily: 'inherit' }}>Font size</label>
            <select id="fontSize" value={fontSize} onChange={(e) => setFontSize(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a', width: '100%', fontSize: '14px', fontFamily: 'inherit' }}>
              <option value="small" style={{ color: '#0f172a', background: '#fff' }}>Small</option>
              <option value="medium" style={{ color: '#0f172a', background: '#fff' }}>Medium</option>
              <option value="large" style={{ color: '#0f172a', background: '#fff' }}>Large</option>
            </select>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, color: '#0f172a' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600, fontSize: '16px', fontFamily: 'inherit' }}>Theme</h4>
            <label htmlFor="theme" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6, fontSize: '14px', fontFamily: 'inherit' }}>Appearance</label>
            <select id="theme" value={theme} onChange={(e) => setTheme(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a', width: '100%', fontSize: '14px', fontFamily: 'inherit' }}>
              <option value="dark" style={{ color: '#0f172a', background: '#fff' }}>Dark</option>
              <option value="light" style={{ color: '#0f172a', background: '#fff' }}>Light</option>
            </select>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, color: '#0f172a' }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#0f172a', fontWeight: 600, fontSize: '16px', fontFamily: 'inherit' }}>Contact Developer</h4>
            <div style={{ display: 'grid', gap: 10, fontSize: '14px', fontFamily: 'inherit' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600, color: '#0f172a', minWidth: '60px' }}>Email:</span>
                <a href="mailto:tsebo.ramonyalioa.an@gmail.com" style={{ color: '#0ea5e9', textDecoration: 'none' }} onMouseEnter={(e) => e.target.style.textDecoration = 'underline'} onMouseLeave={(e) => e.target.style.textDecoration = 'none'}>
                  tsebo.ramonyalioa.an@gmail.com
                </a>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600, color: '#0f172a', minWidth: '60px' }}>Phone:</span>
                <a href="tel:+27829000488" style={{ color: '#0ea5e9', textDecoration: 'none' }} onMouseEnter={(e) => e.target.style.textDecoration = 'underline'} onMouseLeave={(e) => e.target.style.textDecoration = 'none'}>
                  (+27) 82 900 0488
                </a>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600, color: '#0f172a', minWidth: '60px' }}>GitHub:</span>
                <a href="https://github.com/Tsebo200" target="_blank" rel="noopener noreferrer" style={{ color: '#0ea5e9', textDecoration: 'none' }} onMouseEnter={(e) => e.target.style.textDecoration = 'underline'} onMouseLeave={(e) => e.target.style.textDecoration = 'none'}>
                  github.com/Tsebo200
                </a>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600, color: '#0f172a', minWidth: '60px' }}>LinkedIn:</span>
                <a href="https://www.linkedin.com/in/tsebo-ramonyalioa-2392381b4" target="_blank" rel="noopener noreferrer" style={{ color: '#0ea5e9', textDecoration: 'none' }} onMouseEnter={(e) => e.target.style.textDecoration = 'underline'} onMouseLeave={(e) => e.target.style.textDecoration = 'none'}>
                  linkedin.com/in/tsebo-ramonyalioa-2392381b4
                </a>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default SettingsModal;
