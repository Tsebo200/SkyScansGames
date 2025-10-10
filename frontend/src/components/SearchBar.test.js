import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import SearchBar from './SearchBar';

jest.mock('axios', () => ({
  __esModule: true,
  default: { get: jest.fn() },
  get: jest.fn(),
}));

describe('SearchBar hideVariants filtering', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    axios.get.mockReset();
  });
  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  const results = [
    { id: 1, title: 'Game XYZ Deluxe Edition', platform: 'PC' },
    { id: 2, title: 'Game XYZ', platform: 'PC' },
    { id: 3, title: 'My DLC Thing', platform: 'PC' },
  ];

  test('filters out DLC/editions/spinoffs when hideVariants is true, and includes them when false', async () => {
  axios.get.mockResolvedValue({ data: results });

    const onGameSelect = jest.fn();
    const onChangeHideVariants = jest.fn();
    const { rerender } = render(
      <SearchBar onGameSelect={onGameSelect} hideVariants={true} onChangeHideVariants={onChangeHideVariants} />
    );

    const input = screen.getByPlaceholderText('Search for games...');
    fireEvent.change(input, { target: { value: 'Game' } });

    // advance debounce time
  await act(async () => { jest.advanceTimersByTime(350); });

    // wait for base title to appear
    await waitFor(() => expect(screen.getByText('Game XYZ')).toBeInTheDocument());
    // variant titles should be hidden
    expect(screen.queryByText('Game XYZ Deluxe Edition')).not.toBeInTheDocument();
    expect(screen.queryByText('My DLC Thing')).not.toBeInTheDocument();

    // Now rerender with hideVariants = false and ensure variants are included
    rerender(
      <SearchBar onGameSelect={onGameSelect} hideVariants={false} onChangeHideVariants={onChangeHideVariants} />
    );

    // trigger debounce effect due to dependency change
    await act(async () => { jest.advanceTimersByTime(350); });

  // With hideVariants off and dedupe keeping first seen key, the edition can replace base
  await waitFor(() => expect(screen.getByText('Game XYZ Deluxe Edition')).toBeInTheDocument());
  // Depending on server search behavior, DLC may also appear (mock returns it regardless of q)
  expect(screen.getByText('My DLC Thing')).toBeInTheDocument();
  });
});
