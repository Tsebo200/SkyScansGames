// Simple helpers to call the backend rewrite endpoints with tone presets
// NOTE: The brutal tone string is intentionally locked. Do not change the wording.
const API_BASE = typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_BASE
  ? process.env.REACT_APP_API_BASE.replace(/\/$/, '')
  : '';
// Do not change this exact string – tests rely on it.
export const BRUTAL_TONE_STYLE = 'brutally honest, candid, no fluff';
export const toneStyles = {
  casual: 'casual gamer vibes',
  meme: 'high meme energy',
  streamer: 'streamer commentary style',
  discord: 'Discord chat energy with emojis',
  brutal: BRUTAL_TONE_STYLE
};

export async function rewriteText(text, tone = 'casual', context = null) {
  try {
  const resp = await fetch(`${API_BASE}/api/text/rewrite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, tone, ...(context || {}) })
    });
  if (!resp.ok) throw new Error(`rewrite failed: ${resp.status}`);
    const data = await resp.json();
    return {
      text: data?.text ?? text,
      provider: data?.provider ?? 'unknown',
      used_model: data?.used_model ?? null
    };
  } catch (e) {
    // Fallback: return original text when API not available or fails
    return { text, provider: 'fallback', used_model: null };
  }
}

// Batch rewrite: accepts an array of { key, text } and returns { mapping, provider, used_model }
export async function rewriteBatch(items, tone = 'casual', context = null) {
  try {
    const resp = await fetch(`${API_BASE}/api/text/rewrite-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tone, items, ...(context || {}) })
    });
    if (!resp.ok) throw new Error(`batch rewrite failed: ${resp.status}`);
    const data = await resp.json();
    // Normalize to a simple mapping for convenience
    const mapping = {};
    if (Array.isArray(data?.items)) {
      for (const it of data.items) {
        if (it && typeof it.key === 'string') mapping[it.key] = it.text;
      }
    }
    return { mapping, provider: data?.provider ?? 'unknown', used_model: data?.used_model ?? null };
  } catch (e) {
    // Fallback: return a mapping that preserves the original texts
    const mapping = {};
    if (Array.isArray(items)) {
      for (const it of items) {
        if (it && typeof it.key === 'string') mapping[it.key] = it.text;
      }
    }
    return { mapping, provider: 'fallback', used_model: null };
  }
}
