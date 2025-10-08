# SkyScans Games Demo — Dev Notes & Troubleshooting

This README documents the issues encountered while getting the project running, how we resolved them, and a concise, repeatable setup for macOS (zsh).

## Summary of key challenges and fixes

1) Python version mismatch (global 3.13.7 vs project venv 3.12)
- Symptoms: Backend wouldn’t start, inconsistent behavior; suspicion it was macOS update, but root cause was Python version drift.
- Root cause: Global Python was 3.13.7 while the project’s virtual environment and dependencies were set up for 3.12, causing env confusion and modules not loading.
- Resolution:
  - Uninstalled Python 3.13.7.
  - Installed Python 3.12 (3.12.11).
  - Updated zsh PATH so `python3` resolves to 3.12.
  - Deleted the project venv and recreated it with Python 3.12.11.

2) “Error loading ASGI app. Could not import module \"main\"”
- Cause: Running `uvicorn main:app` from the repository root instead of the `backend/` directory.
- Fix: Always start Uvicorn from `backend/` (so `main.py` is importable as `main`).

3) Port conflicts (“Address already in use” on 8000/8001)
- Cause: A prior Uvicorn instance was holding the port.
- Fix: `pkill -f "uvicorn main:app"` then start again; or run on a different port.

4) Missing dependencies (e.g., `requests`) and pip script issues
- Cause: Venv didn’t have all packages, or zsh executed the `pip` script with a shell exec error.
- Fix: Use `python -m pip install -r backend/requirements.txt` (invokes pip via Python), and prefer `python -m pip` for all package ops.

5) No logs / commands interleaving
- Cause: Running curl in the same terminal or hitting Ctrl+C while the server runs caused shutdown; reload mode restarts may also interleave logs.
- Fix: Start the server in its own terminal; run curls in another. If necessary, start without `--reload` for stability while testing.

6) Monetisation defaults didn’t appear for some titles initially
- Cause: Patterns were missing; scans without overrides fell back to Unknown.
- Fix: Added curated patterns (Skate series, Nightreign, EA Sports families) and used the scan flag `apply_defaults=true` or the admin batch endpoint to populate overrides and fairness.

7) Secrets hygiene
- Observation: `.env` is in `.gitignore`; do not commit API keys. Keep `.env` local.

## Clean setup (macOS + zsh)

1) Ensure Python 3.12.11 is installed and on PATH
- Confirm: `python3 --version` should show 3.12.x
- If needed, use python.org installer or a version manager (e.g., pyenv). Update your `~/.zshrc` PATH accordingly.

2) Create and activate a fresh virtual environment
```zsh
cd /Users/tebstest/Documents/GitHub/SkyScansGamesDemo2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

3) Start the backend (run from backend/)
```zsh
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Expected logs include:
- “Database initialized successfully”
- “Application startup complete”
- “Uvicorn running on http://127.0.0.1:8000”

4) Start the frontend (separate terminal)
```zsh
cd /Users/tebstest/Documents/GitHub/SkyScansGamesDemo2/frontend
npm install
npm start
```

5) Quick health checks
- Backend: 
```zsh
curl -sS "http://127.0.0.1:8000/api/games/search?q=test" | jq '.results | length'
```
- If port is stuck:
```zsh
pkill -f "uvicorn main:app" || true
```

## Monetisation defaults — quick actions

We added curated patterns so scans and the batch admin action can annotate monetisation:
- Skate series (Skate, Skate 2, Skate 3): No MTX; Single-player; P2W: No; Fairness: Perfect.
- Nightreign: No MTX; Single-player; P2W: No; Fairness: Perfect.
- EA Sports (FIFA 20–25, Madden NFL 20–25, NHL 20–25, NBA Live 19–23): Ultimate Team with card packs; P2W: Mixed; Fairness: Fair.

Apply to all matched games and rescan:
```zsh
curl -sS -X POST "http://127.0.0.1:8000/api/admin/apply-monetisation-defaults?recalc=true" | jq '.count'
```
Rescan individual games with defaults:
```zsh
curl -sS -X POST "http://127.0.0.1:8000/api/games/<id>/scan?force=true&apply_defaults=true" | jq -r '.reasoning.monetisation.detailed.fairness_label'
```

## Appendix — verifying shell and Python

- Check zsh PATH:
```zsh
echo $PATH | tr ':' '\n'
which python3
python3 --version
```
- Repoint to Python 3.12 if needed (example ~/.zshrc snippet):
```zsh
export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"
```
- Recreate venv after switching Python:
```zsh
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

---
If you want, I can add a small helper script (scripts/dev-backend.sh) to activate the venv and start Uvicorn in one command.