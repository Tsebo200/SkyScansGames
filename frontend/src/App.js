import React, { useState, useCallback, Suspense, lazy } from 'react';
import axios from 'axios';
import './App.css';

// Lazy load components for better performance
const SearchBar = lazy(() => import('./components/SearchBar'));
const ScoreDashboard = lazy(() => import('./components/ScoreDashboard'));

const App = React.memo(() => {
  const [selectedGame, setSelectedGame] = useState(null);
  const [scores, setScores] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGameSelect = useCallback(async (game) => {
    setSelectedGame(game);
    setLoading(true);
    try {
      const response = await axios.post(`http://localhost:8000/api/games/${game.id}/scan`);
      setScores(response.data.scores);
    } catch (error) {
      console.error('Scan error:', error);
    }
    setLoading(false);
  }, []);

  return (
    <div className="App" style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Reduced number of floating orbs and optimized animations */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '10%',
        width: '150px',
        height: '150px',
        background: 'rgba(255, 255, 255, 0.08)',
        borderRadius: '50%',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        animation: 'float 8s ease-in-out infinite',
        pointerEvents: 'none'
      }}>
        {selectedGame?.cover_image && (
          <img
            src={selectedGame.cover_image}
            alt={`${selectedGame.title} cover`}
            style={{
              width: 56,
              height: 56,
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
        bottom: '20%',
        left: '70%',
        width: '120px',
        height: '120px',
        background: 'rgba(255, 255, 255, 0.06)',
        borderRadius: '50%',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        animation: 'float 12s ease-in-out infinite reverse',
        pointerEvents: 'none'
      }}>
        {selectedGame?.cover_image && (
          <img
            src={selectedGame.cover_image}
            alt={`${selectedGame.title} cover`}
            style={{
              width: 44,
              height: 44,
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
        zIndex: 1,
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <h1 style={{
          color: '#fff',
          textAlign: 'center',
          marginBottom: '30px',
          fontSize: '3rem',
          fontWeight: '300',
          textShadow: '0 0 20px rgba(255, 255, 255, 0.5)',
          background: 'rgba(255, 255, 255, 0.1)',
          padding: '20px',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          display: 'inline-block'
        }}>
          SkyScansGames
        </h1>

        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '40px'
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
            <SearchBar onGameSelect={handleGameSelect} />
          </Suspense>
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
            <ScoreDashboard scores={scores} game={selectedGame} />
          </Suspense>
        )}
      </div>
    </div>
  );
});

export default App;
