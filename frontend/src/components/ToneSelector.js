import React, { useMemo } from 'react';
import { useTone } from '../context/ToneContext';
import { toneStyles } from '../utils/textTone';

const ToneSelector = React.memo(() => {
  const { tone, setTone } = useTone();
  const toneKeys = useMemo(() => Object.keys(toneStyles), []);
  const labelFor = (k) => (k === 'brutal' ? 'brutal honest' : k);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 12, color: '#fff' }}>
      <label htmlFor="tone-select" style={{ fontWeight: 600 }}>Tone</label>
      <select
        id="tone-select"
        value={tone}
        onChange={(e) => setTone(e.target.value)}
        style={{ padding: '6px 8px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.15)', color: '#fff' }}
      >
        {toneKeys.map((k) => (
          <option key={k} value={k} style={{ color: '#111' }}>{labelFor(k)}</option>
        ))}
      </select>
      <span style={{ fontSize: 12, opacity: 0.9 }}>{toneStyles[tone]}</span>
    </div>
  );
});

export default ToneSelector;
