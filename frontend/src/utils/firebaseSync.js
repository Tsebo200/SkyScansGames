import { auth, db, onAuthStateChanged } from '../firebase';
import { doc, getDoc, setDoc, updateDoc, serverTimestamp } from 'firebase/firestore';

// Merge local settings from localStorage/state with remote Firestore profile
export function initSettingsSync({ getLocal, applyLocal, onUserChange } = {}) {
  let unsubscribe = null;
  const stop = onAuthStateChanged(auth, async (user) => {
    try { onUserChange?.(user); } catch {}
    if (!user) return; // Stay local-only when signed out

    const ref = doc(db, 'users', user.uid);
    const snap = await getDoc(ref);
    if (snap.exists()) {
      // Apply remote -> local (authoritative on first load)
      const data = snap.data() || {};
      try { applyLocal?.(data.settings || {}); } catch {}
    } else {
      // First time: create with local defaults if available
      const local = getLocal?.() || {};
      await setDoc(ref, { settings: local, createdAt: serverTimestamp(), updatedAt: serverTimestamp() });
    }
  });
  unsubscribe = stop;

  return {
    async push(localSettings) {
      const user = auth.currentUser;
      if (!user) return;
      const ref = doc(db, 'users', user.uid);
      try {
        await updateDoc(ref, { settings: localSettings, updatedAt: serverTimestamp() });
      } catch (e) {
        // If doc missing, create
        await setDoc(ref, { settings: localSettings, createdAt: serverTimestamp(), updatedAt: serverTimestamp() });
      }
    },
    dispose() { try { unsubscribe?.(); } catch {} }
  };
}
