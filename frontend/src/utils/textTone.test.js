import { BRUTAL_TONE_STYLE, toneStyles } from './textTone';

// Lock the brutal tone wording to avoid accidental regressions
it('keeps brutal tone wording unchanged', () => {
  expect(BRUTAL_TONE_STYLE).toBe('brutally honest, candid, no fluff');
  expect(toneStyles.brutal).toBe(BRUTAL_TONE_STYLE);
});
