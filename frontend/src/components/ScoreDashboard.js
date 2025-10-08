import React, { useState, useCallback, useMemo, useEffect } from 'react';

const ScoreDashboard = React.memo(({ scores, game }) => {
  // UI state
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showGamePreview, setShowGamePreview] = useState(false);
  const [previewTab, setPreviewTab] = useState('overview'); // 'overview' | 'description' | 'awards'

  // Details URL (for QR)
  const detailsUrl = useMemo(() => {
    try {
      const origin = window?.location?.origin || '';
      return `${origin}/api/games/${game.id}`;
    } catch {
      return `/api/games/${game.id}`;
    }
  }, [game.id]);

  // External icon URLs
  const PS_LOGO_URL = useMemo(() => 'https://icon2.cleanpng.com/20180729/qbq/234eef5332a8d317914af0d1b0c5da70.webp', []);
  const PC_LOGO_URL = useMemo(() => 'https://assets.streamlinehq.com/image/private/w_300,h_300,ar_1/f_auto/v1/icons/video-games/steam-2myixiwqkwzmuvfmd69q38.png/steam-6zs7qobtrw9nv56hb122tc.png?_a=DATAg1AAZAA0', []);
  const NINTENDO_LOGO_URL = useMemo(() => 'https://upload.wikimedia.org/wikipedia/en/archive/5/51/20250710001602%21Nintendo_logo.svg', []);
  const XBOX_LOGO_URL = useMemo(() => 'https://upload.wikimedia.org/wikipedia/commons/e/e5/Xbox_Logo.svg', []);

  // Increase padding for tab cards to give more breathing room
  const tabCardStyle = { background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 };

  // Platform icon helper
  const PlatformIcon = useCallback(({ name, size = 18 }) => {
    const n = (name || '').toLowerCase();
    const commonProps = { width: size, height: size, viewBox: '0 0 24 24', style: { display: 'inline-block', verticalAlign: 'middle' } };
    if (/playstation|ps4|ps5/.test(n)) {
      return <img src={PS_LOGO_URL} width={size} height={size} alt="PlayStation" style={{ display: 'inline-block', verticalAlign: 'middle', objectFit: 'contain', borderRadius: 4 }} />;
    }
    if (/xbox|series|one/.test(n)) {
      return <img src={XBOX_LOGO_URL} width={size} height={size} alt="Xbox" style={{ display: 'inline-block', verticalAlign: 'middle', objectFit: 'contain' }} />;
    }
    if (/nintendo|switch/.test(n)) {
      return <img src={NINTENDO_LOGO_URL} width={size} height={size} alt="Nintendo" style={{ display: 'inline-block', verticalAlign: 'middle', objectFit: 'contain' }} />;
    }
    if (/windows|pc/.test(n)) {
      return <img src={PC_LOGO_URL} width={size} height={size} alt="PC/Steam" style={{ display: 'inline-block', verticalAlign: 'middle', objectFit: 'contain', borderRadius: 4 }} />;
    }
    if (/mac|os x|ios/.test(n)) {
      return (
        <svg {...commonProps} aria-label="Apple/macOS" role="img">
          <path d="M15.5 3.5c-1 .6-1.7 1.6-1.6 2.8 1.2.1 2.3-.6 3-1.6.7-1 1-2.3.8-3.4-1.1.1-2.2.6-3.2 1.2z" fill="#111" opacity="0.8" />
          <path d="M19.5 14.2c-.5 1.1-.8 1.6-1.5 2.6-.9 1.3-1.9 2.8-3.4 2.8-1.3 0-1.7-.8-3.2-.8-1.5 0-2 .8-3.3.8-1.4 0-2.4-1.4-3.4-2.8C3.5 16.5 3 14 4.1 12.2c.9-1.6 2.5-2.7 4.2-2.7 1.3 0 2.2.8 3.2.8 1 0 1.9-.8 3.3-.8 1 .1 2 .4 2.8 1.1-1.2 1.3-1.1 3 .9 3.6z" fill="#111" opacity="0.9" />
        </svg>
      );
    }
    if (/linux/.test(n)) {
      return (
        <svg {...commonProps} aria-label="Linux" role="img">
          <circle cx="12" cy="9" r="3" fill="#111827" />
          <rect x="8" y="12" width="8" height="7" rx="3" fill="#111827" />
          <circle cx="10.5" cy="8.5" r="0.6" fill="#fff" />
          <circle cx="13.5" cy="8.5" r="0.6" fill="#fff" />
        </svg>
      );
    }
    return (
      <svg {...commonProps} aria-label="Platform" role="img">
        <rect x="4" y="9" width="16" height="6" rx="3" fill="#6b7280" opacity="0.6" />
        <circle cx="9" cy="12" r="1.2" fill="#374151" />
        <circle cx="15" cy="12" r="1.2" fill="#374151" />
      </svg>
    );
  }, [NINTENDO_LOGO_URL, PC_LOGO_URL, PS_LOGO_URL, XBOX_LOGO_URL]);

  // Rubric metric tiles
  const rubricItems = useMemo(() => [
    { label: 'Core Gameplay', value: scores.core_gameplay_score ?? scores.game_mechanics_score, color: '#45b7d1', key: 'core_gameplay' },
    { label: 'Story & Immersion', value: scores.story_immersion_score ?? scores.story_quality_score, color: '#eb4d4b', key: 'story_immersion' },
    { label: 'Presentation', value: scores.presentation_score ?? scores.graphic_score, color: '#4ecdc4', key: 'presentation' },
    { label: 'Technical Performance', value: scores.technical_performance_score ?? scores.microtransactions_score, color: '#ff9f43', key: 'technical_performance' },
    { label: 'Completeness', value: scores.completeness_score, color: '#f0932b', key: 'completeness_score' },
    { label: 'Innovation & Creativity', value: scores.innovation_creativity_score, color: '#6c5ce7', key: 'innovation_creativity' },
    { label: 'Community & Longevity', value: scores.community_longevity_score, color: '#9980FA', key: 'community_longevity' }
  ], [scores]);

  // Telemetry state (not rendered here, but kept for parity)
  const [telemetry, setTelemetry] = useState(null);
  const [telemetryLoading, setTelemetryLoading] = useState(true);
  const [telemetryError, setTelemetryError] = useState(null);
  const fetchTelemetry = useCallback(async (force = false) => {
    setTelemetryLoading(true); setTelemetryError(null);
    try {
      const resp = await fetch(`/api/games/${game.id}/community-telemetry${force ? '?force=true' : ''}`);
      if (!resp.ok) throw new Error('Failed to load telemetry');
      const data = await resp.json();
      setTelemetry(data.telemetry);
    } catch (e) {
      setTelemetryError(e.message);
    } finally {
      setTelemetryLoading(false);
    }
  }, [game.id]);
  useEffect(() => { fetchTelemetry(false); }, [fetchTelemetry]);

  // Informational (non-weighted) items
  const infoItems = useMemo(() => [
    { label: 'Reviews (Informational)', key: 'reviews_score' },
    { label: 'Accessibility (Informational)', key: 'accessibility_score' },
    { label: 'Monetisation (Informational)', key: 'monetisation' },
    { label: 'Life Support (Informational)', key: 'life_support' },
    { label: 'Inferred Life Support (AI)', key: 'life_support_inferred' }
  ], []);

  // Life support state and derivation
  const [lifeSupport, setLifeSupport] = useState({ status: 'unknown', delta: 0, loading: true, notes: null });
  useEffect(() => {
    const existing = scores?.reasoning?.life_support;
    if (existing && existing.detailed) {
      const d = existing.detailed;
      const delta = d.delta_applied ?? d.life_support_delta ?? d.applied_delta ?? 0;
      setLifeSupport({
        status: d.status || 'unknown',
        delta,
        loading: false,
        notes: d.notes || null,
        last_update_date: d.last_update_date,
        next_update_hint: d.next_update_hint
      });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch(`/api/games/${game.id}/life-support`);
        if (!resp.ok) throw new Error('life support fetch failed');
        const data = await resp.json();
        if (cancelled) return;
        if (data.life_support) {
          const status = data.life_support.support_status || 'unknown';
          const deltaMap = { eternal: 10, active: 5, sunset: -5, offline: -10, unknown: 0 };
          setLifeSupport({
            status,
            delta: deltaMap[status] ?? 0,
            loading: false,
            notes: data.life_support.notes,
            last_update_date: data.life_support.last_update_date,
            next_update_hint: data.life_support.next_update_hint
          });
        } else {
          setLifeSupport(ls => ({ ...ls, loading: false }));
        }
      } catch {
        if (!cancelled) setLifeSupport(ls => ({ ...ls, loading: false }));
      }
    })();
    return () => { cancelled = true; };
  }, [game.id, scores?.reasoning]);

  const lifeSupportColor = useMemo(() => {
    const map = { eternal: '#27ae60', active: '#2980b9', sunset: '#e67e22', offline: '#c0392b', unknown: '#7f8c8d' };
    return map[lifeSupport.status] || '#7f8c8d';
  }, [lifeSupport.status]);
  const lifeSupportLabel = useMemo(() => {
    if (lifeSupport.loading) return 'Loading…';
    const deltaTxt = lifeSupport.delta ? ` (${lifeSupport.delta > 0 ? '+' : ''}${lifeSupport.delta})` : '';
    return `${lifeSupport.status.charAt(0).toUpperCase()}${lifeSupport.status.slice(1)}${deltaTxt}`;
  }, [lifeSupport.loading, lifeSupport.status, lifeSupport.delta]);

  // Monetisation fairness tag (color + label)
  const monetisationFairness = useMemo(() => {
    const d = scores?.reasoning?.monetisation?.detailed;
    if (d && typeof d === 'object' && (d.fairness_label || d.fairness_color)) {
      const label = typeof d.fairness_label === 'string' ? d.fairness_label : 'Unknown';
      const color = typeof d.fairness_color === 'string' ? d.fairness_color : '#7f8c8d';
      return { label, color };
    }
    let label = 'Unknown';
    let color = '#7f8c8d';
    if (d && typeof d === 'object') {
      const types = Array.isArray(d.types) ? d.types.filter(Boolean) : [];
      const notesStr = typeof d.notes === 'string' ? d.notes : '';
      const textHas = (re) => types.some(t => typeof t === 'string' && re.test(t)) || re.test(notesStr);
      const hasP2W = textHas(/(^|\b)(p2w\s*:\s*yes|pay\s*-?to\s*-?win|gameplay\s*advantage|stat\s*boost|xp\s*(boost|advantage)|power\s*boost)/i) || textHas(/p2w\s*:\s*mixed/i);
      const explicitP2WNo = textHas(/(^|\b)p2w\s*:\s*no\b/i);
      const explicitNoMTX = textHas(/no\s*(microtransactions|mtx)\b/i);
      const hasMTX = textHas(/(\bmtx\b|microtransaction|battle\s*pass|item\s*shop|in[- ]app|iap|loot\s*box|gacha)/i);
      if (hasP2W) { label = 'Poor'; color = '#c0392b'; }
      else if (explicitNoMTX || (!hasMTX && !hasP2W)) { label = 'Perfect'; color = '#00bfff'; }
      else if (hasMTX && (explicitP2WNo || !hasP2W)) { label = 'Fair'; color = '#8e44ad'; }
    }
    return { label, color };
  }, [scores?.reasoning?.monetisation]);

  // Modal control helpers
  const handleMetricClick = useCallback((metricKey) => { setSelectedMetric(metricKey); setShowModal(true); }, []);
  const closeModal = useCallback(() => { setShowModal(false); setSelectedMetric(null); }, []);
  const reasoningRef = useMemo(() => (scores && scores.reasoning) || null, [scores]);
  const getReasoning = useCallback((metricKey) => reasoningRef?.[metricKey] || { short: 'No reasoning available', detailed: 'No detailed reasoning available' }, [reasoningRef]);
  const selectedReasoning = useMemo(() => { if (!selectedMetric) return null; return getReasoning(selectedMetric); }, [selectedMetric, getReasoning]);

  // Render helpers
  const renderDetailed = useCallback((reason) => {
    if (!reason) return <p style={{ margin: 0 }}>No details.</p>;
    const detailed = reason.detailed;
    if (detailed == null) return <p style={{ margin: 0 }}>No detailed explanation available.</p>;
    if (typeof detailed === 'string' || typeof detailed === 'number') {
      return <p style={{ margin: 0, textAlign: 'justify' }}>{String(detailed)}</p>;
    }
    if (Array.isArray(detailed)) {
      if (!detailed.length) return <p style={{ margin: 0 }}>No entries.</p>;
      return (
        <ul style={{ margin: '0 0 0 18px', padding: 0 }}>
          {detailed.map((v, i) => (
            <li key={i} style={{ marginBottom: '4px' }}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</li>
          ))}
        </ul>
      );
    }
    if (typeof detailed === 'object') {
      const entries = Object.entries(detailed).filter(([k]) => k !== 'explanation');
      const explanation = detailed.explanation;
      if (!entries.length && !explanation) return <p style={{ margin: 0 }}>No structured details.</p>;
      return (
        <div style={{ margin: 0 }}>
          {entries.length > 0 && (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: explanation ? '12px' : 0 }}>
              <tbody>
                {entries.map(([k, v]) => (
                  <tr key={k}>
                    <td style={{ padding: '4px 6px', fontWeight: 500, fontSize: '0.85rem', textTransform: 'capitalize', width: '55%' }}>{k.replace(/_/g, ' ')}</td>
                    <td style={{ padding: '4px 6px', fontSize: '0.85rem', textAlign: 'right' }}>
                      {typeof v === 'number' ? `${v.toFixed(1)}` : (typeof v === 'object' ? JSON.stringify(v) : String(v))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {explanation && (
            <p style={{ margin: 0, textAlign: 'justify', fontSize: '0.9rem', lineHeight: 1.4 }}>{explanation}</p>
          )}
        </div>
      );
    }
    return <p style={{ margin: 0 }}>{String(detailed)}</p>;
  }, []);

  const renderMonetisation = useCallback((reason) => {
    if (!reason) return <p style={{ margin: 0 }}>No details.</p>;
    const detailed = reason.detailed;
    if (typeof detailed === 'string') {
      return <p style={{ margin: 0, textAlign: 'justify' }}>{detailed}</p>;
    }
    if (detailed && typeof detailed === 'object') {
      const types = Array.isArray(detailed.types) ? detailed.types.filter(Boolean) : [];
      const notes = typeof detailed.notes === 'string' ? detailed.notes : null;
      return (
        <div style={{ margin: 0 }}>
          {types.length > 0 && (
            <ul style={{ margin: '0 0 10px 18px', padding: 0 }}>
              {types.map((t, i) => (
                <li key={i} style={{ marginBottom: '4px' }}>{String(t)}</li>
              ))}
            </ul>
          )}
          {notes && (
            <p style={{ margin: 0, textAlign: 'justify' }}>{notes}</p>
          )}
          {!types.length && !notes && (
            <p style={{ margin: 0 }}>No monetisation details available.</p>
          )}
        </div>
      );
    }
    return <p style={{ margin: 0 }}>No monetisation details available.</p>;
  }, []);

  const overallScoreColor = useMemo(() => {
    const score = scores.overall_score;
    // Use Sky Blue when the score passes over 78%
    if (typeof score === 'number' && score > 78) return '#00bfff';
    // Fallback colors for lower bands
    return score >= 70 ? '#f9ca24' : '#ff6b6b';
  }, [scores.overall_score]);

  return (
    <div style={{ padding: '20px' }}>
      <h2
        onClick={() => setShowGamePreview(true)}
        title="Tap to preview game details"
        role="button"
        style={{
          color: '#fff', textAlign: 'center', marginBottom: '15px', background: 'rgba(255, 255, 255, 0.1)',
          padding: '15px 30px', borderRadius: '25px', border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)', fontSize: '2rem', fontWeight: '300', cursor: 'pointer'
        }}
      >
        {game.title} - Quality Analysis
      </h2>

      {/* Life Support Badge */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '25px' }}>
        <div
          onClick={() => handleMetricClick('life_support')}
          title={lifeSupportLabel}
          style={{
            background: 'rgba(255,255,255,0.1)', border: `1px solid ${lifeSupportColor}55`, padding: '10px 18px', borderRadius: '999px',
            cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '10px', boxShadow: '0 2px 10px rgba(0,0,0,0.25)', backdropFilter: 'blur(4px)'
          }}
        >
          <span style={{ width: 14, height: 14, borderRadius: '50%', background: lifeSupportColor, boxShadow: `0 0 6px ${lifeSupportColor}cc` }} />
          <span style={{ color: '#fff', fontSize: '0.95rem', fontWeight: 500 }}>Life Support: {lifeSupportLabel}</span>
          {lifeSupport.notes && (
            <span style={{ color: '#ddd', fontSize: '0.75rem', fontStyle: 'italic', maxWidth: 260, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {lifeSupport.notes}
            </span>
          )}
        </div>
      </div>

      {/* Metric tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '25px', marginBottom: '30px' }}>
        {rubricItems.map((item, index) => (
          <div key={index}
            style={{
              background: 'rgba(255, 255, 255, 0.1)', borderRadius: '20px', padding: '25px', textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.2)', boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)', transition: 'transform 0.2s ease, box-shadow 0.2s ease', cursor: 'pointer'
            }}
            onClick={() => handleMetricClick(item.key)}
            title={item.label}
            onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)'; }}
          >
            <h3 style={{ margin: '0 0 15px 0', color: '#fff', fontSize: '1.1rem', fontWeight: 500 }}>{item.label}</h3>
            <div style={{ fontSize: '2.8rem', fontWeight: 'bold', color: item.color, textShadow: '0 0 5px rgba(255, 255, 255, 0.2)', marginBottom: 10 }}>
              {item.value ?? '—'}{typeof item.value === 'number' ? '%' : ''}
            </div>
            <div style={{ width: '100%', height: 8, background: 'rgba(255, 255, 255, 0.2)', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: `${item.value || 0}%`, height: '100%', background: `linear-gradient(90deg, ${item.color}, ${item.color}aa)`, borderRadius: 4, transition: 'width 0.8s ease' }} />
            </div>
          </div>
        ))}

        {/* Monetisation preview card */}
        <div
          onClick={() => handleMetricClick('monetisation')}
          title="Monetisation"
          style={{ background: 'rgba(255, 255, 255, 0.1)', borderRadius: 20, padding: 25, textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.2)', boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)', transition: 'transform 0.2s ease, box-shadow 0.2s ease', cursor: 'pointer' }}
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)'; }}
        >
          <h3 style={{ margin: '0 0 15px 0', color: '#fff', fontSize: '1.1rem', fontWeight: 500 }}>Monetisation</h3>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 10 }}>
            <span style={{ width: 14, height: 14, borderRadius: '50%', background: monetisationFairness.color, boxShadow: `0 0 6px ${monetisationFairness.color}aa` }} />
            <span style={{ color: '#eee', fontSize: '0.95rem', fontWeight: 500 }}>Fairness: {monetisationFairness.label}</span>
          </div>
          <div style={{ width: '100%', height: 8, background: 'rgba(255, 255, 255, 0.2)', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: '100%', height: '100%', background: `linear-gradient(90deg, ${monetisationFairness.color}, ${monetisationFairness.color}aa)`, borderRadius: 4, opacity: 0.6 }} />
          </div>
        </div>
      </div>

      {/* Informational panels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '25px', marginBottom: '30px' }}>
        <div onClick={() => handleMetricClick('reviews_score')} title="View reviews details" style={{ background: 'rgba(255,255,255,0.12)', padding: 20, borderRadius: 18, border: '1px solid rgba(255,255,255,0.25)', cursor: 'pointer' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#fff' }}>Reviews (Informational)</h4>
          <p style={{ margin: 0, color: '#eee', fontSize: '0.9rem' }}>Metacritic: {scores.reviews_score ?? 'N/A'}/100 (Not weighted).</p>
        </div>
        <div onClick={() => handleMetricClick('accessibility_score')} title="View accessibility details" style={{ background: 'rgba(255,255,255,0.12)', padding: 20, borderRadius: 18, border: '1px solid rgba(255,255,255,0.25)', cursor: 'pointer' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#fff' }}>Accessibility (Informational)</h4>
          <p style={{ margin: 0, color: '#eee', fontSize: '0.9rem' }}>Score: {scores.accessibility_score ?? 'N/A'} (Heuristic blend)</p>
          {(() => {
            const det = scores?.reasoning?.accessibility_score?.detailed;
            const feats = det?.heuristic_features;
            if (!feats) return null;
            const vals = Object.values(feats);
            const total = vals.length;
            const present = vals.filter(v => !!v).length;
            return (
              <p style={{ margin: '6px 0 0 0', color: '#ddd', fontSize: '0.8rem' }}>
                Features present: {present}/{total} • Confidence: {det?.heuristic_confidence ?? '—'}
              </p>
            );
          })()}
        </div>
        <div onClick={() => handleMetricClick('life_support')} title="View life support details" style={{ background: 'rgba(255,255,255,0.12)', padding: 20, borderRadius: 18, border: `1px solid ${lifeSupportColor}55`, cursor: 'pointer' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#fff' }}>Life Support (Informational)</h4>
          <p style={{ margin: 0, color: '#eee', fontSize: '0.9rem' }}>
            {lifeSupportLabel}{lifeSupport.last_update_date ? ` • Updated: ${lifeSupport.last_update_date}` : ''}
          </p>
        </div>
        {scores?.reasoning?.life_support_inferred && (
          <div onClick={() => handleMetricClick('life_support_inferred')} title="View inferred life support details" style={{ background: 'rgba(255,255,255,0.12)', padding: 20, borderRadius: 18, border: '1px solid rgba(255,255,255,0.25)', cursor: 'pointer' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#fff' }}>Inferred Life Support (AI)</h4>
            <p style={{ margin: 0, color: '#eee', fontSize: '0.9rem' }}>{scores.reasoning.life_support_inferred.short}</p>
          </div>
        )}
      </div>

      {/* Overall score highlight */}
      <div onClick={() => handleMetricClick('overall_score')} title={getReasoning('overall_score').short} style={{ background: 'rgba(255, 255, 255, 0.15)', borderRadius: 25, padding: 30, textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.3)', boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)', position: 'relative', overflow: 'hidden', cursor: 'pointer' }}>
        <h3 style={{ margin: '0 0 20px 0', color: '#fff', fontSize: '2rem', fontWeight: 300, position: 'relative', zIndex: 1 }}>Overall Quality Score</h3>
        <div style={{ fontSize: '5rem', fontWeight: 'bold', color: '#fff', textShadow: '0 0 10px rgba(255, 255, 255, 0.3)', position: 'relative', zIndex: 1 }}>{scores.overall_score}%</div>
        <div style={{ width: 200, height: 200, margin: '20px auto 0', borderRadius: '50%', background: `conic-gradient(${overallScoreColor} ${scores.overall_score}%, rgba(255, 255, 255, 0.1) ${scores.overall_score}%)`, position: 'relative', zIndex: 1, boxShadow: '0 0 15px rgba(255, 255, 255, 0.1)' }}>
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 160, height: 160, borderRadius: '50%', background: 'rgba(255, 255, 255, 0.1)' }} />
        </div>
      </div>

      {/* Data Source disclaimer */}
      <div style={{ marginTop: 30, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 15, padding: 20, border: '1px solid rgba(255, 255, 255, 0.15)', boxShadow: '0 2px 15px rgba(0, 0, 0, 0.05)' }}>
        <h4 style={{ margin: '0 0 10px 0', color: '#fff', fontSize: '1rem', fontWeight: 500, textAlign: 'center' }}>📊 Data Source Information</h4>
        <p style={{ margin: 0, color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.9rem', lineHeight: 1.4, textAlign: 'center' }}>
          Scores are generated using data from <strong>RAWG.io</strong>, which aggregates information from various sources.
          Metacritic scores may vary slightly from official values due to timing and source differences.
          For official critic scores, please check <strong>Metacritic.com</strong> directly.
        </p>
      </div>

      {/* Metric reasoning modal */}
      {showModal && selectedMetric && selectedReasoning && (
        <div onClick={closeModal} style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0, 0, 0, 0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'rgba(255, 255, 255, 0.95)', borderRadius: 20, padding: 30, maxWidth: 500, maxHeight: '70vh', overflowY: 'auto', border: '1px solid rgba(255, 255, 255, 0.3)', boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, color: '#333', fontSize: '1.5rem', fontWeight: 600 }}>
                {(() => {
                  if (selectedMetric === 'overall_score') return 'Overall Quality Score';
                  const rubricMatch = rubricItems.find(item => item.key === selectedMetric);
                  if (rubricMatch) return rubricMatch.label;
                  const infoMatch = [{ label: 'Reviews (Informational)', key: 'reviews_score' }, { label: 'Accessibility (Informational)', key: 'accessibility_score' }, { label: 'Monetisation (Informational)', key: 'monetisation' }, { label: 'Life Support (Informational)', key: 'life_support' }, { label: 'Inferred Life Support (AI)', key: 'life_support_inferred' }].find(item => item.key === selectedMetric);
                  if (infoMatch) return infoMatch.label;
                  return 'Score Details';
                })()}
              </h3>
              <button onClick={closeModal} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: '#666', padding: 5 }}>×</button>
            </div>
            <div style={{ color: '#555', lineHeight: 1.6, fontSize: '1rem' }}>
              <p style={{ fontWeight: 500, color: '#333', marginBottom: 15, fontSize: '1.1rem' }}>{selectedReasoning.short}</p>
              {selectedMetric === 'monetisation' ? renderMonetisation(selectedReasoning) : renderDetailed(selectedReasoning)}
            </div>
          </div>
        </div>
      )}

      {/* Game Preview modal with tabs */}
      {showGamePreview && (
        <div onClick={() => setShowGamePreview(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ width: 'min(1100px, 98vw)', background: 'rgba(255,255,255,0.98)', borderRadius: 18, border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 12px 36px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
            <div style={{ display: 'flex', padding: 16, alignItems: 'center', borderBottom: '1px solid rgba(0,0,0,0.08)' }}>
              <h3 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 600, color: '#222', flex: 1 }}>{game.title}</h3>
              <button onClick={() => setShowGamePreview(false)} style={{ border: 'none', background: 'transparent', fontSize: '1.5rem', cursor: 'pointer', color: '#666' }}>×</button>
            </div>
            {/* Increase grid gap and padding for modal content area */}
            <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20, padding: 20 }}>
              <div>
                {game.cover_image ? (
                  <img src={game.cover_image} alt={`${game.title} cover`} style={{ width: '100%', height: 320, objectFit: 'cover', borderRadius: 12, border: '1px solid rgba(0,0,0,0.08)' }} />
                ) : (
                  <div style={{ width: '100%', height: 320, borderRadius: 12, border: '1px dashed rgba(0,0,0,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#777' }}>No image</div>
                )}
              </div>
              {/* Increase vertical spacing between tab bar and content */}
              <div style={{ display: 'grid', gap: 16 }}>
                <div style={{ display: 'flex', gap: 10, borderBottom: '1px solid #e5e7eb', marginBottom: 8, paddingBottom: 4 }}>
                  {['overview', 'description', 'awards'].map(tab => (
                    <button key={tab} onClick={() => setPreviewTab(tab)} style={{ border: 'none', background: previewTab === tab ? '#0ea5e9' : 'transparent', color: previewTab === tab ? '#fff' : '#0f172a', padding: '8px 12px', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}>
                      {tab === 'overview' ? 'Overview' : tab === 'description' ? 'Description' : 'Awards'}
                    </button>
                  ))}
                </div>

                {previewTab === 'overview' && (
                  <div style={tabCardStyle}>
                    {/* Add more row spacing inside the overview card */}
                    <div style={{ display: 'grid', gap: 16 }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, color: '#333' }}>
                        {game.release_year && <span style={{ padding: '6px 10px', background: '#eef2ff', borderRadius: 8, border: '1px solid #dbe4ff' }}>Year: <strong>{game.release_year}</strong></span>}
                        {game.release_date && <span style={{ padding: '6px 10px', background: '#f0f9ff', borderRadius: 8, border: '1px solid #cff0ff' }}>Released: <strong>{game.release_date}</strong></span>}
                      </div>
                      {(() => {
                        const list = Array.isArray(game.platforms) && game.platforms.length > 0 ? game.platforms : (game.platform ? [game.platform] : []);
                        if (!list.length) return null;
                        return (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                            {list.map((p, idx) => (
                              <span key={`${p}-${idx}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: '#f8fafc', borderRadius: 999, border: '1px solid #e5e7eb', color: '#111827', fontSize: '0.9rem', whiteSpace: 'nowrap', lineHeight: 1.25 }}>
                                <PlatformIcon name={p} />
                                <span style={{ whiteSpace: 'nowrap' }}>{p}</span>
                              </span>
                            ))}
                          </div>
                        );
                      })()}
                    </div>
                    <div style={{ color: '#444', fontSize: '0.95rem', marginTop: 10 }}>
                      <p style={{ margin: 0 }}>Overall Score: <strong>{scores.overall_score}%</strong></p>
                      {scores?.reasoning?.monetisation?.detailed?.fairness_label && (
                        <p style={{ margin: '6px 0 0 0' }}>Monetisation Fairness: <span style={{ fontWeight: 600, color: monetisationFairness.color }}>{monetisationFairness.label}</span></p>
                      )}
                    </div>
                    {/* Increase spacing between action buttons */}
                    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 16 }}>
                      {game.rawg_id && (
                        <a href={`https://rawg.io/games/${game.rawg_id}`} target="_blank" rel="noreferrer" style={{ background: '#111827', color: '#fff', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', fontSize: '0.9rem' }}>View on RAWG</a>
                      )}
                      {game.cover_image && (
                        <a href={game.cover_image} target="_blank" rel="noreferrer" style={{ background: '#374151', color: '#fff', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', fontSize: '0.9rem' }}>Open Cover</a>
                      )}
                    </div>
                    {/* Increase margin and gap for the QR/details row */}
                    <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: 'auto 1fr', alignItems: 'center', gap: 18 }}>
                      <img src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(detailsUrl)}`} alt="QR code to game details" style={{ width: 120, height: 120, borderRadius: 8, border: '1px solid #e5e7eb' }} />
                      <div style={{ fontSize: '0.9rem', color: '#374151' }}>
                        <div style={{ fontWeight: 600, marginBottom: 6 }}>Scan for database details</div>
                        <div style={{ wordBreak: 'break-all', color: '#111827' }}>{detailsUrl}</div>
                        {(() => {
                          const isLocal = typeof window !== 'undefined' && /localhost|127\.0\.0\.1/.test(window.location.hostname);
                          if (!isLocal) return null;
                          return (
                            <div style={{ marginTop: 8, fontSize: '0.8rem', color: '#6b7280' }}>
                              Tip: If scanning from another device, ensure your machine is reachable on the network.
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                    {scores?.reasoning?.overall_score?.detailed && (
                      <p style={{ margin: '10px 0 0 0', color: '#555', fontSize: '0.9rem' }}>{scores.reasoning.overall_score.detailed}</p>
                    )}
                  </div>
                )}

                {previewTab === 'awards' && (
                  <div style={tabCardStyle}>
                    {(() => {
                      const awards = Array.isArray(game?.awards) && game.awards.length
                        ? game.awards
                        : (/elden ring/i.test(game?.title || '')
                            ? [
                                { year: 2022, name: 'Game of the Year', organization: 'The Game Awards' },
                                { year: 2022, name: 'Ultimate Game of the Year', organization: 'Golden Joystick Awards' },
                                { year: 2023, name: 'Game of the Year', organization: 'D.I.C.E. Awards' }
                              ]
                            : []);
                      return (
                        <>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                            <span style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>Awards</span>
                            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>curated; verify with official sources</span>
                          </div>
                          {awards.length ? (
                            <ul style={{ margin: 0, padding: '0 0 0 18px', color: '#111827' }}>
                              {awards.map((a, i) => (
                                <li key={i} style={{ marginBottom: 4, lineHeight: 1.3 }}>
                                  <span style={{ fontWeight: 600 }}>{a.name}</span>
                                  {a.organization ? ` — ${a.organization}` : ''}
                                  {a.year ? ` (${a.year})` : ''}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <div style={{ color: '#475569' }}>No awards data available.</div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                )}

                {previewTab === 'description' && (
                  <div style={tabCardStyle}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>About this game</span>
                    </div>
                    <div style={{ color: '#111827', fontSize: '0.95rem', lineHeight: 1.5 }}>
                      <p style={{ marginTop: 0 }}>
                        {game.title}{game.release_year ? ` (${game.release_year})` : ''}
                        {Array.isArray(game.platforms) && game.platforms.length ? ` • Available on ${game.platforms.join(', ')}` : (game.platform ? ` • Platform: ${game.platform}` : '')}
                      </p>
                      <p style={{ marginBottom: 10, color: '#334155' }}>
                        {scores?.reasoning?.presentation?.detailed?.explanation || scores?.reasoning?.overall_score?.detailed || 'A popular title evaluated by our rubric for gameplay, story, presentation, performance, innovation, and community.'}
                      </p>
                      <div style={{ marginTop: 10 }}>
                        <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>Why play</div>
                        <ul style={{ margin: 0, padding: '0 0 0 18px' }}>
                          <li style={{ marginBottom: 6 }}>{scores?.reasoning?.core_gameplay?.short || 'Strong core gameplay loop.'}</li>
                          <li style={{ marginBottom: 6 }}>{scores?.reasoning?.story_immersion?.short || 'Engaging narrative and worldbuilding.'}</li>
                          <li style={{ marginBottom: 6 }}>{scores?.reasoning?.innovation_creativity?.short || 'Notable creativity or genre impact.'}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

export default ScoreDashboard;