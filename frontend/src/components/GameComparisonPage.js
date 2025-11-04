import React, { useState } from 'react';

// Dummy data for demonstration
const games = [
  {
    id: 1,
    name: 'Game One',
    genre: 'Action',
    rating: 8.5,
    platform: 'PC',
    release: '2024-05-10',
    trailer: 'https://www.youtube.com/embed/dummy1',
    screenshots: [
      'https://via.placeholder.com/300x180?text=Game+One+1',
      'https://via.placeholder.com/300x180?text=Game+One+2'
    ]
  },
  {
    id: 2,
    name: 'Game Two',
    genre: 'RPG',
    rating: 9.1,
    platform: 'PS5',
    release: '2025-02-20',
    trailer: 'https://www.youtube.com/embed/dummy2',
    screenshots: [
      'https://via.placeholder.com/300x180?text=Game+Two+1',
      'https://via.placeholder.com/300x180?text=Game+Two+2'
    ]
  }
];

export default function GameComparisonPage() {
  const [selected, setSelected] = useState(games[0].id);
  const game = games.find(g => g.id === selected);

  return (
    <div style={{ padding: 24, color: '#fff' }}>
      <h2>Compare Games</h2>
      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        {games.map(g => (
          <button
            key={g.id}
            onClick={() => setSelected(g.id)}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              background: selected === g.id ? '#38bdf8' : '#222',
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            {g.name}
          </button>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 32 }}>
        <div>
          <h3>{game.name}</h3>
          <p><strong>Genre:</strong> {game.genre}</p>
          <p><strong>Rating:</strong> {game.rating}</p>
          <p><strong>Platform:</strong> {game.platform}</p>
          <p><strong>Release Date:</strong> {game.release}</p>
        </div>
        <div>
          <h4>Trailer</h4>
          <iframe width="320" height="180" src={game.trailer} title="Trailer" frameBorder="0" allowFullScreen />
          <h4>Screenshots</h4>
          <div style={{ display: 'flex', gap: 8 }}>
            {game.screenshots.map((src, i) => (
              <img key={i} src={src} alt={`Screenshot ${i+1}`} style={{ width: 120, borderRadius: 8 }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
