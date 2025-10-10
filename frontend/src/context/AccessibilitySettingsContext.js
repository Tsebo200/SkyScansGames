import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { initSettingsSync } from '../utils/firebaseSync';

const AccessibilitySettingsContext = createContext({
  colorVision: 'normal',
  setColorVision: () => {},
  reduceMotion: false,
  setReduceMotion: () => {},
  highContrast: false,
  setHighContrast: () => {},
  fontSize: 'medium', // small | medium | large
  setFontSize: () => {},
  theme: 'dark', // dark | light
  setTheme: () => {},
});

const STORAGE_KEY = 'skyscans.accessibility';

export const AccessibilitySettingsProvider = ({ children }) => {
  const [state, setState] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch {}
    return { colorVision: 'normal', reduceMotion: false, highContrast: false, fontSize: 'medium', theme: 'dark' };
  });

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
    // Push to Firebase if authenticated
    try { syncRef?.push?.(state); } catch {}
  }, [state]);

  const [syncRef, setSyncRef] = useState(null);
  useEffect(() => {
    const ref = initSettingsSync({
      getLocal: () => state,
      applyLocal: (remote) => setState(s => ({ ...s, ...remote })),
    });
    setSyncRef(ref);
    return () => ref?.dispose?.();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo(() => ({
    colorVision: state.colorVision,
    setColorVision: (v) => setState(s => ({ ...s, colorVision: v })),
    reduceMotion: !!state.reduceMotion,
    setReduceMotion: (v) => setState(s => ({ ...s, reduceMotion: !!v })),
    highContrast: !!state.highContrast,
    setHighContrast: (v) => setState(s => ({ ...s, highContrast: !!v })),
    fontSize: state.fontSize || 'medium',
    setFontSize: (v) => setState(s => ({ ...s, fontSize: v })),
    theme: state.theme || 'dark',
    setTheme: (v) => setState(s => ({ ...s, theme: v }))
  }), [state]);
  return (
    <AccessibilitySettingsContext.Provider value={value}>
      {children}
    </AccessibilitySettingsContext.Provider>
  );
};

export const useAccessibilitySettings = () => useContext(AccessibilitySettingsContext);
