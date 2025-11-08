chBar.js
(venv) [root@skyscansgames components]# rm SearchBar.js
rm: remove regular file 'SearchBar.js'? y
(venv) [root@skyscansgames components]# ls -la SearchBar.js
ls: cannot access 'SearchBar.js': No such file or directory
(venv) [root@skyscansgames components]# nano SearchBar.js
(venv) [root@skyscansgames components]# cd ..
(venv) [root@skyscansgames src]# cd ..
(venv) [root@skyscansgames frontend]# npm run build

> frontend@0.1.0 build
> react-scripts build

Creating an optimized production build...
Failed to compile.

SyntaxError: /root/SkyScansGames/frontend/src/App.js: Unexpected token (370:7)
  368 |         {/* If user clicked bubble before scores loaded, open preview as soon as scores are ready */}
  369 |         {/* queued preview opening handl(venv) [root@skyscansgames frontend]# cd /root/SkyScansGames/frontend/src/components
(venv) [root@skyscansgames components]# nano SearchBar.js
(venv) [root@skyscansgames components]# m /root/SkyScansGames/frontend/src/components/SearchBar.js
-bash: m: command not found
(venv) [root@skyscansgames components]# rm /var/www/SkyScansGames/frontend/src/components/SearchBar.js
rm: cannot remove '/var/www/SkyScansGames/frontend/src/components/SearchBar.js': No such file or directory
(venv) [root@skyscansgames components]# pwd
/root/SkyScansGames/frontend/src/components
(venv) [root@skyscansgames components]# s -la SearchBar.js
-bash: s: command not found
(venv) [root@skyscansgames components]# ls -la SearchBar.js
-rwxr-xr-x. 1 root root 12373 Nov  8 15:46 Seared via useEffect above */}
> 370 |       </div>
      |        ^
  371 |       <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
  372 |     </div>
  373 |   );


(venv) [root@skyscansgames frontend]# cd /root/SkyScansGames/frontend/src
rm App.js
rm: remove regular file 'App.js'? y
(venv) [root@skyscansgames src]# nano App.js
(venv) [root@skyscansgames src]# cd ..
(venv) [root@skyscansgames frontend]# npm run build

> frontend@0.1.0 build
> react-scripts build

Creating an optimized production build...
Compiled with warnings.

[eslint]
src/components/ScoreDashboard.js
  Line 234:6:   React Hook useCallback has a missing dependency: 'buildSubscores'. Either include it or remove the dependency array                                                                                                   react-hooks/exhaustive-deps
  Line 333:9:   The 'rc' conditional could make the dependencies of useMemo Hook (at line 342) change on every render. Move it inside the useMemo callback. Alternatively, wrap the initialization of 'rc' in its own useMemo() Hook  react-hooks/exhaustive-deps
  Line 345:10:  'telemetry' is assigned a value but never used                                                                                                                                                                        no-unused-vars
  Line 346:10:  'telemetryLoading' is assigned a value but never used
                                          no-unused-vars
  Line 347:10:  'telemetryError' is assigned a value but never used                                                                                                                                                                   no-unused-vars
  Line 364:9:   'infoItems' is assigned a value but never used                                                                                                                                                                        no-unused-vars

src/components/SearchBar.js
  Line 19:9:  'setHideVariants' is assigned a value but never used  no-unused-vars

src/components/Switch.js
  Line 45:43:  Unnecessary escape character: \,  no-useless-escape

src/context/AISettingsContext.js
  Line 55:6:  React Hook useCallback has a missing dependency: 'userId'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/context/AccessibilitySettingsContext.js
  Line 32:6:  React Hook useEffect has a missing dependency: 'syncRef'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/utils/sfx.js
  Line 3:5:  'unlocked' is assigned a value but never used  no-unused-vars

Search for the keywords to learn more about each warning.
To ignore, add // eslint-disable-next-line to the line before.

File sizes after gzip:

  191.45 kB  build/static/js/main.039cf047.js
  24.81 kB   build/static/js/536.6abca2b2.chunk.js
  12.2 kB    build/static/js/397.7061c883.chunk.js
  2.92 kB    build/static/js/684.a56b6337.chunk.js
  1.76 kB    build/static/js/453.670e15c7.chunk.js
  392 B      build/static/css/main.dc32f9ca.css

The project was built assuming it is hosted at /.
You can control this with the homepage field in your package.json.

The build folder is ready to be deployed.
You may serve it with a static server:

  npm install -g serve
  serve -s build

Find out more about deployment here:

  https://cra.link/deployment

(venv) [root@skyscansgames frontend]# cd /root/SkyScansGames/frontend/src
rm App.js
nano App.js
rm: remove regular file 'App.js'? y
(venv) [root@skyscansgames src]# cd ..
(venv) [root@skyscansgames frontend]# npm run build

