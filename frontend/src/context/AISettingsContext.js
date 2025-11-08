import React, { createContext, useContext, useMemo, useCallback, useState, useEffect } from 'react';
import { auth, db, onAuthStateChanged } from '../firebase';
import { doc, getDoc, setDoc, updateDoc, serverTimestamp } from 'firebase/firestore';

const KEY = 'aiFeedbackEnabled';

const AISettingsContext = createContext({
  aiFeedbackEnabled: false,
  setAIWebhook: () => {},
  setAIFeedbackEnabled: () => {}
});

export function AISettingsProvider({ children }) {
  const [aiFeedbackEnabled, setEnabled] = useState(true);
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY);
      if (saved != null) setEnabled(saved === 'true');
    } catch {}
  }, []);

  // Firebase load
  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (user) => {
      setUserId(user ? user.uid : null);
      if (!user) return;
      const ref = doc(db, 'users', user.uid);
      const snap = await getDoc(ref);
      if (snap.exists()) {
        const data = snap.data();
        const remote = data?.settings?.aiFeedbackEnabled;
        if (typeof remote === 'boolean') setEnabled(remote);
      } else {
        // Initialise with current local value
        await setDoc(ref, { settings: { aiFeedbackEnabled: true }, createdAt: serverTimestamp(), updatedAt: serverTimestamp() }, { merge: true });
      }
    });
    return () => unsub();
  }, []);

  const setAIFeedbackEnabled = useCallback((val) => {
    setEnabled(val);
    try { localStorage.setItem(KEY, String(val)); } catch {}
    // Push remote
    try {
      if (userId) {
        const ref = doc(db, 'users', userId);
        updateDoc(ref, { 'settings.aiFeedbackEnabled': val, updatedAt: serverTimestamp() }).catch(async () => {
          await setDoc(ref, { settings: { aiFeedbackEnabled: val }, createdAt: serverTimestamp(), updatedAt: serverTimestamp() }, { merge: true });
        });
      }
    } catch {}
  }, []);

  const value = useMemo(() => ({ aiFeedbackEnabled, setAIFeedbackEnabled }), [aiFeedbackEnabled, setAIFeedbackEnabled]);
  return <AISettingsContext.Provider value={value}>{children}</AISettingsContext.Provider>;
}

export function useAISettings() {
  return useContext(AISettingsContext);
}
