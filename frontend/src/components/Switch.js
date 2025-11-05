import React, { useCallback } from 'react';

// Reusable iOS-style switch
// Props: checked: boolean, onChange: (newVal:boolean) => void, disabled?: boolean, label?: string, size?: 'sm' | 'md' | 'lg'
export default function Switch({ checked, onChange, disabled = false, label = null, size = 'md' }) {
  const toggle = useCallback(() => {
    if (disabled) return;
    onChange(!checked);
  }, [checked, onChange, disabled]);

  const onKeyDown = useCallback((e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onChange(!checked);
    }
  }, [checked, onChange, disabled]);

  const dims = size === 'sm'
    ? { w: 42, h: 24, pad: 2, knob: 20 }
    : size === 'lg'
    ? { w: 64, h: 36, pad: 3, knob: 30 }
    : { w: 54, h: 30, pad: 3, knob: 24 };

  const trackStyle = {
    width: dims.w,
    height: dims.h,
    background: checked ? '#38bdf8' : 'rgba(255,255,255,0.25)', // sky blue
    border: `1px solid ${checked ? '#0ea5e9' : 'rgba(255,255,255,0.35)'}`,
    borderRadius: 999,
    position: 'relative',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'background 150ms ease, border-color 150ms ease',
    boxShadow: checked ? 'inset 0 0 6px rgba(0,0,0,0.2)' : 'inset 0 0 6px rgba(0,0,0,0.1)'
  };

  const knobStyle = {
    position: 'absolute',
    top: dims.pad,
    left: checked ? dims.w - dims.knob - dims.pad : dims.pad,
    width: dims.knob,
    height: dims.knob,
    borderRadius: '50%',
    background: '#fff',
    boxShadow: '0 1px 3px rgba(0,0,0,0.25)\, 0 1px 1px rgba(0,0,0,0.15)',
    transition: 'left 150ms ease'
  };

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, opacity: disabled ? 0.6 : 1 }}>
      {label && (
        <span style={{ color: '#fff', fontSize: size === 'lg' ? '1rem' : '0.9rem' }}>{label}</span>
      )}
      <div
        role="switch"
        aria-checked={checked}
        aria-disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onClick={toggle}
        onKeyDown={onKeyDown}
        style={trackStyle}
        title={label || ''}
      >
        <span style={knobStyle} />
      </div>
    </div>
  );
}