> frontend@0.1.0 build
> react-scripts build

Creating an optimized production build...
Compiled with warnings.

[eslint]
src/components/ScoreDashboard.js
  Line 234:6:   React Hook useCallback has a missing dependency: 'buildSubscores'. Either include it or remove the dependency array                                                                                                   react-hooks/exhaustive-deps
  Line 333:9:   The 'rc' conditional could make the dependencies of useMemo Hook (at line 342) change on every render. Move it inside the useMemo callback. Alternatively, wrap the initialization of 'rc' in its own useMemo() Hook  react-hooks/exhaustive-deps
  Line 345:10:  'telemetry' is assigned a value but never used
                                          no-unused-vars
  Line 346:10:  'telemetryLoading' is assigned a value but never used                                                                                                                                                                 no-unused-vars
  Line 347:10:  'telemetryError' is assigned a value but never used                                                                                                                                                                   no-unused-vars
  Line 364:9:   'infoItems' is assigned a value but never used                                                                                                                                                                        no-unused-vars

src/components/SearchBar.js
  Line 19:9:  'setHideVariants' is assigned a value but never used  no-unused-vars

src/components/Switch.js
  Line 45:43:  Unnecessary escape character: \,  no-useless-escape

src/context/AISettingsContext.js
  Line 55:6:  React Hook useCallback has a missing dependency: 'userId'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/context/AccessibilitySettingsContext.js
  Line 32:6:  React Hook useEffect has a missing dependency: 'syncRef'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/utils/sfx.js
  Line 3:5:  'unlocked' is assigned a value but never used  no-unused-vars

Search for the keywords to learn more about each warning.
To ignore, add // eslint-disable-next-line to the line before.

File sizes after gzip:

  191.48 kB (+27 B)  build/static/js/main.157426c9.js
  24.81 kB           build/static/js/536.6abca2b2.chunk.js
  12.2 kB            build/static/js/397.7061c883.chunk.js
  2.92 kB            build/static/js/684.a56b6337.chunk.js
  1.76 kB            build/static/js/453.670e15c7.chunk.js
  392 B              build/static/css/main.dc32f9ca.css

The project was built assuming it is hosted at /.
You can control this with the homepage field in your package.json.

The build folder is ready to be deployed.
You may serve it with a static server:

  npm install -g serve
  serve -s build

Find out more about deployment here:

  https://cra.link/deployment

(venv) [root@skyscansgames frontend]# nano App.js
(venv) [root@skyscansgames frontend]# npm run build

> frontend@0.1.0 build
> react-scripts build

Creating an optimized production build...
Compiled with warnings.

[eslint]
src/components/ScoreDashboard.js
  Line 234:6:   React Hook useCallback has a missing dependency: 'buildSubscores'. Either include it or remove the dependency array                                                                                                   react-hooks/exhaustive-deps
  Line 333:9:   The 'rc' conditional could make the dependencies of useMemo Hook (at line 342) change on every render. Move it inside the useMemo callback. Alternatively, wrap the initialization of 'rc' in its own useMemo() Hook  react-hooks/exhaustive-deps
  Line 345:10:  'telemetry' is assigned a value but never used                                                                                                                                                                        no-unused-vars
  Line 346:10:  'telemetryLoading' is assigned a value but never used
                                                                                                                                        no-unused-vars
  Line 347:10:  'telemetryError' is assigned a value but never used                                                                                                                                                                   no-unused-vars
  Line 364:9:   'infoItems' is assigned a value but never used                                                                                                                                                                        no-unused-vars

src/components/SearchBar.js
  Line 19:9:  'setHideVariants' is assigned a value but never used  no-unused-vars

src/components/Switch.js
  Line 45:43:  Unnecessary escape character: \,  no-useless-escape

src/context/AISettingsContext.js
  Line 55:6:  React Hook useCallback has a missing dependency: 'userId'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/context/AccessibilitySettingsContext.js
  Line 32:6:  React Hook useEffect has a missing dependency: 'syncRef'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/utils/sfx.js
  Line 3:5:  'unlocked' is assigned a value but never used  no-unused-vars

Search for the keywords to learn more about each warning.
To ignore, add // eslint-disable-next-line to the line before.

File sizes after gzip:

  191.48 kB  build/static/js/main.157426c9.js
  24.81 kB   build/static/js/536.6abca2b2.chunk.js
  12.2 kB    build/static/js/397.7061c883.chunk.js
  2.92 kB    build/static/js/684.a56b6337.chunk.js
  1.76 kB    build/static/js/453.670e15c7.chunk.js
  392 B      build/static/css/main.dc32f9ca.css

