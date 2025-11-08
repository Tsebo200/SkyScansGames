import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import axios from 'axios';
import { debounce } from 'lodash';
import sfx from '../utils/sfx';

const SearchBar = React.memo(({ onGameSelect, hideVariants: hideVariantsProp, onChangeHideVariants }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const optionsRef = useRef({});
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' ? window.innerWidth < 768 : false);
  // Speech-to-text support
  const [isSpeechSupported, setIsSpeechSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  // Support controlled or uncontrolled hideVariants
  const [hideVariantsState, setHideVariantsState] = useState(true);
  const hideVariants = (typeof hideVariantsProp === 'boolean') ? hideVariantsProp : hideVariantsState;
  const setHideVariants = onChangeHideVariants || setHideVariantsState;

  // Heuristic filters to hide DLC/editions/spinoffs from results
  const isVariantTitle = useCallback((title) => {
    if (!title) return false;
    const t = String(title).toLowerCase();
    // Keywords indicating non-base entries
    const variantKeywords = [
      'demo', 'prologue', 'beta', 'alpha', 'trial', 'prototype',
      'remaster', 'remastered', 'definitive', 'complete edition',
      'collection', 'origins collection', 'anniversary', 'director\'s cut',
      'ultimate', 'deluxe', 'gold', 'goty', 'bundle', 'pack',
      'expansion', 'dlc', 'season pass', 'expansion pass',
      'soundtrack', 'vr', 'mobile', 'lite', 'cloud version', 'hd',
      'hd edition', 'hd remaster', 'free trial'
    ];
    return variantKeywords.some(k => t.includes(k));
  }, []);

  // Deduplicate by a normalized key (strip punctuation/edition words)
  const normalizeKey = useCallback((title) => {
    if (!title) return '';
    let t = String(title).toLowerCase();
    t = t.replace(/\(.*?\)|\[.*?\]/g, ' '); // remove bracketed info
    t = t.replace(/[^a-z0-9:\-\s]/g, ' ');    // strip non-alphanum except colon/dash/space
    // remove common edition words
    const stop = ['remastered','definitive','complete','edition','collection','bundle','ultimate','deluxe','gold'];
    stop.forEach(w => { t = t.replace(new RegExp(`\\b${w}\\b`, 'g'), ' '); });
    return t.replace(/\s+/g, ' ').trim();
  }, []);

  const debouncedSearch = useMemo(
    () => debounce((q) => {
      if (q.length < 2) {
        setResults([]);
        return;
      }
      setLoading(true);
      const apiBase = process.env.REACT_APP_API_BASE || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api');
      axios.get(`${apiBase}/games/search`, { params: { q } })
        .then(response => {
          let data = Array.isArray(response.data) ? response.data : [];
          // Optional filter of variants
          if (hideVariants) {
            data = data.filter(g => !isVariantTitle(g.title));
          }
          // Deduplicate by normalized key (keep first occurrence)
          const seen = new Set();
          const deduped = [];
          for (const g of data) {
            const key = normalizeKey(g.title);
            if (seen.has(key)) continue;
            seen.add(key);
            deduped.push(g);
          }
          setResults(deduped);
        })
        .catch(error => {
          console.error('Search error:', error);
          setResults([]);
        })
        .finally(() => {
          setLoading(false);
        });
    }, 300), // Reduced debounce time for better responsiveness
    [hideVariants, isVariantTitle, normalizeKey]
  );

  useEffect(() => {
    debouncedSearch(query);
    // Reset active index when query changes
    setActiveIndex(-1);
    return () => debouncedSearch.cancel();
  }, [query, debouncedSearch]);

  // Responsive window width detection
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Detect Web Speech API support
  useEffect(() => {
    try {
      const w = typeof window !== 'undefined' ? window : {};
      const SR = w.SpeechRecognition || w.webkitSpeechRecognition;
      setIsSpeechSupported(!!SR);
    } catch {
      setIsSpeechSupported(false);
    }
  }, []);

  const handleSelect = useCallback((game) => {
    // Unlock audio on user interaction
    try { sfx.unlock(); } catch {}
    onGameSelect(game);
    setQuery('');
    setResults([]);
    setActiveIndex(-1);
  }, [onGameSelect]);

  // When results change, reset activeIndex to first item
  useEffect(() => {
    if (results.length > 0) {
      setActiveIndex(0);
    } else {
      setActiveIndex(-1);
    }
  }, [results.length]);

  const handleKeyDown = useCallback((e) => {
    if (!results || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((idx) => {
        if (idx < 0) return 0; // Start at first item if no selection
        return (idx + 1) % results.length;
      });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((idx) => {
        if (idx <= 0) return results.length - 1; // Wrap to last item
        return idx - 1;
      });
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0 && activeIndex < results.length) {
        e.preventDefault();
        handleSelect(results[activeIndex]);
      } else if (results.length > 0) {
        // If no selection but results exist, select first item
        e.preventDefault();
        handleSelect(results[0]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setResults([]);
      setActiveIndex(-1);
      setQuery('');
    }
  }, [results, activeIndex, handleSelect]);

  // Scroll active option into view when it changes
  useEffect(() => {
    const id = results[activeIndex]?.id;
    if (id && optionsRef.current[id]) {
      try { optionsRef.current[id].scrollIntoView({ block: 'nearest' }); } catch {}
    }
  }, [activeIndex, results]);

  // Speech recognition handlers
  const startListening = useCallback(() => {
    if (!isSpeechSupported || isListening) return;
    try {
      const w = typeof window !== 'undefined' ? window : {};
      const SR = w.SpeechRecognition || w.webkitSpeechRecognition;
      if (!SR) return;
      const rec = new SR();
      recognitionRef.current = rec;
      rec.lang = 'en-GB';
      rec.interimResults = true;
      rec.maxAlternatives = 1;
      let finalTranscript = '';
      rec.onstart = () => setIsListening(true);
      rec.onerror = () => { setIsListening(false); };
      rec.onend = () => {
        setIsListening(false);
        if (finalTranscript.trim()) {
          setQuery(finalTranscript.trim());
        }
      };
      rec.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript;
          if (event.results[i].isFinal) finalTranscript += t;
          else interim += t;
        }
        // Show interim in the input so users can see progress
        const composed = (finalTranscript + ' ' + interim).trim();
        if (composed) setQuery(composed);
      };
      rec.start();
    } catch {
      setIsListening(false);
    }
  }, [isSpeechSupported, isListening]);

  const stopListening = useCallback(() => {
    try {
      const rec = recognitionRef.current;
      if (rec) rec.stop();
    } catch {}
  }, []);

  // Memoize the results list to prevent unnecessary re-renders
  const resultsList = useMemo(() => results.map((game, index) => {
    const isActive = index === activeIndex;
    const optionId = `search-option-${game.id}`;
    return (
    <li
      key={game.id}
      id={optionId}
      role="option"
      aria-selected={isActive}
      onClick={() => handleSelect(game)}
      style={{
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
        padding: '12px 18px',
        cursor: 'pointer',
        borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
        transition: 'background 0.2s ease',
        color: '#333',
        fontSize: '15px',
        background: isActive ? 'rgba(14, 165, 233, 0.15)' : 'transparent'
      }}
      ref={(el) => { if (el) optionsRef.current[game.id] = el; }}
    >
      {game.cover_image && (
        <img
          src={game.cover_image}
          alt={game.title}
          style={{
            width: isMobile ? '40px' : '48px',
            height: isMobile ? '40px' : '48px',
            objectFit: 'cover',
            borderRadius: '8px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.15)'
          }}
          loading="lazy"
        />
      )}
      <div style={{ flex: 1 }}>
        <strong style={{ color: '#000', fontSize: isMobile ? '14px' : '16px', display: 'block' }}>{game.title || 'Unknown Game'}</strong>
        <small style={{ color: '#666', fontSize: isMobile ? '12px' : '13px', display:'block' }}>
          {game.generation ? `Generation ${game.generation}` : 'Unknown Generation'} • {game.platform || 'Unknown Platform'}
        </small>
        {Array.isArray(game.platforms) && game.platforms.length > 0 && (
          <small style={{ color: '#888', fontSize: isMobile ? '11px' : '12px', display:'block', marginTop:'2px' }}>
            {game.platforms.slice(0, isMobile ? 4 : 6).join(', ')}{game.platforms.length > (isMobile ? 4 : 6) ? '…' : ''}
          </small>
        )}
      </div>
    </li>
  );
  }), [results, handleSelect, activeIndex, isMobile]);

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: isMobile ? '100%' : '500px', boxSizing: 'border-box' }}>
      <style>
        {`input::placeholder { color: white; }`}
      </style>
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            // Unlock audio on first user interaction
            try { sfx.unlock(); } catch {}
          }}
          onKeyDown={handleKeyDown}
          role="combobox"
          aria-expanded={results.length > 0}
          aria-controls="search-results-listbox"
          aria-activedescendant={activeIndex >= 0 && results[activeIndex] ? `search-option-${results[activeIndex].id}` : undefined}
          placeholder="Search for games..."
          style={{
            width: '100%',
            padding: isMobile ? '12px 16px' : '14px 18px',
            // Add extra right padding so the loading text doesn't overlap typed text
            paddingRight: isMobile ? '56px' : '64px',
            borderRadius: '25px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            background: 'rgba(255, 255, 255, 0.15)',
            boxSizing: 'border-box',
            color: '#fff',
            fontSize: isMobile ? '14px' : '16px',
            outline: 'none',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
            transition: 'all 0.3s ease'
          }}
          onFocus={(e) => {
            e.target.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.2)';
            // Unlock audio on first user interaction
            try { sfx.unlock(); } catch {}
          }}
          onBlur={(e) => e.target.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)'}
        />
        {loading && (
          <div style={{
            position: 'absolute',
            right: isMobile ? '52px' : '60px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: '#fff',
            fontSize: isMobile ? '12px' : '13px',
            pointerEvents: 'none'
          }}>
            Searching...
          </div>
        )}
        <button
          type="button"
          onClick={isListening ? stopListening : startListening}
          aria-pressed={isListening}
          disabled={!isSpeechSupported}
          title={isSpeechSupported ? (isListening ? 'Stop voice input' : 'Voice search') : 'Voice input not supported in this browser'}
          style={{
            position: 'absolute',
            right: '8px',
            top: '50%',
            transform: 'translateY(-50%)',
            border: '1px solid rgba(255,255,255,0.35)',
            background: isListening ? 'rgba(14,165,233,0.85)' : 'rgba(255,255,255,0.2)',
            color: '#fff',
            width: isMobile ? 32 : 36,
            height: isMobile ? 32 : 36,
            padding: 0,
            borderRadius: '50%',
            cursor: isSpeechSupported ? 'pointer' : 'not-allowed',
            fontSize: '16px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <span aria-hidden="true">🎤</span>
        </button>
      </div>
      {/* Filter toggle moved to App-level options bar */}
      {results.length > 0 && (
        <ul role="listbox" id="search-results-listbox" style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          left: 0,
          right: 0,
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '15px',
          listStyle: 'none',
          padding: '8px 0',
          margin: 0,
          zIndex: 1000,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          maxHeight: isMobile ? '200px' : '250px',
          overflowY: 'auto'
        }}>
          {resultsList}
        </ul>
      )}
    </div>
  );
});

export default SearchBar;
