// Firebase app initialization. Replace with your project's config.
// You can set these via environment variables (REACT_APP_*), or inline for local dev.
import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged as _onAuthStateChanged, setPersistence, browserLocalPersistence } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';


const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID
};

let storage = null;
let app = null;
let auth = null;
let db = null;
let onAuthStateChanged = (_ignored, cb) => { try { cb(null); } catch {} return () => {}; };

const hasConfig = !!(firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId && firebaseConfig.appId);
if (process.env.NODE_ENV !== 'test' && hasConfig) {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  setPersistence(auth, browserLocalPersistence).catch(() => {});
  db = getFirestore(app);
  storage = getStorage(app); // <-- add this line
  onAuthStateChanged = _onAuthStateChanged;
}

export { app, auth, db, storage, onAuthStateChanged };
