import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

// Mock axios globally to avoid ESM transform issues in Jest environment
jest.mock('axios', () => ({
  __esModule: true,
  default: { post: jest.fn(() => Promise.resolve({ data: { scores: null } })) },
}));

// Mock SearchBar to expose a simple button that selects a test game
jest.mock('./components/SearchBar', () => {
  const React = require('react');
  const TestSearch = ({ onGameSelect }) => (
    <button onClick={() => onGameSelect({ id: 1, title: 'Test Game', cover_image: 'https://example.com/cover.jpg' })}>
      Select Game
    </button>
  );
  return { __esModule: true, default: TestSearch };
});

test('renders app title', () => {
  render(<App />);
  const title = screen.getByText(/SkyScansGames/i);
  expect(title).toBeInTheDocument();
});

test('clicking floating bubble opens the game preview modal', async () => {
  const user = userEvent;
  const axios = (await import('axios')).default;
  // Return minimal valid scores so ScoreDashboard renders
  axios.post.mockResolvedValueOnce({ data: { scores: { overall_score: 82, reasoning: {} } } });

  render(<App />);

  // Trigger selecting a game via mocked SearchBar
  await user.click(screen.getByRole('button', { name: /select game/i }));

  // The floating bubble becomes a button when a game is selected
  const bubble = await screen.findByRole('button', { name: /open game details/i });
  await user.click(bubble);

  // Modal should open; look for Overview tab
  const overview = await screen.findByRole('tab', { name: /overview/i });
  expect(overview).toBeInTheDocument();
});
