import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { debounce } from 'lodash';

const SearchBar = React.memo(({ onGameSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hideVariants, setHideVariants] = useState(true);

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
      axios.get('http://localhost:8000/api/games/search', { params: { q } })
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
    return () => debouncedSearch.cancel();
  }, [query, debouncedSearch]);

  const handleSelect = useCallback((game) => {
    onGameSelect(game);
    setQuery('');
    setResults([]);
  }, [onGameSelect]);

  // Memoize the results list to prevent unnecessary re-renders
  const resultsList = useMemo(() => results.map(game => (
    <li
      key={game.id}
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
        fontSize: '15px'
      }}
      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.8)'}
      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
    >
      {game.cover_image && (
        <img
          src={game.cover_image}
          alt={game.title}
          style={{
            width: '48px',
            height: '48px',
            objectFit: 'cover',
            borderRadius: '8px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.15)'
          }}
          loading="lazy"
        />
      )}
      <div style={{ flex: 1 }}>
        <strong style={{ color: '#000', fontSize: '16px', display: 'block' }}>{game.title || 'Unknown Game'}</strong>
        <small style={{ color: '#666', fontSize: '13px', display:'block' }}>
          {game.generation ? `Generation ${game.generation}` : 'Unknown Generation'} • {game.platform || 'Unknown Platform'}
        </small>
        {Array.isArray(game.platforms) && game.platforms.length > 0 && (
          <small style={{ color: '#888', fontSize: '12px', display:'block', marginTop:'2px' }}>
            {game.platforms.slice(0, 6).join(', ')}{game.platforms.length > 6 ? '…' : ''}
          </small>
        )}
      </div>
    </li>
  )), [results, handleSelect]);

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: '500px' }}>
      <style>
        {`input::placeholder { color: white; }`}
      </style>
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for games..."
          style={{
            width: '100%',
            padding: '14px 18px',
            // Add extra right padding so the loading text doesn't overlap typed text
            paddingRight: '96px',
            borderRadius: '25px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            background: 'rgba(255, 255, 255, 0.15)',
            color: '#fff',
            fontSize: '16px',
            outline: 'none',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
            transition: 'all 0.3s ease'
          }}
          onFocus={(e) => e.target.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.2)'}
          onBlur={(e) => e.target.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)'}
        />
        {loading && (
          <div style={{
            position: 'absolute',
            right: '-30px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: '#fff',
            fontSize: '13px',
            pointerEvents: 'none'
          }}>
            Searching...
          </div>
        )}
      </div>
      {/* Filter toggle */}
      <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontSize: '13px' }}>
        <input id="hide-variants" type="checkbox" checked={hideVariants} onChange={(e) => setHideVariants(e.target.checked)} />
        <label htmlFor="hide-variants">Hide DLC/editions/spinoffs</label>
      </div>
      {results.length > 0 && (
        <ul style={{
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
          maxHeight: '250px',
          overflowY: 'auto'
        }}>
          {resultsList}
        </ul>
      )}
    </div>
  );
});

export default SearchBar;