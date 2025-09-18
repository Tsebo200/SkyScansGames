# Quickstart: SkyScansGames

## Prerequisites
- Python 3.11+
- Node.js 18+
- Git

## Backend Setup
1. Clone repo and cd to root
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install fastapi uvicorn requests aiohttp cachetools ratelimit scikit-learn transformers`
5. Run server: `uvicorn main:app --reload`

## Frontend Setup
1. Cd to frontend directory (create if not exists)
2. Install dependencies: `npm install react react-dom axios lodash`
3. Run dev server: `npm start`

## Usage
1. Open browser to http://localhost:3000
2. Enter game title in search bar
3. Select game and click scan
4. View scores in dashboard

## Test Scenarios
- Search for "The Legend of Zelda: Breath of the Wild" (Gen 7)
- Verify scores display in separate containers
- Toggle light/dark mode
- Check contrast with WCAG AA tools