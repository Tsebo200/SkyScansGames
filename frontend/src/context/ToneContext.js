import React, { createContext, useContext, useMemo, useState } from 'react';

const ToneContext = createContext({ tone: 'casual', setTone: () => {} });

export function ToneProvider({ children, initialTone = 'casual' }) {
  const [tone, setTone] = useState(initialTone);
  const value = useMemo(() => ({ tone, setTone }), [tone]);
  return (
    <ToneContext.Provider value={value}>
      {children}
    </ToneContext.Provider>
  );
}

export function useTone() {
  return useContext(ToneContext);
}

export { ToneContext };
