<!-- Repository Information & Links-->

<br />

![GitHub repo size](https://img.shields.io/github/repo-size/Tsebo200/SkyScansGamesDemo2)
![GitHub watchers](https://img.shields.io/github/watchers/Tsebo200/SkyScansGamesDemo2)
![GitHub language count](https://img.shields.io/github/languages/count/Tsebo200/SkyScansGamesDemo2)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/Tsebo200/SkyScansGamesDemo2)
![Github Language](https://img.shields.io/github/languages/top/Tsebo200/SkyScansGamesDemo2)
![Github Downloads](https://img.shields.io/github/downloads/Tsebo200/SkyScansGamesDemo2/total)

<!-- HEADER SECTION -->

<h5 align="center" style="padding:0;margin:0;">Tsebo Ramonyalioa</h5>

<h5 align="center" style="padding:0;margin:0;">SkyScans Games</h5>

<h6 align="center">Web Demo | 2025</h6>

</br>

<p align="center">

  <a href="#">
    <img src="frontend/src/logo.svg" align="center" alt="Sky Logo" width="140" height="140">
  </a>

  <h3 align="center">Sky Scans Games (SSG) — Web Demo</h3>

  <p align="center">
    An AI-augmented game discovery web app with rubric-driven scoring, search, and accessibility-focused UI. Frontend in React, backend in FastAPI with RAWG API integration.
   <br />
   <br />
   <a href="#video-demo">View Demo</a>
    ·
    <a href="https://github.com/Tsebo200/SkyScansGamesDemo2/issues">Report Bug</a>
    ·
    <a href="https://github.com/Tsebo200/SkyScansGamesDemo2/issues">Request Feature</a>
  </p>

<!-- TABLE OF CONTENTS -->

## Table of Contents

* [About the Project](#about-the-project)
  * [Project Description](#project-description)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [How to install](#how-to-install)
* [Features and Functionality](#features-and-functionality)
* [Concept Process](#concept-process)
  * [Ideation](#ideation)
  * [Wireframes](#wireframes)
  * [Custom UI](#custom-ui)
  * [User Flow](#userflow)
* [Development Process](#development-process)
  * [Implementation Process](#implementation-process)
       * [Highlights](#highlights)
       * [Challenges](#challenges)
  * [Future Implementation](#future-implementation)
* [Final Outcome](#final-outcome)
   * [Mockups](#mockups)
   * [Video Demonstration](#video-demonstration)
* [Conclusion](#conclusion)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)

<!--PROJECT DESCRIPTION-->

## About the Project

### Project Description

A web application for discovering games with a focus on accessibility and transparent scoring. The app uses rubric-driven scoring (Completeness, Monetisation, Accessibility, Creativity/Innovation) and integrates the RAWG API. The frontend is a React app (Create React App) and the backend is a FastAPI service that proxies RAWG, enriches with heuristics, and persists to SQLite.

### Built With

The RFFS Stack

* React (CRA)
* Firebase (optional: auth + settings sync)
* FastAPI (Python) + SQLite (local persistence)
* RAWG API integration

<!-- GETTING STARTED -->

## Getting Started

The following instructions will get the project running locally for development and testing on macOS/Linux. Windows works similarly with PowerShell.

### Prerequisites

Ensure you have:

- Node.js >= 18 and npm
- Python 3.12.x
- curl (for quick endpoint checks)

### How to install

#### 1) Clone Repository

```sh
git clone https://github.com/Tsebo200/SkyScansGamesDemo2.git
cd SkyScansGamesDemo2
```

#### 2) Backend setup

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

Create a `.env` in the repo root (or export env vars in your shell):

```sh
# Backend
RAWG_API_KEY=your_rawg_api_key
ALLOWED_ORIGINS=http://localhost:3000
# Optional
OPENAI_API_KEY=your_openai_key
DATABASE_URL=/absolute/path/to/skyscans_games.db  # default is repo root file
```

Start the backend from the `backend/` directory:

```sh
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### 3) Frontend setup

In a new terminal:

```sh
cd SkyScansGamesDemo2/frontend
npm install
```

Create a `.env` file in `frontend/` (CRA uses REACT_APP_*):

```sh
REACT_APP_API_BASE=http://localhost:8000

# Optional Firebase (enable if you want cloud sync)
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
```

Run the frontend:

```sh
npm start
```

The React app will open at `http://localhost:3000` and proxy API requests to `http://localhost:8000`.

<!-- FEATURES AND FUNCTIONALITY-->

## Features and Functionality

### Search and Details
- Debounced search against RAWG via backend proxy
- Game details view with genres, release info, platforms, and images

### Scoring & Insights
- Rubric-based scoring (completeness, monetisation, accessibility, creativity/innovation)
- Heuristics to classify monetisation tactics and fairness

### Accessibility
- Tone and accessibility settings (high contrast, reduced motion, larger text) in UI
- Keyboard-friendly components and color considerations

### Settings & Sync (optional)
- Firebase-based settings sync for user preferences
- Local-first behavior when not signed in

<!-- CONCEPT PROCESS -->

## Concept Process

### Ideation

Make game discovery transparent and accessible by surfacing monetisation, accessibility indicators, and creativity signals—not just popularity.

### Wireframes

Simple multi-panel layout: search, results, details, and a dashboard for score breakdowns.

### Custom UI

- Reusable React components (`SearchBar`, `ScoreDashboard`, `SettingsModal`)
- Subtle animations and responsive layout using CSS

### UserFlow 

1. Search for a title
2. Review details and rubric scores
3. Compare or shortlist titles
4. Adjust accessibility and tone settings

<!-- DEVELOPMENT PROCESS -->

## Development Process

### Implementation Process

* **Frontend**: React (Create React App), Testing Library for unit tests
* **Backend**: FastAPI (Uvicorn), requests/aiohttp, SQLite for persistence
* **API Integration**: RAWG API for game data; optional OpenAI for innovation summaries
* **State Management**: React hooks and context for accessibility/tone settings
* **Auth/Sync**: Optional Firebase (guarded by env)

#### Highlights

- End-to-end local setup in minutes
- Heuristic scoring pipeline with cached RAWG calls
- Optional cloud sync without blocking local dev

#### Challenges

- Python version drift (ensure 3.12.x)
- CORS and CRA proxy alignment between ports 3000/8000
- Handling incomplete RAWG fields consistently

### Future Implementation

- Notifications for updates and recommendations
- Deeper embedding-based similarity
- Social sharing and lists
- Advanced filters by genre/platform/score range

<!-- MOCKUPS -->

## Final Outcome

### Mockups

Modern responsive UI with a focus on readable score breakdowns and accessible controls.

### Video Demonstration

<a id="video-demo"></a>

To see a run-through of the application, add a recording link here when available.

See the [open issues](https://github.com/Tsebo200/SkyScansGamesDemo2/issues) for a list of proposed features (and known issues).

<!-- CONCLUSION / LICENSE / CONTACT -->

## Conclusion

This demo showcases a practical approach to transparent, accessibility-aware game discovery with a lightweight, developer-friendly stack.

## Author

* **Tsebo Ramonyalioa** - [Tsebo200](https://github.com/Tsebo200)

## License

Copyright (c) 2025 CreativeT by Tsebo Ramonyalioa

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

See: https://creativecommons.org/licenses/by-nc/4.0/

SPDX: CC-BY-NC-4.0

BY: credit must be given to the creator.

NC: Only noncommercial uses of the work are permitted.

## Contact

* **Tsebo Ramonyalioa** - [tsebo.ramonyalioa.an@gmail.com](mailto:tsebo.ramonyalioa.an@gmail.com)
* **Project Link** - https://github.com/Tsebo200/SkyScansGamesDemo2

## Acknowledgements

* RAWG API — https://rawg.io/apidocs
* FastAPI — https://fastapi.tiangolo.com/
* React — https://reactjs.org/
* Firebase — https://firebase.google.com/
* YouTube — https://www.youtube.com/
* Open-source community — https://react.dev/

---

Developer notes and troubleshooting have moved to a separate section in this README. For Render deployment details, see `backend/README-deploy-render.md`.