The project was built assuming it is hosted at /.
You can control this with the homepage field in your package.json.

The build folder is ready to be deployed.
You may serve it with a static server:

  npm install -g serve
  serve -s build

Find out more about deployment here:

  https://cra.link/deployment

(venv) [root@skyscansgames frontend]# systemctl reload nginx
(venv) [root@skyscansgames frontend]# nano App.js
(venv) [root@skyscansgames frontend]# nano SearchBar.js
(venv) [root@skyscansgames frontend]# npm run build

> frontend@0.1.0 build
> react-scripts build

Creating an optimized production build...
Compiled with warnings.

[eslint]
src/components/ScoreDashboard.js
  Line 234:6:   React Hook useCallback has a missing dependency: 'buildSubscores'. Either include it or remove the dependency array                                                                                                   react-hooks/exhaustive-deps
  Line 333:9:   The 'rc' conditional could make the dependencies of useMemo Hook (at line 342) change on every render. Move it inside the useMemo callback. Alternatively, wrap the initialization of 'rc' in its own useMemo() Hook  react-hooks/exhaustive-deps
  Line 345:10:  'telemetry' is assigned a value but never used                                                                                                                                                                        no-unused-vars
  Line 346:10:  'telemetryLoading' is assigned a value but never used                                                                                                                                                                 no-unused-vars
  Line 347:10:  'telemetryError' is assigned a value but never used                                                                                                                                                                   no-unused-vars
  Line 364:9:   'infoItems' is assigned a value but never used                                                                                                                                                                        no-unused-vars

src/components/SearchBar.js
  Line 19:9:  'setHideVariants' is assigned a value but never used  no-unused-vars

src/components/Switch.js
  Line 45:43:  Unnecessary escape character: \,  no-useless-escape

src/context/AISettingsContext.js
  Line 55:6:  React Hook useCallback has a missing dependency: 'userId'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/context/AccessibilitySettingsContext.js
  Line 32:6:  React Hook useEffect has a missing dependency: 'syncRef'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/utils/sfx.js
  Line 3:5:  'unlocked' is assigned a value but never used  no-unused-vars

Search for the keywords to learn more about each warning.
To ignore, add // eslint-disable-next-line to the line before.

File sizes after gzip:

  191.48 kB  build/static/js/main.157426c9.js
  24.81 kB   build/static/js/536.6abca2b2.chunk.js
  12.2 kB    build/static/js/397.7061c883.chunk.js
  2.92 kB    build/static/js/684.a56b6337.chunk.js
  1.76 kB    build/static/js/453.670e15c7.chunk.js
  392 B      build/static/css/main.dc32f9ca.css

The project was built assuming it is hosted at /.
You can control this with the homepage field in your package.json.

The build folder is ready to be deployed.
You may serve it with a static server:

  npm install -g serve
  serve -s build

Find out more about deployment here:

  https://cra.link/deployment

(venv) [root@skyscansgames frontend]# systemctl reload nginx
(venv) [root@skyscansgames frontend]# nano SettingsModal.js
(venv) [root@skyscansgames frontend]# npm run build

> frontend@0.1.0 build
> react-scripts build

