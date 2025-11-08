// Lightweight sound effects via Web Audio API. Gracefully no-op when unavailable.
let ctx = null;
let unlocked = false;

const getCtx = () => {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    if (!ctx) ctx = new AC();
    // Best effort resume (needed after user gesture on some browsers)
    if (ctx.state === 'suspended') ctx.resume?.();
    unlocked = true;
    return ctx;
  } catch {
    return null;
  }
};

// Basic beep helper
const beep = (opts = {}) => {
  const {
    type = 'sine',
    freq = 440,
    duration = 0.15,
    gain = 0.04,
    attack = 0.005,
    decay = 0.02,
    startTime = 0
  } = opts;
  const c = getCtx();
  if (!c) return;
  const t0 = c.currentTime + startTime;
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = type;
  o.frequency.value = freq;
  g.gain.setValueAtTime(0, t0);
  g.gain.linearRampToValueAtTime(gain, t0 + attack);
  g.gain.exponentialRampToValueAtTime(Math.max(1e-4, gain * 0.001), t0 + Math.max(attack + 0.001, duration - decay));
  g.gain.setValueAtTime(Math.max(1e-4, gain * 0.001), t0 + duration);
  o.connect(g).connect(c.destination);
  o.start(t0);
  o.stop(t0 + duration + 0.01);
};

// Sequences
const arpeggio = (base = 440, steps = [0, 4, 7, 12], gap = 0.06, opt = {}) => {
  steps.forEach((s, i) => beep({ freq: base * Math.pow(2, s / 12), startTime: i * gap, ...opt }));
};

export const sfx = {
  // Call this on a direct user gesture (e.g., search click) to ensure audio unlock
  unlock: () => { getCtx(); },
  scanStart: () => {
    // Subtle rising up-sweep
    arpeggio(370, [0, 3, 7], 0.07, { type: 'sine', gain: 0.035, duration: 0.12 });
  },
  scanDone: () => {
    // Pleasant confirmation chime
    arpeggio(523.25, [0, 7, 12], 0.08, { type: 'triangle', gain: 0.045, duration: 0.14 });
  },
  scoreReveal: () => {
    // Short sparkle
    arpeggio(659.25, [0, 5, 9, 12], 0.05, { type: 'sine', gain: 0.035, duration: 0.10 });
  },
  recommendation: () => {
    // Soft notification ping
    beep({ type: 'sine', freq: 880, gain: 0.03, duration: 0.12 });
    beep({ type: 'sine', freq: 1174.66, gain: 0.025, duration: 0.10, startTime: 0.08 });
  }
};

export default sfx;
