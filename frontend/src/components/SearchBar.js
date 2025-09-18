import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { debounce } from 'lodash';

const SearchBar = React.memo(({ onGameSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const debouncedSearch = useMemo(
    () => debounce((q) => {
      if (q.length < 2) {
        setResults([]);
        return;
      }
      setLoading(true);
      axios.get('http://localhost:8000/api/games/search', { params: { q } })
        .then(response => {
          setResults(response.data);
        })
        .catch(error => {
          console.error('Search error:', error);
          setResults([]);
        })
        .finally(() => {
          setLoading(false);
        });
    }, 300), // Reduced debounce time for better responsiveness
    []
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
        padding: '12px 18px',
        cursor: 'pointer',
        borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
        transition: 'background 0.2s ease',
        color: '#333',
        fontSize: '15px'
      }}
      onMouseEnter={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.8)'}
      onMouseLeave={(e) => e.target.style.background = 'transparent'}
    >
      <strong style={{ color: '#000', fontSize: '16px' }}>{game.title || 'Unknown Game'}</strong><br />
      <small style={{ color: '#666', fontSize: '13px' }}>
        {game.generation ? `Generation ${game.generation}` : 'Unknown Generation'} • {game.platform || 'Unknown Platform'}
      </small>
    </li>
  )), [results, handleSelect]);

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: '500px' }}>
      <style>
        {`input::placeholder { color: white; }`}
      </style>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search for games..."
        style={{
          width: '100%',
          padding: '14px 18px',
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
          right: '18px',
          top: '50%',
          transform: 'translateY(-50%)',
          color: '#fff',
          fontSize: '13px'
        }}>
          Searching...
        </div>
      )}
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