^[[ACreating an optimized production build...
Compiled with warnings.

[eslint]
src/components/ScoreDashboard.js
  Line 234:6:   React Hook useCallback has a missing dependency: 'buildSubscores'. Either include it or remove the dependency array                                                                                                   react-hooks/exhaustive-deps
  Line 333:9:   The 'rc' conditional could make the dependencies of useMemo Hook (at line 342) change on every render. Move it inside the useMemo callback. Alternatively, wrap the initialization of 'rc' in its own useMemo() Hook  react-hooks/exhaustive-deps
  Line 345:10:  'telemetry' is assigned a value but never used                                                                                                                                                                        no-unused-vars
  GNU nano 8.1                           SettingsModal.js
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAccessibilitySettings } from '../context/AccessibilitySettingsContext';

const SettingsModal = ({ open, onClose }) => {
  const { colorVision, setColorVision, reduceMotion, setReduceMotion, highContrast, setHighCo>

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return createPortal(
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 'min(720px, 95vw)', backgroun>
        <div style={{ display: 'flex', alignItems: 'center', padding: 14, borderBottom: '1px >
          <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#111827', fle>
          <button onClick={onClose} aria-label="Close settings" style={{ border: 'none', back>
        </div>
	<div style={{ padding: 16, display: 'grid', gap: 16 }}>
          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius:>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600 }}>Accessibil>
            <label htmlFor="colorVision" style={{ display: 'block', fontWeight: 600, color: '>
            <select id="colorVision" value={colorVision} onChange={(e) => setColorVision(e.ta>
              <option value="normal" style={{ color: '#0f172a' }}>Normal</option>
              <option value="deuteranopia" style={{ color: '#0f172a' }}>Deuteranopia (green-w>
              <option value="protanopia" style={{ color: '#0f172a' }}>Protanopia (red-weak)</>
              <option value="tritanopia" style={{ color: '#0f172a' }}>Tritanopia (blue-weak)<>
            </select>
            <p style={{ margin: '8px 0 0 0', color: '#475569', fontSize: '0.9rem' }}>We’ll ad>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius:>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600 }}>Motion & C>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer'>
              <input type="checkbox" checked={reduceMotion} onChange={(e) => setReduceMotion(>
              <span style={{ color: '#0f172a', fontWeight: 500 }}>Reduce motion/animations</s>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8, cur>
              <input type="checkbox" checked={highContrast} onChange={(e) => setHighContrast(>
              <span style={{ color: '#0f172a', fontWeight: 500 }}>High contrast mode</span>
            </label>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius:>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600 }}>Typography>
            <label htmlFor="fontSize" style={{ display: 'block', fontWeight: 600, color: '#0f>
                                      [ Read 74 lines ]
^G Help        ^O Write Out   ^F Where Is    ^K Cut         ^T Execute     ^C Location
^X Exit        ^R Read File   ^\ Replace     ^U Paste       ^J Justify     ^/ Go To Lineimport React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAccessibilitySettings } from '../context/AccessibilitySettingsContext';

const SettingsModal = ({ open, onClose }) => {
  const { colorVision, setColorVision, reduceMotion, setReduceMotion, highContrast, setHighContrast, fontSize, setFontSize, theme, setTheme } = useAccessibilitySettings();

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return createPortal(
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 'min(720px, 95vw)', background: 'rgba(255,255,255,0.98)', borderRadius: 16, border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 12px 36px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', padding: 14, borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#111827', flex: 1 }}>Settings</h3>
          <button onClick={onClose} aria-label="Close settings" style={{ border: 'none', background: 'transparent', fontSize: '1.5rem', cursor: 'pointer', color: '#6b7280' }}>×</button>
        </div>
        <div style={{ padding: 16, display: 'grid', gap: 16 }}>
          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600 }}>Accessibility</h4>
            <label htmlFor="colorVision" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>Color vision mode</label>
            <select id="colorVision" value={colorVision} onChange={(e) => setColorVision(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a', width: '100%', fontSize: '14px' }}>
              <option value="normal" style={{ color: '#0f172a' }}>Normal</option>
              <option value="deuteranopia" style={{ color: '#0f172a' }}>Deuteranopia (green-weak)</option>
              <option value="protanopia" style={{ color: '#0f172a' }}>Protanopia (red-weak)</option>
              <option value="tritanopia" style={{ color: '#0f172a' }}>Tritanopia (blue-weak)</option>
            </select>
            <p style={{ margin: '8px 0 0 0', color: '#475569', fontSize: '0.9rem' }}>We’ll adapt UI colours and contrasts to improve distinguishability for common colour-vision deficiencies.</p>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600 }}>Motion & Contrast</h4>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
              <input type="checkbox" checked={reduceMotion} onChange={(e) => setReduceMotion(e.target.checked)} style={{ cursor: 'pointer' }} />
              <span style={{ color: '#0f172a', fontWeight: 500 }}>Reduce motion/animations</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8, cursor: 'pointer' }}>
              <input type="checkbox" checked={highContrast} onChange={(e) => setHighContrast(e.target.checked)} style={{ cursor: 'pointer' }} />
              <span style={{ color: '#0f172a', fontWeight: 500 }}>High contrast mode</span>
            </label>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600 }}>Typography</h4>
            <label htmlFor="fontSize" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>Font size</label>
            <select id="fontSize" value={fontSize} onChange={(e) => setFontSize(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a', width: '100%', fontSize: '14px' }}>
              <option value="small" style={{ color: '#0f172a' }}>Small</option>
              <option value="medium" style={{ color: '#0f172a' }}>Medium</option>
              <option value="large" style={{ color: '#0f172a' }}>Large</option>
            </select>
          </section>

          <section style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#0f172a', fontWeight: 600 }}>Theme</h4>
            <label htmlFor="theme" style={{ display: 'block', fontWeight: 600, color: '#0f172a', marginBottom: 6 }}>Appearance</label>
            <select id="theme" value={theme} onChange={(e) => setTheme(e.target.value)} style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#fff', color: '#0f172a', width: '100%', fontSize: '14px' }}>
              <option value="dark" style={{ color: '#0f172a' }}>Dark</option>
              <option value="light" style={{ color: '#0f172a' }}>Light</option>
            </select>
          </section>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default SettingsModal;
