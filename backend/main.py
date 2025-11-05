from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
import re
from datetime import datetime, timedelta
import os
from contextlib import contextmanager
import requests
try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # Fallback if not installed yet
    BeautifulSoup = None  # type: ignore
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time
from functools import lru_cache
import math
 
# Load environment variables
try:
    from dotenv import load_dotenv, find_dotenv
    # 1) Load from repo root (or nearest up the tree) when server is started from project root
    root_env = find_dotenv(usecwd=True)
    if root_env:
        load_dotenv(root_env)
    # 2) Also load a local backend/.env sitting next to this file (does not override root by default)
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=False)
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")

app = FastAPI(title="SkyScansGames API", version="1.0.0")

# Configuration
RAWG_API_KEY = os.getenv("RAWG_API_KEY", "demo")  # Get from environment or use demo
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "")
CIPT_BASE_URL = "https://caniplaythat.com"
CACHE_TTL = 3600  # 1 hour cache
COMMUNITY_TELEMETRY_TTL = 21600  # 6 hours reuse window for telemetry snapshot
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("CHATGPT_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
USE_LLM_INNOVATION = os.getenv("USE_LLM_INNOVATION", "0").lower() in ("1","true","yes")
# Opt-in flag to apply heuristic monetisation defaults automatically during scans (off by default)
AUTO_MONETISATION_DEFAULTS = os.getenv("AUTO_MONETISATION_DEFAULTS", "0").lower() in ("1","true","yes")

# Anthropic (Claude) configuration for fun/gamey tone rewrites
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")

# Caching configuration
# Set via env to extend TTLs in offline scenarios or disable expiry checks entirely
API_CACHE_TTL = int(os.getenv("API_CACHE_TTL", "1800"))  # default 30 minutes for API responses
SEARCH_CACHE_TTL = int(os.getenv("SEARCH_CACHE_TTL", "600"))  # default 10 minutes for search results
API_CACHE_DISABLE_EXPIRY = os.getenv("API_CACHE_DISABLE_EXPIRY", "0").lower() in ("1","true","yes")

@lru_cache(maxsize=100)
def get_cache_key(url: str, params: str = "") -> str:
    """Generate cache key from URL and parameters"""
    key_data = f"{url}|{params}"
    return hashlib.md5(key_data.encode()).hexdigest()

def get_cached_response(cache_key: str) -> dict:
    """Get cached API response from database"""
    with get_db() as conn:
        if API_CACHE_DISABLE_EXPIRY:
            result = conn.execute("""
                SELECT response FROM api_cache 
                WHERE id = ?
            """, (cache_key,)).fetchone()
        else:
            result = conn.execute("""
                SELECT response FROM api_cache 
                WHERE id = ? AND expires_at > datetime('now')
            """, (cache_key,)).fetchone()
        if result:
            # result may be a tuple with only response or response+expires_at
            resp = result[0]
            try:
                return json.loads(resp)
            except Exception:
                return None
    return None

def set_cached_response(cache_key: str, response: dict, ttl: int):
    """Cache API response in database"""
    expires_at = time.time() + ttl
    with get_db() as conn:
        # We don't currently track URL separately (left blank previously); keep placeholder for structure
        conn.execute("""
            INSERT OR REPLACE INTO api_cache (id, url, response, expires_at)
            VALUES (?, ?, ?, datetime(?, 'unixepoch'))
        """, (cache_key, 'api', json.dumps(response), expires_at))
        conn.commit()

# --- LLM helper (requests-based) ---
def _call_openai_chat(messages: list, model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 600) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content')
        return content
    except Exception as e:
        print(f"OpenAI chat call failed: {e}")
        return None

def llm_innovation_score(game_id: int, rawg_details: dict) -> Optional[dict]:
    """Ask an LLM to produce a 0-100 Innovation & Creativity score and structured breakdown from game metadata.
    Returns dict with fields: overall_score, novelty, mechanic_diversity, emergent_systems, hype_penalty, explanation
    and persists into game_innovation_metrics.
    """
    if not OPENAI_API_KEY:
        return None
    name = rawg_details.get('name') or rawg_details.get('slug') or 'Unknown Game'
    genres = [g.get('name') for g in (rawg_details.get('genres') or []) if isinstance(g, dict)]
    tags = [t.get('name') for t in (rawg_details.get('tags') or []) if isinstance(t, dict)]
    description = rawg_details.get('description_raw') or rawg_details.get('description') or ''
    user_payload = {
        "name": name,
        "genres": genres,
        "tags": tags,
        "description": description[:6000]
    }
    system_msg = {
        "role": "system",
        "content": (
            "You are a careful rater for video game Innovation & Creativity. "
            "Only use the provided info. Output strict JSON with keys: overall_score (0-100), novelty (0-100), "
            "mechanic_diversity (0-100), emergent_systems (0-100), hype_penalty (0-100), explanation (string). "
            "Do not invent features not implied by text; be conservative."
        )
    }
    user_msg = {
        "role": "user",
        "content": json.dumps(user_payload)
    }
    content = _call_openai_chat([system_msg, user_msg])
    if not content:
        return None
    try:
        parsed = json.loads(content)
        overall = float(parsed.get('overall_score', 0))
        novelty = float(parsed.get('novelty', 0))
        mech_div = float(parsed.get('mechanic_diversity', 0))
        emergent = float(parsed.get('emergent_systems', 0))
        hype_pen = float(parsed.get('hype_penalty', 0))
        overall = max(0, min(100, overall))
        summary = {
            'llm_model': OPENAI_MODEL,
            'novelty': novelty,
            'mechanic_diversity': mech_div,
            'emergent_systems': emergent,
            'hype_penalty': hype_pen,
            'explanation': parsed.get('explanation')
        }
        with get_db() as conn:
            conn.execute(
                "REPLACE INTO game_innovation_metrics (game_id, tag_divergence, emergent_keywords, hype_penalty, mechanic_diversity, base_score, adjusted_score, summary_json) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (game_id, None, None, hype_pen, int(mech_div), None, overall, json.dumps(summary))
            )
            conn.commit()
        return {'overall_score': overall, 'summary': summary}
    except Exception as e:
        print(f"LLM innovation parse error: {e}")
        return None

# API Clients
class RAWGClient:
    BASE_URL = "https://api.rawg.io/api"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_games(self, query: str, page_size: int = 10, page: int = 1) -> dict:
        """Search for games using RAWG API with caching and pagination.

        Replaces previous implementation; uses broader search for shorter queries.
        """
        page_size = max(1, min(page_size, 40))
        page = max(1, page)
        url = f"{self.BASE_URL}/games"
        params = {
            "key": self.api_key,
            "search": query,
            "page_size": page_size,
            "page": page,
            "search_precise": True if len(query) > 3 else False
        }
        cache_key = get_cache_key(url, str(params))
        cached_result = get_cached_response(cache_key)
        if cached_result:
            print(f"Cache hit for search: '{query}' page={page} size={page_size}")
            return cached_result
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            set_cached_response(cache_key, result, SEARCH_CACHE_TTL)
            return result
        except requests.RequestException as e:
            print(f"RAWG API error: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                demo_result = self._get_demo_games(query)
                set_cached_response(cache_key, demo_result, 300)
                return demo_result
            return {"results": []}
    
    def _get_demo_games(self, query: str) -> dict:
        """Return demo games when API key is invalid"""
        demo_games = [
            {
                "id": 1,
                "name": "The Legend of Zelda: Breath of the Wild",
                "released": "2017-03-03",
                "background_image": "https://media.rawg.io/media/games/83f/83f6f70a7c1b86cd2637b029d8b42cb3.jpg",
                "rating": 4.5,
                "metacritic": 97
            },
            {
                "id": 2,
                "name": "The Witcher 3: Wild Hunt",
                "released": "2015-05-19",
                "background_image": "https://media.rawg.io/media/games/618/618c2031a07bbff6b4f611f10b6bcdbc.jpg",
                "rating": 4.7,
                "metacritic": 93
            },
            {
                "id": 3,
                "name": "God of War Ragnarök",
                "released": "2022-11-09",
                "background_image": "https://media.rawg.io/media/games/20a/20aa03a10cda45230a362b9bdb965b68.jpg",
                "rating": 4.8,
                "metacritic": 94
            },
            {
                "id": 4,
                "name": "Elden Ring",
                "released": "2022-02-25",
                "background_image": "https://media.rawg.io/media/games/5ec/5ecac5cb026ec26a56efcc546364e3483.jpg",
                "rating": 4.6,
                "metacritic": 96
            },
            {
                "id": 5,
                "name": "Red Dead Redemption 2",
                "released": "2018-10-26",
                "background_image": "https://media.rawg.io/media/games/511/5118aff5091cb3efec399c808f8c598f2.jpg",
                "rating": 4.7,
                "metacritic": 97
            }
        ]
        
        # Filter demo games based on query
        if query.lower() in ["god", "war"]:
            filtered_games = [g for g in demo_games if "god" in g["name"].lower() or "war" in g["name"].lower()]
        elif query.lower() in ["witcher", "wild"]:
            filtered_games = [g for g in demo_games if "witcher" in g["name"].lower()]
        elif query.lower() in ["zelda", "legend"]:
            filtered_games = [g for g in demo_games if "zelda" in g["name"].lower()]
        elif query.lower() in ["elden", "ring"]:
            filtered_games = [g for g in demo_games if "elden" in g["name"].lower()]
        elif query.lower() in ["red", "dead"]:
            filtered_games = [g for g in demo_games if "red" in g["name"].lower()]
        else:
            filtered_games = demo_games[:3]  # Return first 3 games for any other query
        
        return {"results": filtered_games}
    
    def get_game_details(self, rawg_id: int) -> dict:
        """Get detailed game information with caching"""
        url = f"{self.BASE_URL}/games/{rawg_id}"
        params = {"key": self.api_key}
        
        # Create cache key
        cache_key = get_cache_key(url, str(params))
        
        # Check cache first
        cached_result = get_cached_response(cache_key)
        if cached_result:
            print(f"Cache hit for game details: {rawg_id}")
            return cached_result
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Cache the result
            set_cached_response(cache_key, result, API_CACHE_TTL)
            return result
        except requests.RequestException as e:
            print(f"RAWG API error: {e}")
            # If API key is invalid, return demo game details
            if "401" in str(e) or "Unauthorized" in str(e):
                demo_result = self._get_demo_game_details(rawg_id)
                # Cache demo result for shorter time
                set_cached_response(cache_key, demo_result, 300)  # 5 minutes
                return demo_result
            return {}
    
    def _get_demo_game_details(self, rawg_id: int) -> dict:
        """Return demo game details when API key is invalid"""
        demo_details = {
            1: {
                "id": 1,
                "name": "The Legend of Zelda: Breath of the Wild",
                "metacritic": 97,
                "rating": 4.5,
                "released": "2017-03-03",
                "playtime": 25,
                "genres": [{"name": "Adventure"}, {"name": "Action"}],
                "esrb_rating": {"name": "E10+"},
                "description_raw": "The Legend of Zelda: Breath of the Wild is an open-world action-adventure game developed and published by Nintendo."
            },
            2: {
                "id": 2,
                "name": "The Witcher 3: Wild Hunt",
                "metacritic": 93,
                "rating": 4.7,
                "released": "2015-05-19",
                "playtime": 30,
                "genres": [{"name": "RPG"}, {"name": "Action"}],
                "esrb_rating": {"name": "M"},
                "description_raw": "The Witcher 3: Wild Hunt is an open-world, action role-playing game developed by CD Projekt RED."
            },
            3: {
                "id": 3,
                "name": "God of War Ragnarök",
                "metacritic": 94,
                "rating": 4.8,
                "released": "2022-11-09",
                "playtime": 20,
                "genres": [{"name": "Action"}, {"name": "Adventure"}],
                "esrb_rating": {"name": "M"},
                "description_raw": "God of War Ragnarök is an action-adventure game developed by Santa Monica Studio."
            },
            4: {
                "id": 4,
                "name": "Elden Ring",
                "metacritic": 96,
                "rating": 4.6,
                "released": "2022-02-25",
                "playtime": 35,
                "genres": [{"name": "Action"}, {"name": "RPG"}],
                "esrb_rating": {"name": "M"},
                "description_raw": "Elden Ring is an action role-playing game developed by FromSoftware."
            },
            5: {
                "id": 5,
                "name": "Red Dead Redemption 2",
                "metacritic": 97,
                "rating": 4.7,
                "released": "2018-10-26",
                "playtime": 28,
                "genres": [{"name": "Action"}, {"name": "Adventure"}],
                "esrb_rating": {"name": "M"},
                "description_raw": "Red Dead Redemption 2 is an open-world action-adventure game developed by Rockstar Games."
            }
        }
        
        return demo_details.get(rawg_id, {})

class SteamClient:
    BASE_URL = "https://store.steampowered.com/api"
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
    
    def get_app_details(self, app_id: int) -> dict:
        """Get Steam app details"""
        url = f"https://store.steampowered.com/api/appdetails"
        params = {
            "appids": app_id,
            "cc": "us",
            "l": "english"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get(str(app_id), {}).get("data", {}) if data else {}
        except requests.RequestException as e:
            print(f"Steam API error: {e}")
            return {}

# Initialize API clients
rawg_client = RAWGClient(RAWG_API_KEY)
steam_client = SteamClient(STEAM_API_KEY)

class CIPTClient:
    """Lightweight scraper client for CanIPlayThat accessibility reviews.

    NOTE: Site does not expose an official public API; this approach scrapes search
    results and (optionally) review pages. Keep requests minimal and cache results.
    """
    SEARCH_URL = f"{CIPT_BASE_URL}/"

    def search_reviews(self, title: str, limit: int = 3) -> list:
        if BeautifulSoup is None:
            return []
        query = title.replace(' ', '+')
        url = f"{CIPT_BASE_URL}/?s={query}"
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (compatible; SkyScansBot/0.1)"})
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"CIPT search error for '{title}': {e}")
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []
        # Heuristic: Accessibility review links often contain 'accessibility-review' or 'accessibility review'
        for a in soup.select('a'):  # broad, then filter
            href = a.get('href') or ''
            text = a.get_text(strip=True) or ''
            lowered = text.lower()
            if not href or not text:
                continue
            # Filter by game title words presence and accessibility signals
            title_tokens = [t for t in title.lower().split() if len(t) > 2]
            if any(tok in lowered for tok in title_tokens) and ('accessibility' in lowered or 'review' in lowered):
                results.append({
                    'title': text,
                    'url': href
                })
            if len(results) >= limit:
                break
        return results

    def extract_accessibility_score(self, review_url: str) -> dict:
        """Attempt to extract structured accessibility info from a review page.
        CIPT pages vary; we approximate a score by counting feature keywords.
        Returns {'raw_score': int, 'max_score': int, 'features': {...}} or empty dict.
        """
        if BeautifulSoup is None:
            return {}
        try:
            resp = requests.get(review_url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (compatible; SkyScansBot/0.1)"})
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"CIPT review fetch error: {e}")
            return {}
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator=' ').lower()
        # Simple keyword buckets
        feature_keywords = {
            'captions': ['subtitle', 'captions', 'subtitles'],
            'remapping': ['remap', 'binding', 'key binding', 'rebinding', 'customize controls'],
            'difficulty': ['difficulty', 'assist', 'mode', 'story mode'],
            'motor': ['toggle', 'hold', 'press', 'motor'],
            'visual': ['colorblind', 'contrast', 'text size', 'ui scale'],
            'audio': ['audio description', 'text to speech', 'tts'],
            'cognitive': ['puzzle hint', 'cognitive', 'simplified']
        }
        feature_hits = {}
        total_hits = 0
        for feature, keys in feature_keywords.items():
            hits = sum(1 for k in keys if k in text)
            if hits:
                feature_hits[feature] = hits
                total_hits += hits
        if not total_hits:
            return {}
        # Normalize to pseudo score out of 100 (cap at 100)
        # Assume each hit ~5 points, up to 20 hits => 100
        raw_score = min(100, total_hits * 5)
        return {
            'raw_score': raw_score,
            'max_score': 100,
            'features': feature_hits,
            'source': review_url
        }

cipt_client = CIPTClient()

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()

# Database setup
BASE_DIR = os.path.dirname(__file__)
# Prefer the repo root database to avoid duplicate files when running from different CWDs
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
DATABASE_URL = os.environ.get("DATABASE_URL") or os.path.join(REPO_ROOT, "skyscans_games.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        # Games table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                release_year INTEGER,
                release_date TEXT,
                release_date_source TEXT,
                release_date_notes TEXT,
                generation INTEGER,
                platform TEXT,
                engine TEXT,
                rawg_id INTEGER,
                steam_id INTEGER,
                cover_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Ensure new columns exist (migrations)
        try:
            _cols = [c[1] for c in conn.execute("PRAGMA table_info(games)").fetchall()]
            if 'release_year' not in _cols:
                conn.execute("ALTER TABLE games ADD COLUMN release_year INTEGER")
            if 'release_date' not in _cols:
                conn.execute("ALTER TABLE games ADD COLUMN release_date TEXT")
            if 'release_date_source' not in _cols:
                conn.execute("ALTER TABLE games ADD COLUMN release_date_source TEXT")
            if 'release_date_notes' not in _cols:
                conn.execute("ALTER TABLE games ADD COLUMN release_date_notes TEXT")
            if 'cover_image' not in _cols:
                conn.execute("ALTER TABLE games ADD COLUMN cover_image TEXT")
        except Exception as _e:
            print(f"cover_image migration notice: {_e}")

        # Scores table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                reviews_score REAL,
                graphic_score REAL,
                microtransactions_score REAL,
                game_mechanics_score REAL,
                completeness_score REAL,
                story_quality_score REAL,
                accessibility_score REAL,
                overall_score REAL,
                reasoning TEXT,
                -- New rubric explicit columns (may be NULL for legacy rows)
                core_gameplay_score REAL,
                story_immersion_score REAL,
                presentation_score REAL,
                technical_performance_score REAL,
                innovation_creativity_score REAL,
                community_longevity_score REAL,
                scoring_version INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')
        # Migrate missing columns (if existing DB predates rubric change)
        existing_cols = [c[1] for c in conn.execute("PRAGMA table_info(scores)").fetchall()]
        required_new = [
            ('core_gameplay_score','REAL'),('story_immersion_score','REAL'),('presentation_score','REAL'),
            ('technical_performance_score','REAL'),('innovation_creativity_score','REAL'),('community_longevity_score','REAL'),
            ('scoring_version','INTEGER')
        ]
        for col, ctype in required_new:
            if col not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE scores ADD COLUMN {col} {ctype}")
                except Exception as e:
                    print(f"Migration warning (scores add {col}): {e}")

        # Cache table for API responses (id is md5 hex string -> needs TEXT type)
        def ensure_api_cache_schema():
            info = conn.execute("PRAGMA table_info(api_cache)").fetchall()
            recreate = False
            if info:
                for col in info:
                    # col format: (cid, name, type, notnull, dflt_value, pk)
                    if col[1] == 'id' and col[2].lower() != 'text':
                        recreate = True
                        break
            if recreate:
                print("Migrating api_cache table to TEXT primary key for cache keys")
                conn.execute("DROP TABLE api_cache")
                info = []
            if not info or recreate:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS api_cache (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        response TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                ''')

        ensure_api_cache_schema()

        # Accessibility review cache table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS accessibility_reviews (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                source_url TEXT NOT NULL,
                raw_score REAL,
                max_score REAL,
                features_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
        # Overrides table (monetisation & performance adjustments)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS score_overrides (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL UNIQUE,
                monetisation_types TEXT,
                monetisation_notes TEXT,
                performance_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
        # Community telemetry table (stores raw snapshot from RAWG-based heuristics)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_community_telemetry (
                game_id INTEGER PRIMARY KEY,
                ratings_count INTEGER,
                added_count INTEGER,
                updated_rawg_at TEXT,
                steam_ccu INTEGER,
                steam_reviews_total INTEGER,
                confidence_score REAL,
                raw_payload TEXT,
                steam_payload TEXT,
                last_scan_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
        # Migration for newly added columns if table pre-existed
        existing_cols = [c[1] for c in conn.execute("PRAGMA table_info(game_community_telemetry)").fetchall()]
        for new_col, ctype in [
            ("steam_ccu","INTEGER"),("steam_reviews_total","INTEGER"),("confidence_score","REAL"),("steam_payload","TEXT"),
            ("steam_positive_reviews","INTEGER"),("steam_negative_reviews","INTEGER"),("steam_review_score","INTEGER"),
            ("steam_weighted_vote","REAL"),("steam_achievements_sampled","INTEGER"),("steam_achievements_avg_percent","REAL")
        ]:
            if new_col not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE game_community_telemetry ADD COLUMN {new_col} {ctype}")
                except Exception as e:
                    print(f"Migration (game_community_telemetry add {new_col}) warning: {e}")
        # MVP new intelligence tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_innovation_metrics (
                game_id INTEGER PRIMARY KEY,
                tag_divergence REAL,
                emergent_keywords INTEGER,
                hype_penalty INTEGER,
                mechanic_diversity INTEGER,
                base_score REAL,
                adjusted_score REAL,
                summary_json TEXT,
                computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_accessibility_features (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                feature_key TEXT NOT NULL,
                present INTEGER NOT NULL,
                confidence REAL,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, feature_key),
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_life_support_inference (
                game_id INTEGER PRIMARY KEY,
                inferred_status TEXT,
                confidence REAL,
                last_patch_age_days INTEGER,
                ccu_value INTEGER,
                evidence_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
        # Life support table (live service status / eternal support)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS game_life_support (
                game_id INTEGER PRIMARY KEY,
                support_status TEXT, -- unknown | active | eternal | sunset | offline
                last_update_date TEXT,
                next_update_hint TEXT,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
        # Archive table for legacy or alternative scoring versions
        conn.execute('''
            CREATE TABLE IF NOT EXISTS scores_archive (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                scoring_version INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, scoring_version),
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')

        # RAWG details snapshot table for offline usage
        conn.execute('''
            CREATE TABLE IF NOT EXISTS rawg_detail_snapshots (
                game_id INTEGER PRIMARY KEY,
                description TEXT,
                genres_json TEXT,
                developers_json TEXT,
                publishers_json TEXT,
                age_rating TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')

        # Insert mock data if tables are empty
        if not conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]:
            mock_games_data = [
                (1, "The Legend of Zelda: Breath of the Wild", 7, "console", "Custom", None, None),
                (2, "The Witcher 3: Wild Hunt", 7, "pc", "REDengine", None, None),
                (3, "God of War Ragnarök", 9, "console", "Custom", None, None),
            ]
            conn.executemany("INSERT INTO games (id, title, generation, platform, engine, rawg_id, steam_id) VALUES (?, ?, ?, ?, ?, ?, ?)", mock_games_data)

            # Generate scores using the new function with mock RAWG data
            for game_data in mock_games_data:
                game_id, title, generation, platform, engine, rawg_id, steam_id = game_data
                # Create mock RAWG data for score generation
                mock_rawg_data = {
                    "metacritic": 95 if "Zelda" in title else 93 if "Witcher" in title else 94,
                    "rating": 4.5 if "Zelda" in title else 4.7 if "Witcher" in title else 4.8,
                    "released": "2017-03-03" if "Zelda" in title else "2015-05-19" if "Witcher" in title else "2022-11-09",
                    "playtime": 25 if "Zelda" in title else 30 if "Witcher" in title else 20,
                    "genres": [{"name": "Adventure"} if "Zelda" in title else {"name": "RPG"} if "Witcher" in title else {"name": "Action"}],
                    "esrb_rating": {"name": "E10+"}
                }
                
                scores = generate_scores_from_api(mock_rawg_data)
                
                conn.execute("""
                    INSERT INTO scores (game_id, reviews_score, graphic_score, microtransactions_score,
                                      game_mechanics_score, completeness_score, story_quality_score,
                                      accessibility_score, overall_score, reasoning)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game_id,
                    scores["reviews_score"],
                    scores["graphic_score"],
                    scores["microtransactions_score"],
                    scores["game_mechanics_score"],
                    scores["completeness_score"],
                    scores["story_quality_score"],
                    scores["accessibility_score"],
                    scores["overall_score"],
                    json.dumps(scores["reasoning"])
                ))

        conn.commit()
        conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_games_rawg_id ON games(rawg_id)''')

# ================= MVP Heuristic Intelligence (Innovation, Accessibility, Life Support) =================
EMERGENT_KEYWORDS = [
    'procedural','emergent','sandbox','systemic','simulation','dynamic ai','modding','physics-driven','roguelike','roguelite','ecosystem'
]
HYPE_KEYWORDS = [
    'revolutionary','groundbreaking','never before','ultimate','definitive','unparalleled','first ever','game-changing'
]
ACCESSIBILITY_REGEX = {
    'subtitles': re.compile(r'\bsubtitles?\b', re.IGNORECASE),
    'colorblind_support': re.compile(r'color.?blind|dalton', re.IGNORECASE),
    'remap_keyboard': re.compile(r'(rebind|remap).+(key|keyboard|control)', re.IGNORECASE),
    'remap_controller': re.compile(r'(controller).+(remap|rebind)', re.IGNORECASE),
    'font_scaling': re.compile(r'(font).+(size|scal)', re.IGNORECASE),
    'contrast_modes': re.compile(r'high.?contrast', re.IGNORECASE)
}

def compute_innovation_metrics(game_id: int, rawg_details: dict) -> dict:
    """MVP heuristic: approximate innovation using RAWG tags/genres/description.
    Stores row in game_innovation_metrics and returns adjusted score & summary.
    """
    try:
        desc = rawg_details.get('description_raw') or rawg_details.get('description') or ''
        tags = rawg_details.get('tags') or []
        tag_names = [t.get('name') for t in tags if isinstance(t, dict) and t.get('name')]
        genres = rawg_details.get('genres') or []
        genre_names = [g.get('name') for g in genres if isinstance(g, dict) and g.get('name')]
        full_text = ' '.join(filter(None, [desc] + tag_names + genre_names)).lower()
        emergent_hits = sum(1 for k in EMERGENT_KEYWORDS if k in full_text)
        hype_hits = sum(1 for k in HYPE_KEYWORDS if k in full_text)
        mechanic_diversity = min(30, len(set(tag_names)))
        baseline = {'action','adventure','rpg','indie','strategy','simulation'}
        overlap = len(baseline.intersection({(g or '').lower() for g in genre_names}))
        tag_divergence = 1 - (overlap / max(1,len(genre_names))) if genre_names else 0.5
        base_score = (
            min(1, tag_divergence) * 40 +
            min(emergent_hits,10) * 3 +
            (mechanic_diversity/30) * 25
        ) - hype_hits * 1.5
        adjusted = max(0, min(100, base_score))
        summary = {
            'tag_divergence': round(tag_divergence,3),
            'emergent_keywords': emergent_hits,
            'hype_penalty': hype_hits,
            'mechanic_diversity': mechanic_diversity,
            'explanation': 'divergence*40 + emergent*3 + diversityScaled*25 - hype*1.5 (clamped)'
        }
        with get_db() as conn:
            conn.execute("REPLACE INTO game_innovation_metrics (game_id, tag_divergence, emergent_keywords, hype_penalty, mechanic_diversity, base_score, adjusted_score, summary_json) VALUES (?,?,?,?,?,?,?,?)",
                         (game_id, tag_divergence, emergent_hits, hype_hits, mechanic_diversity, base_score, adjusted, json.dumps(summary)))
            conn.commit()
        return {'adjusted_score': adjusted, 'summary': summary}
    except Exception as e:
        print(f"Innovation heuristic error: {e}")
        return {'adjusted_score': None, 'summary': {'error': str(e)}}

def infer_accessibility_features(game_id: int, rawg_details: dict) -> dict:
    desc = (rawg_details.get('description_raw') or rawg_details.get('description') or '').lower()
    results = {}
    for key, rx in ACCESSIBILITY_REGEX.items():
        present = 1 if rx.search(desc) else 0
        results[key] = present
    positives = sum(results.values())
    confidence = round(0.4 + (positives / (len(results) or 1)) * 0.6,2)
    try:
        with get_db() as conn:
            for key, present in results.items():
                conn.execute("REPLACE INTO game_accessibility_features (game_id, feature_key, present, confidence, evidence) VALUES (?,?,?,?,?)",
                             (game_id, key, present, confidence, None))
            conn.commit()
    except Exception as e:
        print(f"Accessibility feature persist error: {e}")
    core = ['subtitles','colorblind_support','remap_keyboard','remap_controller']
    core_present = sum(results.get(c,0) for c in core)
    core_score = core_present / max(1,len(core))
    qol_keys = [k for k in results.keys() if k not in core]
    qol_present = sum(results.get(q,0) for q in qol_keys)
    qol_score = qol_present / max(1,len(qol_keys))
    heuristic_score = round((core_score*0.7 + qol_score*0.3) * 100 * confidence,1)
    return {'features': results, 'confidence': confidence, 'heuristic_score': heuristic_score}

def infer_life_support_status(game_id: int, rawg_details: dict, telemetry: Optional[dict]) -> dict:
    updated_rawg_at = rawg_details.get('updated') or rawg_details.get('last_updated') or rawg_details.get('updated_at')
    age_days = None
    if updated_rawg_at:
        try:
            dt = datetime.fromisoformat(updated_rawg_at.replace('Z','+00:00')) if 'T' in updated_rawg_at else datetime.fromisoformat(updated_rawg_at)
            age_days = (datetime.utcnow() - dt).days
        except Exception:
            pass
    ccu = telemetry.get('steam_ccu') if telemetry else None
    status = 'unknown'
    confidence = 0.4
    if age_days is not None:
        if age_days <= 45 and (ccu or 0) > 5000:
            status = 'eternal'; confidence = 0.7
        elif age_days <= 120:
            status = 'active'; confidence = 0.6
        elif age_days > 400 and (ccu or 0) < 50:
            status = 'sunset'; confidence = 0.55
    if ccu is not None and ccu < 5 and (age_days or 999) > 600:
        status = 'offline'; confidence = 0.65
    evidence = {'age_days': age_days, 'ccu': ccu}
    try:
        with get_db() as conn:
            conn.execute("REPLACE INTO game_life_support_inference (game_id, inferred_status, confidence, last_patch_age_days, ccu_value, evidence_json) VALUES (?,?,?,?,?,?)",
                         (game_id, status, confidence, age_days, ccu, json.dumps(evidence)))
            conn.commit()
    except Exception as e:
        print(f"Life support inference persist error: {e}")
    return {'status': status, 'confidence': confidence, 'evidence': evidence}

# =========================================================================================================

def generate_scores_from_api(game_data: dict, steam_data: dict = None) -> dict:
    """Generate scores based on RAWG + simple heuristics following new rubric.

    Rubric Groups (weights to 100):
      Core Gameplay 25%
      Story & Immersion 20%
      Presentation 15%
      Technical Performance 15%
      Completeness 10% (kept as its own score)
      Innovation & Creativity 10%
      Community & Longevity 5%
    Informational (NOT scored): Reviews (Metacritic), Accessibility, Monetisation.
    """
    # --- Normalize raw inputs ---
    raw_metacritic = game_data.get("metacritic")
    if not isinstance(raw_metacritic, (int, float)):
        raw_metacritic = 70  # neutral fallback
    metacritic = max(0, min(100, int(raw_metacritic)))

    rating_raw = game_data.get("rating")
    if not isinstance(rating_raw, (int, float)):
        # Fallback: derive an approximate 0-5 from metacritic if RAWG user rating missing
        try:
            rating_raw = (metacritic / 20.0) if isinstance(metacritic, (int, float)) else 3.5
        except Exception:
            rating_raw = 3.5
    rating = max(0.0, min(5.0, float(rating_raw)))

    release_year = 2020
    if isinstance(game_data.get("released"), str) and len(game_data["released"]) >= 4:
        try:
            release_year = int(game_data["released"][:4])
        except ValueError:
            pass

    playtime_val = game_data.get("playtime")
    if not isinstance(playtime_val, (int, float)):
        playtime_val = 0
    playtime = playtime_val or 0

    genres = game_data.get("genres") or []
    if not isinstance(genres, list):
        genres = []
    genre_names = []
    for g in genres:
        if isinstance(g, dict):
            nm = g.get("name")
            if isinstance(nm, str):
                genre_names.append(nm.lower())

    # --- Informational Scores (NOT used directly in weighted overall) ---
    reviews_score = metacritic  # Shown only, excluded from weighted total per new rubric.
    accessibility_score = 75 if game_data.get("esrb_rating") else 70  # May be augmented later (CIPT)

    # --- Completeness (10%) ---
    if playtime > 40:
        completeness_score = 92
    elif playtime > 25:
        completeness_score = 90
    elif playtime > 15:
        completeness_score = 85
    elif playtime > 8:
        completeness_score = 80
    elif playtime > 2:
        completeness_score = 75
    else:
        completeness_score = 70

    # --- Core Gameplay (25%) ---
    # Mechanics & Controls (10): rating-derived
    mechanics_controls = min(100, (rating / 5) * 100)
    # Balance (7): heuristic using difference between metacritic & scaled rating
    rating_scaled = mechanics_controls
    balance_gap = abs(rating_scaled - metacritic)
    balance = max(50, 100 - balance_gap * 0.6)  # larger disagreement lowers balance
    balance = min(100, balance)
    # Replayability (8): based on playtime + genre
    replayability_base = 60
    if playtime > 30:
        replayability_base += 15
    elif playtime > 15:
        replayability_base += 10
    if any(g in genre_names for g in ["rpg", "roguelike", "strategy"]):
        replayability_base += 10
    if "adventure" in genre_names:
        replayability_base += 5
    replayability = max(50, min(100, replayability_base))
    core_gameplay_score = (
        mechanics_controls * (10/25) +
        balance * (7/25) +
        replayability * (8/25)
    )

    # --- Story & Immersion (20%) ---
    # Narrative Quality (10): metacritic + genre influence
    narrative = metacritic
    if any(g in genre_names for g in ["rpg", "adventure"]):
        narrative = min(100, narrative + 5)
    # Worldbuilding (5)
    worldbuilding = 70
    if "rpg" in genre_names:
        worldbuilding += 15
    elif "adventure" in genre_names:
        worldbuilding += 10
    worldbuilding = min(100, worldbuilding)
    # Character Development (5)
    character_dev = 65
    if any(g in genre_names for g in ["rpg", "adventure"]):
        character_dev += 15
    character_dev = min(95, character_dev)
    story_immersion_score = (
        narrative * (10/20) +
        worldbuilding * (5/20) +
        character_dev * (5/20)
    )

    # --- Presentation (15%) ---
    # Graphics & Art (6): reuse prior heuristic
    graphics_base = min(100, 60 + (release_year - 2010) * 2)
    graphics_art = min(100, graphics_base + (metacritic - 70) * 0.3)
    # Sound & Music (5): rating & metacritic blend
    sound_music = min(100, (rating_scaled * 0.5) + (metacritic * 0.5))
    # Immersion Factor (4): average of narrative & graphics + small genre bump
    immersion_factor = min(100, (narrative + graphics_art) / 2 + (5 if "adventure" in genre_names else 0))
    presentation_score = (
        graphics_art * (6/15) +
        sound_music * (5/15) +
        immersion_factor * (4/15)
    )

    # --- Technical Performance (15%) ---
    # Frame Stability (6): newer titles may still patch; assume baseline 80 then adjust by rating
    frame_stability = min(100, 75 + (rating * 3))
    # Stability & Reliability (4): rating & metacritic consistency
    stability_reliability = max(50, min(95, 70 + (min(rating_scaled, metacritic) - 60) * 0.3))
    # Optimisation (5): release year & playtime (longer titles may have heavier loads)
    optimisation = 78
    if release_year >= 2023:
        optimisation = min(100, optimisation + 5)
    if playtime > 40:
        optimisation -= 3
    optimisation = max(60, min(100, optimisation))
    technical_performance_score = (
        frame_stability * (6/15) +
        stability_reliability * (4/15) +
        optimisation * (5/15)
    )

    # --- Innovation & Creativity (10%) ---
    title = game_data.get("name") or ""
    sequel_penalty = 0
    if any(token in title.lower() for token in [" ii", " iii", " iv", " v", " 2", " 3", " 4", ":"]):
        sequel_penalty = 8
    originality = max(50, min(95, 80 - sequel_penalty + (5 if "roguelike" in genre_names else 0)))
    genre_impact = 60
    if metacritic >= 90:
        genre_impact += 15
    player_expression = 55
    if any(g in genre_names for g in ["rpg", "simulation", "strategy"]):
        player_expression += 20
    innovation_creativity_score = (
        originality * (5/10) +
        genre_impact * (3/10) +
        player_expression * (2/10)
    )

    # --- Community & Longevity (5%) ---
    multiplayer_online = 60  # Placeholder baseline
    community_engagement = 55
    longevity = 50 + (10 if playtime > 30 else 0) + (5 if rating > 4 else 0)
    longevity = min(90, longevity)
    community_longevity_score = (
        multiplayer_online * (2/5) +
        community_engagement * (2/5) +
        longevity * (1/5)
    )

    # --- Monetisation (informational) ---
    monetisation_notes = "Unknown / not evaluated"  # Could integrate Steam / store data later

    # --- Weighted Overall (exclude reviews & accessibility & monetisation) ---
    overall_score = (
        core_gameplay_score * 0.25 +
        story_immersion_score * 0.20 +
        presentation_score * 0.15 +
        technical_performance_score * 0.15 +
        completeness_score * 0.10 +
        innovation_creativity_score * 0.10 +
        community_longevity_score * 0.05
    )

    metacritic_count = game_data.get('metacritic_count') or 'multiple'
    data_source_note = "Note: Rubric uses heuristic estimations from RAWG data; real performance, balance, and monetisation may differ."

    reasoning = {
        "reviews_score": {
            "short": f"Metacritic (informational): {metacritic}/100",
            "detailed": f"Critic aggregate (not counted in weighted score). Source: RAWG / Metacritic. {metacritic_count} critic references."
        },
        "completeness_score": {
            "short": f"Estimated playtime: {playtime or 'Unknown'} hours",
            "detailed": "Content completeness evaluated from estimated playtime and genre scope. Longer or deeper games trend higher."
        },
        "accessibility_score": {
            "short": "Accessibility (informational)",
            "detailed": "Reported ESRB present. Advanced feature detection pending (subtitles, remapping, difficulty scaling, colorblind, screen reader, audio cues). Not counted in weighted score yet." 
        },
        "core_gameplay": {
            "short": f"Core Gameplay: {core_gameplay_score:.1f}/100",
            "detailed": {
                "mechanics_controls": mechanics_controls,
                "balance": balance,
                "replayability": replayability,
                "explanation": "Aggregated from mechanics, balance consistency, and replayability signals (genres & playtime)."}
        },
        "story_immersion": {
            "short": f"Story & Immersion: {story_immersion_score:.1f}/100",
            "detailed": {
                "narrative_quality": narrative,
                "worldbuilding": worldbuilding,
                "character_development": character_dev,
                "explanation": "Heuristic narrative estimate using genres (RPG/Adventure boost) plus critic sentiment."}
        },
        "presentation": {
            "short": f"Presentation: {presentation_score:.1f}/100",
            "detailed": {
                "graphics_art": graphics_art,
                "sound_music": sound_music,
                "immersion_factor": immersion_factor,
                "explanation": "Blends visual fidelity proxy, audio, and atmospheric cohesion."}
        },
        "technical_performance": {
            "short": f"Technical Performance: {technical_performance_score:.1f}/100",
            "detailed": {
                "frame_stability": frame_stability,
                "stability_reliability": stability_reliability,
                "optimisation": optimisation,
                "explanation": "Approximation (no direct telemetry). Uses rating, release year, and generic assumptions."}
        },
        "innovation_creativity": {
            "short": f"Innovation & Creativity: {innovation_creativity_score:.1f}/100",
            "detailed": {
                "originality": originality,
                "genre_impact": genre_impact,
                "player_expression": player_expression,
                "explanation": "Sequel detection & genre diversity heuristics."}
        },
        "community_longevity": {
            "short": f"Community & Longevity: {community_longevity_score:.1f}/100",
            "detailed": {
                "multiplayer_online": multiplayer_online,
                "community_engagement": community_engagement,
                "longevity": longevity,
                "explanation": "Placeholder scoring until explicit community metrics integrated."}
        },
        "monetisation": {
            "short": "Monetisation (informational)",
            "detailed": monetisation_notes
        },
        "overall_score": {
            "short": f"Weighted Overall: {overall_score:.1f}/100",
            "detailed": f"Weighted aggregation of rubric categories (excludes Reviews, Accessibility, Monetisation). {data_source_note}"
        }
    }

    return {
        # Legacy fields (kept for frontend compatibility; some repurposed):
        "reviews_score": round(reviews_score, 1),  # informational
        "graphic_score": round(presentation_score, 1),  # repurposed => presentation aggregate
        "microtransactions_score": round(technical_performance_score, 1),  # repurposed => technical performance
        "game_mechanics_score": round(core_gameplay_score, 1),  # repurposed => core gameplay
        "completeness_score": round(completeness_score, 1),
        "story_quality_score": round(story_immersion_score, 1),  # repurposed => story & immersion
        "accessibility_score": round(accessibility_score, 1),  # informational
        "overall_score": round(overall_score, 1),
        # New explicit category scores (added for future UI updates):
        "core_gameplay_score": round(core_gameplay_score, 1),
        "story_immersion_score": round(story_immersion_score, 1),
        "presentation_score": round(presentation_score, 1),
        "technical_performance_score": round(technical_performance_score, 1),
        "innovation_creativity_score": round(innovation_creativity_score, 1),
        "community_longevity_score": round(community_longevity_score, 1),
        "reasoning": reasoning
    }
# Initialize database on startup
# init_db()  # Removed from here - will be called in startup event

# CORS for frontend (configurable via env)
_allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
try:
    ALLOWED_ORIGINS = [o.strip() for o in _allowed.split(',') if o.strip()]
except Exception:
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple request logging middleware (debugging 404 issues)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    print(f"[REQ] {request.method} {request.url.path} -> {response.status_code} ({duration_ms} ms)")
    return response

# Custom 404 handler to list available routes when a path is not found
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        routes = []
        for r in app.router.routes:
            try:
                path = getattr(r, 'path', None)
                methods = list(getattr(r, 'methods', []) or [])
                if path and methods:
                    routes.append({"path": path, "methods": methods})
            except Exception:
                continue
        return JSONResponse(status_code=404, content={
            "detail": "Not Found",
            "requested_path": request.url.path,
            "hint": "Verify the path and HTTP method. See 'routes' for valid endpoints.",
            "routes": routes
        })
    # Fall back to default for other statuses
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
class Game(BaseModel):
    id: int
    title: str
    release_year: Optional[int] = None
    release_date: Optional[str] = None
    generation: Optional[int] = None
    platform: Optional[str] = None
    engine: Optional[str] = None
    rawg_id: Optional[int] = None
    steam_id: Optional[int] = None
    cover_image: Optional[str] = None
    platforms: Optional[List[str]] = None

class ScoreMetrics(BaseModel):
    reviews_score: float
    graphic_score: float
    microtransactions_score: float
    game_mechanics_score: float
    completeness_score: float
    story_quality_score: float
    accessibility_score: float
    overall_score: float
    reasoning: dict
    # New rubric v2 fields (optional for backward compatibility)
    core_gameplay_score: Optional[float] = None
    story_immersion_score: Optional[float] = None
    presentation_score: Optional[float] = None
    technical_performance_score: Optional[float] = None
    innovation_creativity_score: Optional[float] = None
    community_longevity_score: Optional[float] = None
    scoring_version: Optional[int] = None

class GameWithScores(BaseModel):
    game: Game
    scores: Optional[ScoreMetrics] = None

SCORING_VERSION = 2

# --- Monetisation classification helper (server-side for consistent UI)
import re
def classify_monetisation(details: dict) -> dict:
    try:
        types = details.get('types') if isinstance(details, dict) else None
        notes = details.get('notes') if isinstance(details, dict) else None
        types_list = [t for t in (types if isinstance(types, list) else []) if isinstance(t, str)]
        notes_str = notes if isinstance(notes, str) else ''
        # Combine text for simpler negation handling
        joined = (' | '.join(types_list) + ' | ' + notes_str).lower()

        # Explicit negatives
        explicit_no_mtx = (
            'no microtransaction' in joined or 'no mtx' in joined
        )
        explicit_p2w_no = (
            'p2w: no' in joined or 'no pay to win' in joined or 'no pay-to-win' in joined or 'no p2w' in joined or 'not pay to win' in joined
        )

        # Positive MTX signals (ignore negated variants like 'no loot boxes', 'no battle pass')
        has_mtx_tokens = [
            ('battle pass', not ('no battle pass' in joined)),
            ('item shop', True),
            ('microtransaction', not ('no microtransaction' in joined)),
            (' mtx', not ('no mtx' in joined)),
            ('in-app', True),
            (' iap', True),
            ('loot box', not ('no loot box' in joined) and not ('no loot boxes' in joined)),
            ('gacha', True)
        ]
        has_mtx = any(tok in joined and cond for tok, cond in has_mtx_tokens)

        # Positive P2W signals; avoid negations. If explicit_p2w_no, treat as not P2W.
        if explicit_p2w_no:
            has_p2w = False
        else:
            # Consider flexible negations like 'no explicit pay-to-win' or 'not pay to win'
            negated_pay_to_win = bool(re.search(r'(no|not|without)\s+(?:\w+\s+){0,3}pay\s*-?to\s*-?win', joined)) or 'no p2w' in joined
            mentions_pay_to_win = (('pay-to-win' in joined) or ('pay to win' in joined))
            tactic_hits = any(tok in joined for tok in ['gameplay advantage','stat boost','xp boost','xp advantage','power boost'])
            has_p2w = (
                ('p2w: yes' in joined) or
                (mentions_pay_to_win and not negated_pay_to_win) or
                tactic_hits
            )

        if has_p2w:
            return {"label": "Poor", "color": "#c0392b"}
        if explicit_no_mtx or (not has_mtx and not has_p2w):
            # Perfect -> Sky Blue
            return {"label": "Perfect", "color": "#00bfff"}
        if has_mtx and (explicit_p2w_no or not has_p2w):
            # Fair -> Purple
            return {"label": "Fair", "color": "#8e44ad"}
        return {"label": "Unknown", "color": "#7f8c8d"}
    except Exception:
        return {"label": "Unknown", "color": "#7f8c8d"}

def infer_monetisation_heuristic(rawg_details: dict | None, steam_data: dict | None) -> dict | None:
    """Infer monetisation using lightweight heuristics from RAWG details and Steam categories.
    Returns a dict suitable for classify_monetisation with keys: types (list[str]), notes (str), tactics (list[str]).
    """
    try:
        types: list[str] = []
        notes_parts: list[str] = []
        text_blobs: list[str] = []
        if isinstance(rawg_details, dict) and rawg_details:
            desc = rawg_details.get('description_raw') or rawg_details.get('description') or ''
            text_blobs.append(desc)
            tag_names = [t.get('name') for t in (rawg_details.get('tags') or []) if isinstance(t, dict) and t.get('name')]
            if tag_names:
                text_blobs.append(' '.join(tag_names))
            genre_names = [g.get('name') for g in (rawg_details.get('genres') or []) if isinstance(g, dict) and g.get('name')]
            if genre_names:
                text_blobs.append(' '.join(genre_names))
        if isinstance(steam_data, dict) and steam_data:
            # Steam categories sometimes include 'In-App Purchases'
            cats = steam_data.get('categories') or []
            if isinstance(cats, list):
                for c in cats:
                    try:
                        d = (c.get('description') or '').strip().lower()
                        if 'in-app' in d or 'in app' in d or 'in app purchases' in d or 'in-app purchases' in d:
                            types.append('In-App Purchases')
                    except Exception:
                        continue
            # some games mention monetisation in short_description
            sd = steam_data.get('short_description') or ''
            text_blobs.append(sd)
        blob = ('\n'.join(text_blobs)).lower()
        if not blob and not types:
            return None

        # Signal detection
        def has(*keywords: str) -> bool:
            return any(k in blob for k in keywords)

        # Strong signals
        if has('ultimate team', 'fut'):
            types.extend(['Ultimate Team (FUT-like)', 'Packs/Player Cards'])
            notes_parts.append('Ultimate Team/card packs present; online modes may be affected by spend.')
        if has('battle pass'):
            types.append('Battle Pass')
        if has('item shop', 'storefront', 'cash shop'):
            types.append('Item Shop')
        if has('loot box', 'lootbox', 'loot boxes', 'gacha'):
            types.append('Loot Boxes')
        if has('in-app purchases', 'in app purchases', 'in-app purchase', 'in app purchase', 'microtransactions', 'micro-transaction', 'micro transactions'):
            types.append('Microtransactions')
        if has('season pass'):
            types.append('Season Pass')

        # P2W vs cosmetic-only cues (also collect specific tactic signals)
        tactic_map = [
            ('gameplay advantage', 'gameplay advantage'),
            ('stat boost', 'stat boost'),
            ('xp boost', 'xp boost'),
            ('xp advantage', 'xp advantage'),
            ('power boost', 'power boost'),
            ('competitive advantage', 'competitive advantage'),
        ]
        tactics: list[str] = []
        for key, label in tactic_map:
            if key in blob:
                tactics.append(label)
        p2w_explicit = has('pay-to-win', 'pay to win') or bool(tactics)
        cosmetic_only = has('cosmetic only', 'cosmetics only', 'purely cosmetic', 'cosmetic items only')
        if p2w_explicit:
            types.append('P2W: Yes')
            notes_parts.append('Text mentions gameplay advantage from spend.')
        elif cosmetic_only and types:
            types.append('P2W: No')
            types.append('Cosmetic MTX')
            notes_parts.append('Text indicates cosmetics only; no gameplay edge.')
        elif types:
            # Monetisation present but fairness unclear; do NOT mark as P2W without signals
            notes_parts.append('Monetisation present; no explicit pay-to-win signals in text.')
        else:
            # No signals
            return None

        # Deduplicate and normalise
        out_types = []
        seen = set()
        for t in types:
            if not isinstance(t, str):
                continue
            tt = t.strip()
            if tt and tt not in seen:
                out_types.append(tt)
                seen.add(tt)
        notes = ' '.join(notes_parts).strip() or None
        return {'types': out_types, 'notes': notes, 'tactics': tactics}
    except Exception:
        return None

@app.get("/api/games/search", response_model=List[Game])
async def search_games(q: str, page: int = 1, page_size: int = 10):
    """Search games via RAWG API with pagination and store minimal metadata locally.

    NOTE: This endpoint requires 'q'. A 404 elsewhere usually means wrong path or server not running 'main.py'.
    Returns empty list if 'q' is blank (handled before invoking RAWG).
    """
    if not q:
        return []
    rawg_results = rawg_client.search_games(q, page_size=page_size, page=page)
    games: List[Game] = []
    with get_db() as conn:
        results_list = rawg_results.get("results", []) if isinstance(rawg_results, dict) else []
        for game_data in results_list:
            rawg_id = game_data.get("id")
            title = game_data.get("name", "Unknown Title")
            platform = "multi-platform"
            cover_image = game_data.get("background_image")
            # release date/year from RAWG 'released' (YYYY-MM-DD)
            release_year = None
            release_date = None
            try:
                rel = game_data.get("released")
                if isinstance(rel, str) and len(rel) >= 4:
                    release_year = int(rel[:4])
                    release_date = rel
            except Exception:
                release_year = None
                release_date = None
            # Extract platform names list from RAWG structure
            platform_names: List[str] = []
            raw_platforms = game_data.get("platforms") or []
            if isinstance(raw_platforms, list):
                for p in raw_platforms:
                    # RAWG returns [{'platform': {'id':..,'name':..}, 'released_at':..., ...}, ...]
                    if isinstance(p, dict):
                        plat_obj = p.get('platform')
                        if isinstance(plat_obj, dict):
                            name = plat_obj.get('name')
                            if isinstance(name, str):
                                platform_names.append(name)
                        else:
                            name = p.get('name')
                            if isinstance(name, str):
                                platform_names.append(name)
            # For legacy single platform column store first platform if available
            single_platform = platform_names[0] if platform_names else platform
            conn.execute("""
                INSERT OR IGNORE INTO games (title, rawg_id, platform, cover_image, release_year, release_date, release_date_source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (title, rawg_id, single_platform, cover_image, release_year, release_date, 'rawg'))
            if cover_image:
                conn.execute("""
                    UPDATE games SET cover_image = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE rawg_id = ? AND (cover_image IS NULL OR cover_image = '')
                """, (cover_image, rawg_id))
            if release_year:
                conn.execute(
                    "UPDATE games SET release_year = ?, updated_at = CURRENT_TIMESTAMP WHERE rawg_id = ? AND (release_year IS NULL)",
                    (release_year, rawg_id)
                )
            if release_date:
                conn.execute(
                    "UPDATE games SET release_date = ?, release_date_source = COALESCE(release_date_source, 'rawg'), updated_at = CURRENT_TIMESTAMP WHERE rawg_id = ? AND (release_date IS NULL)",
                    (release_date, rawg_id)
                )
            if single_platform and single_platform != platform:
                conn.execute("""
                    UPDATE games SET platform = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE rawg_id = ? AND (platform IS NULL OR platform = 'multi-platform')
                """, (single_platform, rawg_id))
            row = conn.execute("SELECT * FROM games WHERE rawg_id = ?", (rawg_id,)).fetchone()
            if row:
                gdict = dict(row)
                gdict['platforms'] = platform_names if platform_names else None
                games.append(Game(**gdict))
        conn.commit()
        # Local search fallback when RAWG gives no results (offline)
        if not games:
            try:
                like = f"%{q}%"
                offset = max(0, (page - 1) * page_size)
                rows = conn.execute(
                    "SELECT * FROM games WHERE title LIKE ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                    (like, page_size, offset)
                ).fetchall()
                for row in rows:
                    gdict = dict(row)
                    gdict['platforms'] = None
                    games.append(Game(**gdict))
            except Exception:
                pass
    return games

@app.get("/api/games/search-details")
async def search_games_with_details(q: str, page: int = 1, page_size: int = 5):
    """Search games and return minimal DB game info (including id) plus RAWG details.

    Returns a list of objects: [{ game: Game, details: {...} }]
    The RAWG details are trimmed to the most relevant fields to keep payload light.
    """
    if not q:
        return []
    # Reuse existing search to ensure DB is populated and consistent
    results = await search_games(q=q, page=page, page_size=page_size)
    items = []
    for g in results:
        try:
            rawg_id = getattr(g, 'rawg_id', None)
            details = rawg_client.get_game_details(rawg_id) if rawg_id else {}
            # Trim/normalize details to a compact shape
            det = {}
            if isinstance(details, dict) and details:
                genres = [d.get('name') for d in (details.get('genres') or []) if isinstance(d, dict) and d.get('name')]
                platforms = []
                raw_platforms = details.get('parent_platforms') or details.get('platforms') or []
                if isinstance(raw_platforms, list):
                    for p in raw_platforms:
                        if isinstance(p, dict):
                            # RAWG sometimes nests under 'platform'
                            po = p.get('platform') if 'platform' in p else p
                            if isinstance(po, dict) and isinstance(po.get('name'), str):
                                platforms.append(po['name'])
                det = {
                    'id': details.get('id'),
                    'name': details.get('name'),
                    'slug': details.get('slug'),
                    'released': details.get('released'),
                    'updated': details.get('updated') or details.get('updated_at'),
                    'metacritic': details.get('metacritic'),
                    'rating': details.get('rating'),
                    'playtime': details.get('playtime'),
                    'genres': genres,
                    'background_image': details.get('background_image'),
                    'esrb_rating': (details.get('esrb_rating') or {}).get('name') if isinstance(details.get('esrb_rating'), dict) else details.get('esrb_rating'),
                    'platforms': platforms or None,
                }
                # Include a short description excerpt if available
                desc = details.get('description_raw') or details.get('description')
                if isinstance(desc, str) and desc:
                    # Keep it short to avoid large payloads
                    det['description_excerpt'] = desc[:400] + ('…' if len(desc) > 400 else '')
            items.append({
                'game': g,
                'details': det
            })
        except Exception as _e:
            items.append({ 'game': g, 'details': {} })
    return items

@app.get("/api/search/games")
async def api_search_games_with_details(q: str, page: int = 1, page_size: int = 5):
    """Alias endpoint to search games by title and return DB id + compact RAWG details.
    This path avoids any collision with /api/games/{game_id} routes.
    """
    return await search_games_with_details(q=q, page=page, page_size=page_size)

@app.get("/api/games/{game_id}/rawg-details")
async def get_game_rawg_details(game_id: int, refresh: bool = False):
    """Return RAWG details for a game, serving from local snapshot when available.

    If refresh=true, attempts to fetch fresh details and update the snapshot; otherwise returns snapshot first.
    """
    def normalize(raw: dict) -> dict:
        desc = raw.get('description_raw') or raw.get('description') or None
        if isinstance(desc, str):
            desc = desc if len(desc) <= 8000 else (desc[:8000] + '…')
        genres = [d.get('name') for d in (raw.get('genres') or []) if isinstance(d, dict) and d.get('name')]
        developers = [d.get('name') for d in (raw.get('developers') or []) if isinstance(d, dict) and d.get('name')]
        publishers = [d.get('name') for d in (raw.get('publishers') or []) if isinstance(d, dict) and d.get('name')]
        esrb = None
        er = raw.get('esrb_rating')
        if isinstance(er, dict):
            esrb = er.get('name')
        elif isinstance(er, str):
            esrb = er
        return {
            'description': desc,
            'genres': genres or [],
            'developers': developers or [],
            'publishers': publishers or [],
            'age_rating': esrb
        }

    with get_db() as conn:
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        # Serve snapshot if present and not forcing refresh
        if not refresh:
            snap = conn.execute("SELECT description, genres_json, developers_json, publishers_json, age_rating FROM rawg_detail_snapshots WHERE game_id = ?", (game_id,)).fetchone()
            if snap:
                try:
                    return {
                        'description': snap[0],
                        'genres': json.loads(snap[1] or '[]'),
                        'developers': json.loads(snap[2] or '[]'),
                        'publishers': json.loads(snap[3] or '[]'),
                        'age_rating': snap[4]
                    }
                except Exception:
                    pass
        rawg_id = dict(game).get('rawg_id')
        if not rawg_id:
            return {'description': None, 'genres': [], 'developers': [], 'publishers': [], 'age_rating': None}
        # Try to fetch from RAWG and persist snapshot
        try:
            details = rawg_client.get_game_details(rawg_id) or {}
            if not isinstance(details, dict):
                details = {}
            norm = normalize(details)
            conn.execute(
                "REPLACE INTO rawg_detail_snapshots (game_id, description, genres_json, developers_json, publishers_json, age_rating, updated_at) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP)",
                (game_id, norm['description'], json.dumps(norm['genres']), json.dumps(norm['developers']), json.dumps(norm['publishers']), norm['age_rating'])
            )
            conn.commit()
            return norm
        except Exception:
            # If offline and snapshot exists, return it; else empty
            snap2 = conn.execute("SELECT description, genres_json, developers_json, publishers_json, age_rating FROM rawg_detail_snapshots WHERE game_id = ?", (game_id,)).fetchone()
            if snap2:
                try:
                    return {
                        'description': snap2[0],
                        'genres': json.loads(snap2[1] or '[]'),
                        'developers': json.loads(snap2[2] or '[]'),
                        'publishers': json.loads(snap2[3] or '[]'),
                        'age_rating': snap2[4]
                    }
                except Exception:
                    pass
            return {'description': None, 'genres': [], 'developers': [], 'publishers': [], 'age_rating': None}

@app.post("/api/games/{game_id}/scan")
async def scan_game(game_id: int, force: bool = False, apply_defaults: bool = False):
    with get_db() as conn:
        # Check if game exists
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Check if scores already exist
        scores = conn.execute("SELECT * FROM scores WHERE game_id = ?", (game_id,)).fetchone()
        # Honor 'force' flag: only early return if not forcing recomputation
        if scores and not force:
            score_dict = dict(scores)
            try:
                score_dict["reasoning"] = json.loads(score_dict["reasoning"])
            except Exception:
                pass
            # Auto-refresh monetisation here too so rescans upgrade Unknown without forcing
            try:
                mon = (score_dict.get('reasoning') or {}).get('monetisation')
                det = (mon or {}).get('detailed') if isinstance(mon, dict) else None
                label = (det or {}).get('fairness_label') if isinstance(det, dict) else None
                needs_refresh = (not label) or (str(label).lower() == 'unknown')
                if needs_refresh:
                    # Fetch RAWG/Steam for heuristic
                    rawg_id2 = dict(game).get('rawg_id')
                    rawg_details2 = rawg_client.get_game_details(rawg_id2) if rawg_id2 else {}
                    try:
                        steam_id2 = dict(game).get('steam_id')
                    except Exception:
                        steam_id2 = None
                    steam_data2 = steam_client.get_app_details(steam_id2) if steam_id2 else {}
                    inferred = infer_monetisation_heuristic(rawg_details2, steam_data2)
                    if inferred:
                        fair = classify_monetisation(inferred)
                        score_dict.setdefault('reasoning', {})['monetisation'] = {
                            'short': 'Monetisation (inferred heuristic)',
                            'detailed': {
                                'types': inferred.get('types', []),
                                'notes': inferred.get('notes'),
                                'tactics': inferred.get('tactics') or [],
                                'fairness_label': fair.get('label'),
                                'fairness_color': fair.get('color'),
                                'fairness_source': 'heuristic',
                                'confidence': 0.5
                            }
                        }
                    else:
                        # Defaults to avoid Unknown
                        is_free = False
                        try:
                            if isinstance(steam_data2, dict) and steam_data2:
                                is_free = bool(steam_data2.get('is_free'))
                        except Exception:
                            is_free = False
                        ftplay_text = ''
                        try:
                            ftplay_text = ((rawg_details2.get('description_raw') or rawg_details2.get('description') or '') + ' ' + ' '.join([t.get('name','') for t in (rawg_details2.get('tags') or []) if isinstance(t, dict)])).lower()
                        except Exception:
                            pass
                        has_f2p_cues = is_free or ('free to play' in ftplay_text) or ('free-to-play' in ftplay_text)
                        if has_f2p_cues:
                            assumed = {'types': ['In-App Purchases'], 'notes': 'Defaulted from Free-to-Play cues; MTX typical, fairness assumed.'}
                            fair = classify_monetisation(assumed)
                            score_dict.setdefault('reasoning', {})['monetisation'] = {
                                'short': 'Monetisation (assumed from F2P)',
                                'detailed': {
                                    'types': assumed['types'],
                                    'notes': assumed['notes'],
                                    'fairness_label': fair.get('label'),
                                    'fairness_color': fair.get('color'),
                                    'fairness_source': 'assumed-f2p',
                                    'confidence': 0.45
                                }
                            }
                        else:
                            assumed = {'types': [], 'notes': 'No monetisation signals detected from public info; treated as none until proven otherwise.'}
                            fair = classify_monetisation(assumed)
                            score_dict.setdefault('reasoning', {})['monetisation'] = {
                                'short': 'Monetisation (no signals found)',
                                'detailed': {
                                    'types': assumed['types'],
                                    'notes': assumed['notes'],
                                    'fairness_label': fair.get('label'),
                                    'fairness_color': fair.get('color'),
                                    'fairness_source': 'assumed-default',
                                    'confidence': 0.35
                                }
                            }
                    # Persist upgrade
                    conn.execute("UPDATE scores SET reasoning = ?, updated_at = CURRENT_TIMESTAMP WHERE game_id = ?", (json.dumps(score_dict['reasoning']), game_id))
                    conn.commit()
            except Exception:
                pass
            return {"status": "completed", "scores": score_dict}

        # Get detailed game data from RAWG API
        game_dict = dict(game)
        rawg_id = game_dict.get("rawg_id")
        # Prepare containers so we can apply monetisation defaults even without RAWG/Steam
        rawg_details = {}
        steam_data = {}
        steam_id = None

        community_telemetry = None
        if rawg_id:
            # Telemetry reuse check
            existing_tel = conn.execute("SELECT * FROM game_community_telemetry WHERE game_id = ?", (game_id,)).fetchone()
            reuse_telemetry = False
            if existing_tel:
                try:
                    last_scan_at = datetime.fromisoformat(existing_tel['last_scan_at'])
                    if (datetime.utcnow() - last_scan_at).total_seconds() < COMMUNITY_TELEMETRY_TTL and not force:
                        reuse_telemetry = True
                except Exception:
                    pass
            # Get detailed game data from RAWG (needed for scoring even if reusing telemetry snapshot) - cached by RAWG client
            rawg_details = rawg_client.get_game_details(rawg_id)
            # Backfill release_year on the games table if missing
            try:
                if game_dict.get('release_year') is None:
                    rel = rawg_details.get('released') if isinstance(rawg_details, dict) else None
                    year = None
                    if isinstance(rel, str) and len(rel) >= 4:
                        try:
                            year = int(rel[:4])
                        except Exception:
                            year = None
                    if year:
                        conn.execute("UPDATE games SET release_year = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND (release_year IS NULL)", (year, game_id))
                        conn.commit()
                        game_dict['release_year'] = year
                # Backfill full release_date if missing
                if game_dict.get('release_date') is None:
                    rel_full = rawg_details.get('released') if isinstance(rawg_details, dict) else None
                    if isinstance(rel_full, str) and len(rel_full) >= 4:
                        conn.execute("UPDATE games SET release_date = ?, release_date_source = COALESCE(release_date_source, 'rawg'), updated_at = CURRENT_TIMESTAMP WHERE id = ? AND (release_date IS NULL)", (rel_full, game_id))
                        conn.commit()
                        game_dict['release_date'] = rel_full
            except Exception as _e:
                pass

            # Debug logging for data verification
            print(f"RAWG data for game {rawg_id}: Metacritic={rawg_details.get('metacritic')}, Rating={rawg_details.get('rating')}")

            # Try to get Steam data if steam_id exists
            steam_id = game_dict.get("steam_id")
            if steam_id:
                steam_data = steam_client.get_app_details(steam_id)

            # Persist RAWG detail snapshot for offline serving
            try:
                desc = rawg_details.get('description_raw') or rawg_details.get('description') if isinstance(rawg_details, dict) else None
                if isinstance(desc, str) and len(desc) > 8000:
                    desc = desc[:8000] + '…'
                genres = [d.get('name') for d in (rawg_details.get('genres') or []) if isinstance(d, dict) and d.get('name')] if isinstance(rawg_details, dict) else []
                developers = [d.get('name') for d in (rawg_details.get('developers') or []) if isinstance(d, dict) and d.get('name')] if isinstance(rawg_details, dict) else []
                publishers = [d.get('name') for d in (rawg_details.get('publishers') or []) if isinstance(d, dict) and d.get('name')] if isinstance(rawg_details, dict) else []
                esrb = None
                er = rawg_details.get('esrb_rating') if isinstance(rawg_details, dict) else None
                if isinstance(er, dict):
                    esrb = er.get('name')
                elif isinstance(er, str):
                    esrb = er
                conn.execute(
                    "REPLACE INTO rawg_detail_snapshots (game_id, description, genres_json, developers_json, publishers_json, age_rating, updated_at) VALUES (?,?,?,?,?,?, CURRENT_TIMESTAMP)",
                    (game_id, desc, json.dumps(genres or []), json.dumps(developers or []), json.dumps(publishers or []), esrb)
                )
                conn.commit()
            except Exception as e:
                print(f"RAWG snapshot persist error: {e}")

            # Persist / compute community telemetry BEFORE generating scores so we can override placeholders
            try:
                if reuse_telemetry:
                    # Build telemetry dict from existing row for application
                    community_telemetry = {
                        'ratings_count': existing_tel['ratings_count'],
                        'added_count': existing_tel['added_count'],
                        'updated_rawg_at': existing_tel['updated_rawg_at'],
                        'steam_ccu': existing_tel['steam_ccu'],
                        'steam_reviews_total': existing_tel['steam_reviews_total'],
                        'multiplayer_online': None,  # will be recomputed below to reflect new scaling if code changed
                        'community_engagement': None,
                        'longevity': None,
                        'confidence_score': existing_tel['confidence_score']
                    }
                    # Recompute scoring-facing submetrics from stored base counts so scaling changes propagate
                    recomputed = recompute_telemetry_submetrics(community_telemetry)
                    community_telemetry.update(recomputed)
                else:
                    community_telemetry = compute_and_store_community_telemetry(conn, game_id, rawg_details, steam_id=game_dict.get('steam_id'))
            except Exception as ct_e:
                print(f"Community telemetry error: {ct_e}")

            # Generate scores from API data (will overwrite community_longevity with placeholder values we may later refine)
            score_data = generate_scores_from_api(rawg_details, steam_data)

            # MVP enrichment: LLM-backed innovation if enabled, else heuristic; accessibility features; life support inference
            try:
                innov_llm = None
                if USE_LLM_INNOVATION:
                    innov_llm = llm_innovation_score(game_id, rawg_details)
                if innov_llm and innov_llm.get('overall_score') is not None:
                    score_data['innovation_creativity_score'] = round(float(innov_llm['overall_score']),1)
                    score_data.setdefault('reasoning', {}).setdefault('innovation_creativity', {
                        'short': 'Innovation & Creativity (LLM-assessed)',
                        'detailed': {}
                    })
                    det = score_data['reasoning']['innovation_creativity'].setdefault('detailed', {})
                    det.update(innov_llm.get('summary', {}))
                else:
                    innov = compute_innovation_metrics(game_id, rawg_details)
                    if innov.get('adjusted_score') is not None:
                        orig_innov = score_data.get('innovation_creativity_score') or 0
                        blended = round(orig_innov*0.8 + innov['adjusted_score']*0.2,1)
                        score_data['innovation_creativity_score'] = blended
                        score_data.setdefault('reasoning', {}).setdefault('innovation_creativity', {
                            'short': 'Innovation & Creativity heuristic augmented',
                            'detailed': {}
                        })
                        det = score_data['reasoning']['innovation_creativity'].setdefault('detailed', {})
                        det.update(innov.get('summary', {}))
                        det['blended_score'] = blended
                        det['heuristic_component'] = innov['adjusted_score']
            except Exception as e:
                print(f"Innovation enrichment error: {e}")
            try:
                acc = infer_accessibility_features(game_id, rawg_details)
                if acc.get('heuristic_score') is not None:
                    # Soft blend into informational accessibility score (not weighted): 70% existing + 30% heuristic
                    score_data['accessibility_score'] = round(score_data.get('accessibility_score',70)*0.7 + acc['heuristic_score']*0.3,1)
                    score_data.setdefault('reasoning', {}).setdefault('accessibility_score', {
                        'short': 'Accessibility heuristic augmented',
                        'detailed': {}
                    })
                    ad = score_data['reasoning']['accessibility_score'].setdefault('detailed', {})
                    ad['heuristic_features'] = acc.get('features')
                    ad['heuristic_confidence'] = acc.get('confidence')
                    ad['heuristic_score_component'] = acc.get('heuristic_score')
            except Exception as e:
                print(f"Accessibility heuristic error: {e}")
            # Heuristic monetisation inference if no override present
            try:
                # If the current score_data has only a placeholder/unknown monetisation, try to enrich
                mon = score_data.get('reasoning', {}).get('monetisation')
                mon_det = (mon or {}).get('detailed') if isinstance(mon, dict) else None
                existing_fairness = (mon_det or {}).get('fairness_label') if isinstance(mon_det, dict) else None
                if not existing_fairness:
                    inferred = infer_monetisation_heuristic(rawg_details, steam_data)
                    if inferred:
                        fair = classify_monetisation(inferred)
                        score_data.setdefault('reasoning', {})['monetisation'] = {
                            'short': 'Monetisation (inferred heuristic)',
                            'detailed': {
                                'types': inferred.get('types', []),
                                'notes': inferred.get('notes'),
                                'tactics': inferred.get('tactics') or [],
                                'fairness_label': fair.get('label'),
                                'fairness_color': fair.get('color'),
                                'fairness_source': 'heuristic',
                                'confidence': 0.5
                            }
                        }
                    else:
                        # No signals found: choose a sensible default to avoid 'Unknown'
                        # If Free-to-Play cues exist, assume MTX present but no explicit P2W -> Fair (low confidence)
                        is_free = False
                        try:
                            if isinstance(steam_data, dict) and steam_data:
                                is_free = bool(steam_data.get('is_free'))
                        except Exception:
                            is_free = False
                        ftplay_text = ''
                        try:
                            ftplay_text = ((rawg_details.get('description_raw') or rawg_details.get('description') or '') + ' ' + ' '.join([t.get('name','') for t in (rawg_details.get('tags') or []) if isinstance(t, dict)])).lower()
                        except Exception:
                            pass
                        has_f2p_cues = is_free or ('free to play' in ftplay_text) or ('free-to-play' in ftplay_text)
                        if has_f2p_cues:
                            assumed = {'types': ['In-App Purchases'], 'notes': 'Defaulted from Free-to-Play cues; MTX typical, fairness assumed.'}
                            fair = classify_monetisation(assumed)
                            score_data.setdefault('reasoning', {})['monetisation'] = {
                                'short': 'Monetisation (assumed from F2P)',
                                'detailed': {
                                    'types': assumed['types'],
                                    'notes': assumed['notes'],
                                    'fairness_label': fair.get('label'),
                                    'fairness_color': fair.get('color'),
                                    'fairness_source': 'assumed-f2p',
                                    'confidence': 0.45
                                }
                            }
                        else:
                            # No F2P cues and no signals -> assume none present for now (Perfect, low confidence)
                            assumed = {'types': [], 'notes': 'No monetisation signals detected from public info; treated as none until proven otherwise.'}
                            fair = classify_monetisation(assumed)
                            score_data.setdefault('reasoning', {})['monetisation'] = {
                                'short': 'Monetisation (no signals found)',
                                'detailed': {
                                    'types': assumed['types'],
                                    'notes': assumed['notes'],
                                    'fairness_label': fair.get('label'),
                                    'fairness_color': fair.get('color'),
                                    'fairness_source': 'assumed-default',
                                    'confidence': 0.35
                                }
                            }
            except Exception as e:
                print(f"Monetisation heuristic error: {e}")
            # Normalize monetisation block to structured default if not overridden later
            try:
                mon = score_data.get('reasoning', {}).get('monetisation')
                if isinstance(mon, dict):
                    det = mon.get('detailed')
                    if isinstance(det, str):
                        score_data['reasoning']['monetisation']['detailed'] = {
                            'types': [],
                            'notes': det,
                            'fairness_label': 'Unknown',
                            'fairness_color': '#7f8c8d',
                            'fairness_source': 'none',
                            'confidence': 0.3
                        }
            except Exception:
                pass
            try:
                inferred_ls = infer_life_support_status(game_id, rawg_details, community_telemetry)
                score_data.setdefault('reasoning', {}).setdefault('life_support_inferred', {
                    'short': f"Inferred Life Support: {inferred_ls.get('status')} (conf {inferred_ls.get('confidence')})",
                    'detailed': inferred_ls
                })
            except Exception as e:
                print(f"Life support inference error: {e}")

            # Recompute overall after possible innovation score adjustment
            try:
                overall = (
                    score_data['core_gameplay_score'] * 0.25 +
                    score_data['story_immersion_score'] * 0.20 +
                    score_data['presentation_score'] * 0.15 +
                    score_data['technical_performance_score'] * 0.15 +
                    score_data['completeness_score'] * 0.10 +
                    score_data['innovation_creativity_score'] * 0.10 +
                    score_data['community_longevity_score'] * 0.05
                )
                score_data['overall_score'] = round(overall,1)
                if 'overall_score' in score_data.get('reasoning', {}):
                    score_data['reasoning']['overall_score']['short'] = f"Weighted Overall: {overall:.1f}/100"
            except Exception as e:
                print(f"Overall recompute after innovation error: {e}")

            # If telemetry exists, recalc community longevity sub-metrics using real-ish signals
            if community_telemetry:
                try:
                    score_data = apply_community_longevity_telemetry(score_data, community_telemetry)
                except Exception as e:
                    print(f"Apply telemetry to community longevity failed: {e}")

            # Attempt to augment accessibility score using CIPT reviews (scrape)
            try:
                existing_rev = conn.execute("SELECT * FROM accessibility_reviews WHERE game_id = ?", (game_id,)).fetchone()
                if existing_rev:
                    # Use cached review to adjust accessibility
                    raw_score = existing_rev[3]
                    if raw_score:
                        # Blend: 70% existing accessibility score + 30% CIPT normalized
                        score_data['accessibility_score'] = round(score_data['accessibility_score'] * 0.7 + (raw_score) * 0.3, 1)
                        acc_det = score_data['reasoning']['accessibility_score'].get('detailed')
                        if isinstance(acc_det, str):
                            score_data['reasoning']['accessibility_score']['detailed'] = acc_det + " CIPT review data incorporated (cached)."
                        elif isinstance(acc_det, dict):
                            score_data['reasoning']['accessibility_score']['detailed']['note'] = (
                                str(score_data['reasoning']['accessibility_score']['detailed'].get('note','')) + " CIPT review data incorporated (cached)."
                            ).strip()
                else:
                    # Search and parse first review
                    reviews = cipt_client.search_reviews(game_dict.get('title', ''))
                    if reviews:
                        review_data = cipt_client.extract_accessibility_score(reviews[0]['url'])
                        if review_data:
                            conn.execute("""
                                INSERT INTO accessibility_reviews (game_id, source_url, raw_score, max_score, features_json)
                                VALUES (?, ?, ?, ?, ?)
                            """, (game_id, review_data['source'], review_data['raw_score'], review_data['max_score'], json.dumps(review_data['features'])))
                            # Blend and annotate
                            score_data['accessibility_score'] = round(score_data['accessibility_score'] * 0.6 + review_data['raw_score'] * 0.4, 1)
                            acc_det2 = score_data['reasoning']['accessibility_score'].get('detailed')
                            if isinstance(acc_det2, str):
                                score_data['reasoning']['accessibility_score']['detailed'] = acc_det2 + " CIPT review analysis blended (heuristic)."
                            elif isinstance(acc_det2, dict):
                                score_data['reasoning']['accessibility_score']['detailed']['note'] = (
                                    str(score_data['reasoning']['accessibility_score']['detailed'].get('note','')) + " CIPT review analysis blended (heuristic)."
                                ).strip()
            except Exception as e:
                print(f"CIPT augmentation error: {e}")
        else:
            # Fallback for games without RAWG ID (use mock data structure)
            mock_rawg_data = {
                "metacritic": 80,
                "rating": 4.0,
                "released": "2020-01-01",
                "playtime": 15,
                "genres": [{"name": "Action"}],
                "esrb_rating": {"name": "E10+"}
            }
            score_data = generate_scores_from_api(mock_rawg_data)

        # Final safeguard: ensure monetisation is not left as Unknown even if heuristics above didn't run
        try:
            mon = score_data.get('reasoning', {}).get('monetisation')
            det = (mon or {}).get('detailed') if isinstance(mon, dict) else None
            label = (det or {}).get('fairness_label') if isinstance(det, dict) else None
            needs_fix = (not label) or (str(label).lower() == 'unknown')
            if needs_fix:
                inferred2 = infer_monetisation_heuristic(rawg_details or {}, steam_data or {})
                if inferred2:
                    fair2 = classify_monetisation(inferred2)
                    score_data.setdefault('reasoning', {})['monetisation'] = {
                        'short': 'Monetisation (inferred heuristic)',
                        'detailed': {
                            'types': inferred2.get('types', []),
                            'notes': inferred2.get('notes'),
                            'tactics': inferred2.get('tactics') or [],
                            'fairness_label': fair2.get('label'),
                            'fairness_color': fair2.get('color'),
                            'fairness_source': 'heuristic',
                            'confidence': 0.5
                        }
                    }
                else:
                    # Apply defaults: F2P cues => assume IAP; else assume none
                    is_free = False
                    try:
                        if isinstance(steam_data, dict) and steam_data:
                            is_free = bool(steam_data.get('is_free'))
                    except Exception:
                        is_free = False
                    ftplay_text = ''
                    try:
                        ftplay_text = ((rawg_details.get('description_raw') or rawg_details.get('description') or '') + ' ' + ' '.join([t.get('name','') for t in (rawg_details.get('tags') or []) if isinstance(t, dict)])).lower()
                    except Exception:
                        pass
                    has_f2p_cues = is_free or ('free to play' in ftplay_text) or ('free-to-play' in ftplay_text)
                    if has_f2p_cues:
                        assumed = {'types': ['In-App Purchases'], 'notes': 'Defaulted from Free-to-Play cues; MTX typical, fairness assumed.'}
                        fair2 = classify_monetisation(assumed)
                        score_data.setdefault('reasoning', {})['monetisation'] = {
                            'short': 'Monetisation (assumed from F2P)',
                            'detailed': {
                                'types': assumed['types'],
                                'notes': assumed['notes'],
                                'fairness_label': fair2.get('label'),
                                'fairness_color': fair2.get('color'),
                                'fairness_source': 'assumed-f2p',
                                'confidence': 0.45
                            }
                        }
                    else:
                        assumed = {'types': [], 'notes': 'No monetisation signals detected from public info; treated as none until proven otherwise.'}
                        fair2 = classify_monetisation(assumed)
                        score_data.setdefault('reasoning', {})['monetisation'] = {
                            'short': 'Monetisation (no signals found)',
                            'detailed': {
                                'types': assumed['types'],
                                'notes': assumed['notes'],
                                'fairness_label': fair2.get('label'),
                                'fairness_color': fair2.get('color'),
                                'fairness_source': 'assumed-default',
                                'confidence': 0.35
                            }
                        }
        except Exception:
            pass

        # Auto-apply monetisation defaults if game title matches known patterns (only if no manual override exists)
        game_title = game_dict.get('title', '')
        try:
            apply_monetisation_overrides_if_match(conn, game_id, game_title)
            conn.commit()
        except Exception as e:
            print(f"Auto monetisation override failed for game {game_id}: {e}")

        # Optionally auto-apply monetisation defaults using franchise patterns if explicitly enabled.
        # This is OFF by default to avoid mislabeling future sequels; enable via env AUTO_MONETISATION_DEFAULTS=1
        # or per-scan query param apply_defaults=true.
        try:
            if AUTO_MONETISATION_DEFAULTS or apply_defaults:
                game_title = game_dict.get('title', '')
                try:
                    applied = apply_monetisation_overrides_if_match(conn, game_id, game_title)
                    if applied:
                        conn.commit()
                except Exception as e:
                    print(f"Auto monetisation override failed for game {game_id}: {e}")
        except NameError:
            # helper may not exist in older deployments
            pass

        # Apply overrides if present
        override_row = conn.execute("SELECT * FROM score_overrides WHERE game_id = ?", (game_id,)).fetchone()
        if override_row:
            try:
                monetisation_types = json.loads(override_row['monetisation_types']) if override_row['monetisation_types'] else []
            except Exception:
                monetisation_types = []
            try:
                performance_json = json.loads(override_row['performance_json']) if override_row['performance_json'] else {}
            except Exception:
                performance_json = {}
            # Override technical performance submetrics if provided
            changed_tp = False
            tp_fields = ['frame_stability','stability_reliability','optimisation']
            tech_reason = score_data['reasoning'].get('technical_performance', {}).get('detailed', {})
            if isinstance(tech_reason, dict):
                for f in tp_fields:
                    if f in performance_json:
                        key_map = {
                            'frame_stability':'frame_stability',
                            'stability_reliability':'stability_reliability',
                            'optimisation':'optimisation'
                        }
                        tech_reason[key_map[f]] = performance_json[f]
                        changed_tp = True
                if changed_tp:
                    # Recompute technical_performance_score weight blend
                    fs = tech_reason.get('frame_stability',0)
                    sr = tech_reason.get('stability_reliability',0)
                    op = tech_reason.get('optimisation',0)
                    tech_score = fs*(6/15)+sr*(4/15)+op*(5/15)
                    score_data['technical_performance_score'] = round(tech_score,1)
                    score_data['microtransactions_score'] = score_data['technical_performance_score']  # legacy mapping
            # Monetisation override (informational)
            monetisation_details = {
                'types': monetisation_types,
                'notes': override_row['monetisation_notes'],
                'fairness_source': 'override',
                'confidence': 0.9
            }
            try:
                fairness = classify_monetisation(monetisation_details)
                monetisation_details['fairness_label'] = fairness['label']
                monetisation_details['fairness_color'] = fairness['color']
            except Exception:
                pass
            score_data['reasoning']['monetisation'] = {
                'short': 'Monetisation (override applied)',
                'detailed': monetisation_details
            }
            # Recompute overall with possibly updated technical score
            overall = (
                score_data['core_gameplay_score'] * 0.25 +
                score_data['story_immersion_score'] * 0.20 +
                score_data['presentation_score'] * 0.15 +
                score_data['technical_performance_score'] * 0.15 +
                score_data['completeness_score'] * 0.10 +
                score_data['innovation_creativity_score'] * 0.10 +
                score_data['community_longevity_score'] * 0.05
            )
            score_data['overall_score'] = round(overall,1)
            score_data['reasoning']['overall_score']['short'] = f"Weighted Overall: {overall:.1f}/100"
        # Persist scores (upsert semantics if already scanned previously)
        existing = conn.execute("SELECT id FROM scores WHERE game_id = ?", (game_id,)).fetchone()
        columns = [
            'game_id','reviews_score','graphic_score','microtransactions_score','game_mechanics_score',
            'completeness_score','story_quality_score','accessibility_score','overall_score','reasoning',
            'core_gameplay_score','story_immersion_score','presentation_score','technical_performance_score',
            'innovation_creativity_score','community_longevity_score','scoring_version'
        ]
        values = [
            game_id,
            score_data['reviews_score'],
            score_data['graphic_score'],
            score_data['microtransactions_score'],
            score_data['game_mechanics_score'],
            score_data['completeness_score'],
            score_data['story_quality_score'],
            score_data['accessibility_score'],
            score_data['overall_score'],
            json.dumps(score_data['reasoning']),
            score_data.get('core_gameplay_score'),
            score_data.get('story_immersion_score'),
            score_data.get('presentation_score'),
            score_data.get('technical_performance_score'),
            score_data.get('innovation_creativity_score'),
            score_data.get('community_longevity_score'),
            SCORING_VERSION
        ]
        if existing:
            set_clause = ",".join([f"{c} = ?" for c in columns[1:]])
            conn.execute(f"UPDATE scores SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE game_id = ?", values[1:]+[game_id])
        else:
            placeholders = ','.join(['?']*len(columns))
            conn.execute(f"INSERT INTO scores ({','.join(columns)}) VALUES ({placeholders})", values)
        conn.commit()
        # BEFORE persisting, ensure legacy archive stored once
        # BEFORE persisting, ensure legacy archive stored once
        legacy_exists = conn.execute("SELECT 1 FROM scores_archive WHERE game_id = ? AND scoring_version = 1", (game_id,)).fetchone()
        if not legacy_exists and rawg_id:
            legacy_payload = generate_scores_from_api_v1(rawg_details if rawg_id else {})
            try:
                conn.execute("INSERT OR IGNORE INTO scores_archive (game_id, scoring_version, payload_json) VALUES (?, ?, ?)", (game_id, 1, json.dumps(legacy_payload)))
            except Exception as e:
                print(f"Archive insert warning: {e}")
        return {"status": "completed", "scores": score_data}

# Convenience GET alias (idempotent when force=false) for tooling/UIs that issue GET requests
@app.get("/api/games/{game_id}/scan")
async def scan_game_get(game_id: int, force: bool = False, apply_defaults: bool = False):
    return await scan_game(game_id, force, apply_defaults)

@app.get("/api/games/{game_id}/accessibility")
async def get_accessibility_reviews(game_id: int):
    """Return stored accessibility review analysis for a game (from CIPT scraping)."""
    with get_db() as conn:
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        rows = conn.execute("SELECT source_url, raw_score, max_score, features_json, created_at FROM accessibility_reviews WHERE game_id = ?", (game_id,)).fetchall()
        data = []
        for r in rows:
            features = {}
            try:
                features = json.loads(r[3]) if r[3] else {}
            except json.JSONDecodeError:
                pass
            data.append({
                'source_url': r[0],
                'raw_score': r[1],
                'max_score': r[2],
                'features': features,
                'created_at': r[4]
            })
        return {'count': len(data), 'reviews': data}

@app.get("/api/games/{game_id}")
async def get_game(game_id: int):
    """Get detailed game information"""
    with get_db() as conn:
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        scores = conn.execute("SELECT * FROM scores WHERE game_id = ?", (game_id,)).fetchone()

        result = Game(**dict(game))
        if scores:
            score_dict = dict(scores)
            score_dict["reasoning"] = json.loads(score_dict["reasoning"])
            # Auto-refresh monetisation if fairness is missing/Unknown so users never see Unknown
            try:
                mon = (score_dict.get('reasoning') or {}).get('monetisation')
                det = (mon or {}).get('detailed') if isinstance(mon, dict) else None
                label = (det or {}).get('fairness_label') if isinstance(det, dict) else None
                needs_refresh = (not label) or (str(label).lower() == 'unknown')
                if needs_refresh:
                    # Fetch RAWG/Steam data for heuristic
                    rawg_id = dict(game).get('rawg_id')
                    rawg_details = rawg_client.get_game_details(rawg_id) if rawg_id else {}
                    # steam_id may not exist in schema for all rows; guard access
                    try:
                        steam_id = dict(game).get('steam_id')
                    except Exception:
                        steam_id = None
                    steam_data = steam_client.get_app_details(steam_id) if steam_id else {}
                    inferred = infer_monetisation_heuristic(rawg_details, steam_data)
                    if inferred:
                        fair = classify_monetisation(inferred)
                        score_dict.setdefault('reasoning', {})['monetisation'] = {
                            'short': 'Monetisation (inferred heuristic)',
                            'detailed': {
                                'types': inferred.get('types', []),
                                'notes': inferred.get('notes'),
                                'tactics': inferred.get('tactics') or [],
                                'fairness_label': fair.get('label'),
                                'fairness_color': fair.get('color'),
                                'fairness_source': 'heuristic',
                                'confidence': 0.5
                            }
                        }
                    else:
                        # Apply the same never-Unknown defaults as scan
                        is_free = False
                        try:
                            if isinstance(steam_data, dict) and steam_data:
                                is_free = bool(steam_data.get('is_free'))
                        except Exception:
                            is_free = False
                        ftplay_text = ''
                        try:
                            ftplay_text = ((rawg_details.get('description_raw') or rawg_details.get('description') or '') + ' ' + ' '.join([t.get('name','') for t in (rawg_details.get('tags') or []) if isinstance(t, dict)])).lower()
                        except Exception:
                            pass
                        has_f2p_cues = is_free or ('free to play' in ftplay_text) or ('free-to-play' in ftplay_text)
                        if has_f2p_cues:
                            assumed = {'types': ['In-App Purchases'], 'notes': 'Defaulted from Free-to-Play cues; MTX typical, fairness assumed.'}
                            fair = classify_monetisation(assumed)
                            score_dict.setdefault('reasoning', {})['monetisation'] = {
                                'short': 'Monetisation (assumed from F2P)',
                                'detailed': {
                                    'types': assumed['types'],
                                    'notes': assumed['notes'],
                                    'fairness_label': fair.get('label'),
                                    'fairness_color': fair.get('color'),
                                    'fairness_source': 'assumed-f2p',
                                    'confidence': 0.45
                                }
                            }
                        else:
                            assumed = {'types': [], 'notes': 'No monetisation signals detected from public info; treated as none until proven otherwise.'}
                            fair = classify_monetisation(assumed)
                            score_dict.setdefault('reasoning', {})['monetisation'] = {
                                'short': 'Monetisation (no signals found)',
                                'detailed': {
                                    'types': assumed['types'],
                                    'notes': assumed['notes'],
                                    'fairness_label': fair.get('label'),
                                    'fairness_color': fair.get('color'),
                                    'fairness_source': 'assumed-default',
                                    'confidence': 0.35
                                }
                            }
                    # Persist update back to DB so subsequent reads are consistent
                    conn.execute("UPDATE scores SET reasoning = ?, updated_at = CURRENT_TIMESTAMP WHERE game_id = ?", (json.dumps(score_dict['reasoning']), game_id))
                    conn.commit()
            except Exception as _e:
                pass
            result = GameWithScores(game=result, scores=ScoreMetrics(**score_dict))

        return result

@app.get("/api/games")
async def get_all_games():
    """Get all games with their scores"""
    with get_db() as conn:
        games = conn.execute("SELECT * FROM games").fetchall()
        result = []

        for game_row in games:
            game = Game(**dict(game_row))
            scores = conn.execute("SELECT * FROM scores WHERE game_id = ?", (game.id,)).fetchone()

            if scores:
                score_dict = dict(scores)
                score_dict["reasoning"] = json.loads(score_dict["reasoning"])
                game_with_scores = GameWithScores(game=game, scores=ScoreMetrics(**score_dict))
                result.append(game_with_scores)
            else:
                result.append(GameWithScores(game=game, scores=None))

        return result

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/data-sources")
async def get_data_sources():
    """Get information about data sources and accuracy"""
    return {
        "primary_source": "RAWG.io API",
        "data_accuracy": {
            "metacritic_scores": "RAWG aggregates Metacritic data but may have slight variations from official scores due to timing and source differences",
            "user_ratings": "Based on RAWG user community ratings",
            "game_details": "Comprehensive game information from RAWG database"
        },
        "disclaimer": "Scores are estimates based on available data and should be used as general guidance rather than definitive ratings.",
        "last_updated": "Data freshness depends on RAWG's update frequency",
        "recommendation": "For official critic scores, please check Metacritic.com directly"
    }

@app.get("/api/config/status")
async def config_status():
    """Return non-sensitive configuration status booleans to verify keys are loaded.
    Does NOT return actual key values."""
    rawg_present = bool(RAWG_API_KEY and RAWG_API_KEY != 'demo')
    steam_present = bool(STEAM_API_KEY)
    return {
        "rawg_api_key_present": rawg_present,
        "steam_api_key_present": steam_present,
        "steam_api_key_used": False,  # currently Steam key not required for endpoints implemented
        "openai_api_key_present": bool(OPENAI_API_KEY),
        "use_llm_innovation": USE_LLM_INNOVATION,
        "openai_model": OPENAI_MODEL,
        "note": "RAWG key present means it's set and not the placeholder 'demo'. Steam key is not yet used in current calls. LLM for innovation is feature flagged."}

from pydantic import BaseModel
from typing import List, Optional

# Request body for score overrides
class ScoreOverrideRequest(BaseModel):
    monetisation_types: Optional[List[str]] = None
    monetisation_notes: Optional[str] = None
    performance: Optional[dict] = None  # keys: frame_stability, stability_reliability, optimisation

class LifeSupportRequest(BaseModel):
    support_status: str  # expected: unknown | active | eternal | sunset | offline
    last_update_date: Optional[str] = None
    next_update_hint: Optional[str] = None
    notes: Optional[str] = None

class ManualReleaseDateRequest(BaseModel):
    release_date: str  # YYYY-MM-DD
    source: Optional[str] = 'manual'
    notes: Optional[str] = None  # e.g., "added by AI; verified from official announcement"

class ToneRewriteRequest(BaseModel):
    text: str
    tone: Optional[str] = 'casual'  # 'casual' | 'meme' | 'streamer' | 'discord'
    # Optional context so we can avoid wrong genre language and be specific
    game_title: Optional[str] = None
    genres: Optional[List[str]] = None
    subscores: Optional[dict] = None  # e.g., {'core_gameplay': {'mechanics_controls': 78, 'balance': 62, 'replayability': 70}, ...}

class ToneRewriteResponse(BaseModel):
    text: str
    used_model: Optional[str] = None
    provider: str = 'anthropic'

class ToneRewriteBatchItem(BaseModel):
    key: str
    text: str

class ToneRewriteBatchRequest(BaseModel):
    tone: Optional[str] = 'casual'
    items: List[ToneRewriteBatchItem]
    # Optional context
    game_title: Optional[str] = None
    genres: Optional[List[str]] = None
    subscores: Optional[dict] = None

class ToneRewriteBatchResponse(BaseModel):
    items: List[ToneRewriteBatchItem]
    used_model: Optional[str] = None
    provider: str = 'anthropic'

@app.post('/api/games/{game_id}/overrides')
async def set_overrides(game_id: int, body: ScoreOverrideRequest):
    with get_db() as conn:
        game = conn.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail='Game not found')
        monetisation_json = json.dumps(body.monetisation_types) if body.monetisation_types else None
        perf_json = json.dumps(body.performance) if body.performance else None
        existing = conn.execute("SELECT id FROM score_overrides WHERE game_id = ?", (game_id,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE score_overrides SET monetisation_types = ?, monetisation_notes = ?, performance_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE game_id = ?
            """, (monetisation_json, body.monetisation_notes, perf_json, game_id))
        else:
            conn.execute("""
                INSERT INTO score_overrides (game_id, monetisation_types, monetisation_notes, performance_json)
                VALUES (?, ?, ?, ?)
            """, (game_id, monetisation_json, body.monetisation_notes, perf_json))
        conn.commit()
        return {"status": "ok", "game_id": game_id}

@app.get('/api/games/{game_id}/overrides')
async def get_overrides(game_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM score_overrides WHERE game_id = ?", (game_id,)).fetchone()
        if not row:
            return {"game_id": game_id, "overrides": None}
        resp = {
            'monetisation_types': json.loads(row['monetisation_types']) if row['monetisation_types'] else None,
            'monetisation_notes': row['monetisation_notes'],
            'performance': json.loads(row['performance_json']) if row['performance_json'] else None,
            'updated_at': row['updated_at']
        }
        return {"game_id": game_id, "overrides": resp}

@app.post('/api/games/{game_id}/life-support')
async def set_life_support(game_id: int, body: LifeSupportRequest):
    allowed = {"unknown","active","eternal","sunset","offline"}
    status = body.support_status.lower()
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported support_status '{body.support_status}'. Allowed: {', '.join(sorted(allowed))}")
    with get_db() as conn:
        game = conn.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail='Game not found')
        existing = conn.execute("SELECT game_id FROM game_life_support WHERE game_id = ?", (game_id,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE game_life_support
                SET support_status = ?, last_update_date = ?, next_update_hint = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE game_id = ?
            """, (status, body.last_update_date, body.next_update_hint, body.notes, game_id))
        else:
            conn.execute("""
                INSERT INTO game_life_support (game_id, support_status, last_update_date, next_update_hint, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (game_id, status, body.last_update_date, body.next_update_hint, body.notes))
        conn.commit()
    return {"status":"ok","game_id":game_id,"support_status":status,"message":"Life support saved. Re-scan to bake into stored score (otherwise applied dynamically)."}

@app.post('/api/admin/games/{game_id}/release-date')
async def admin_set_release_date(game_id: int, body: ManualReleaseDateRequest):
    # Basic validation YYYY-MM-DD
    try:
        if not isinstance(body.release_date, str) or len(body.release_date) < 4:
            raise ValueError('invalid release_date')
        # derive year if possible
        year = None
        try:
            year = int(body.release_date[:4])
        except Exception:
            year = None
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid release_date format')
    with get_db() as conn:
        game = conn.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail='Game not found')
        conn.execute(
            "UPDATE games SET release_date = ?, release_year = COALESCE(release_year, ?), release_date_source = ?, release_date_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (body.release_date, year, (body.source or 'manual'), body.notes, game_id)
        )
        conn.commit()
    return {"status":"ok","game_id":game_id, "release_date": body.release_date, "release_year": year, "source": body.source or 'manual'}

@app.get('/api/games/{game_id}/life-support')
async def get_life_support(game_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM game_life_support WHERE game_id = ?", (game_id,)).fetchone()
        if not row:
            return {"game_id": game_id, "life_support": None}
        return {"game_id": game_id, "life_support": {
            'support_status': row['support_status'],
            'last_update_date': row['last_update_date'],
            'next_update_hint': row['next_update_hint'],
            'notes': row['notes'],
            'updated_at': row['updated_at']
        }}

# =============================== Text Rewrite (Claude 3.5 Sonnet) ===============================

# Tone description constants (keep brutal wording fixed)
BRUTAL_TONE_STYLE = 'brutally honest, candid, no fluff'

def _to_uk_english(s: str) -> str:
    """Convert common US spellings to UK spellings (lightweight mapping)."""
    try:
        import re as _re
        # Map of US -> UK spellings (lowercase keys)
        mapping = {
            'color': 'colour', 'colors': 'colours', 'colored': 'coloured', 'coloring': 'colouring',
            'optimize': 'optimise', 'optimized': 'optimised', 'optimizing': 'optimising', 'optimization': 'optimisation',
            'behavior': 'behaviour', 'behavioral': 'behavioural',
            'center': 'centre', 'centered': 'centred', 'centering': 'centring',
            'favorite': 'favourite', 'favorites': 'favourites',
            'armor': 'armour',
            'analyze': 'analyse', 'analyzed': 'analysed', 'analyzing': 'analysing', 'analyzer': 'analyser',
            'defense': 'defence'
        }
        def sub_word(text: str, src: str, tgt: str) -> str:
            return _re.sub(rf"\b{_re.escape(src)}\b", tgt, text, flags=_re.IGNORECASE)
        out = s
        for us, uk in mapping.items():
            out = sub_word(out, us, uk)
        return out
    except Exception:
        return s

def _fallback_spicy_rewrite(text: str, tone: str = 'casual', topic_hint: str | None = None, subscores: dict | None = None, genres: list[str] | None = None) -> str:
    """Generate a playful, gamer-style rewrite locally when Claude isn't available.
    Keeps it short (1–2 sentences), uses light slang, and tailors to the detected metric.
    """
    try:
        t = (tone or 'casual').lower()
        raw = (text or '').strip()
        lower = raw.lower()

        # Seed randomness for variety but stable per input
        try:
            seed_src = f"{tone}::{topic_hint or ''}::{raw[:120]}"
            rnd = random.Random(hash(seed_src))
        except Exception:
            rnd = random

        # Extract a numeric score out of 100 if present
        score = None
        try:
            import re as _re
            m = _re.search(r"(\d{1,3}(?:\.\d+)?)\s*/\s*100", raw)
            if m:
                score = float(m.group(1))
        except Exception:
            score = None

        # Choose adjectives by score band (creative but non-promotional)
        if score is not None:
            if score >= 90:
                adj = rnd.choice(["polished", "well‑tuned", "sharp", "dialled‑in", "cohesive", "confident"])
            elif score >= 80:
                adj = rnd.choice(["clean", "crisp", "buttery", "snappy", "tight", "punchy"])
            elif score >= 70:
                adj = rnd.choice(["holds its own", "steady", "puts in work", "tight enough", "finds a groove"]) 
            elif score >= 60:
                adj = rnd.choice(["workmanlike", "kinda mid but playable", "serviceable", "rough‑polished", "could use a tune"]) 
            else:
                adj = rnd.choice(["rough", "struggling", "needs training arc", "mid at best", "on life support"]) 
        else:
            adj = rnd.choice(["clean", "silky", "snappy", "low‑key", "zesty"]) 

        # Detect metric/topic hints
        topic = None
        hint = (topic_hint or '').lower()
        candidates = [lower, hint]
        for pool in candidates:
            for key, tag in [
                ("core_gameplay", "Core Gameplay"),
                ("gameplay", "Gameplay"),
                ("mechanic", "Mechanics"),
                ("technical_performance", "Performance"),
                ("performance", "Performance"),
                ("technical", "Performance"),
                ("story_immersion", "Story"),
                ("story", "Story"),
                ("immersion", "Immersion"),
                ("presentation", "Presentation"),
                ("graphic", "Graphics"),
                ("innovation_creativity", "Innovation"),
                ("innovation", "Innovation"),
                ("community_longevity", "Community"),
                ("community", "Community"),
                ("monetisation", "Monetisation"),
                ("monetization", "Monetisation"),
            ]:
                if key in pool:
                    topic = tag
                    break
            if topic:
                break

        # Domain hints (e.g., sports) to avoid combat wording on non-combat titles
        sports_tokens = [
            'sports', 'football', 'soccer', 'fc', 'fifa', 'madden', 'nhl', 'nba', 'eas fc', 'ea sports fc'
        ]
        genres_lower = [g.lower() for g in (genres or []) if isinstance(g, str)]
        is_sports = any(tok in lower for tok in sports_tokens) or any(tok in hint for tok in sports_tokens) or any('sport' in g for g in genres_lower)
        # Broader genre tokens for light context
        genre_tokens = set()
        for g in genres_lower:
            for t in re.split(r"[^a-z0-9]+", g):
                if t:
                    genre_tokens.add(t)
        # Helper: genre-aware context phrase per topic (single short sentence fragment)
        def context_vibe(topic_key: str) -> str | None:
            if is_sports:
                if topic_key in ('gameplay','mechanics'):
                    return "Passing, finishing, and defence shape the match."
                if topic_key == 'presentation':
                    return "Broadcast package and stadium feel do the heavy lifting."
                if topic_key in ('story','immersion'):
                    return "Career beats and broadcast cadence set the tone."
                if topic_key == 'performance':
                    return "Large crowds, replays, and camera cuts test stability."
            if 'shooter' in genre_tokens or 'fps' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Gunfeel and recoil tell the story."
                if topic_key == 'presentation':
                    return "Impact readability and effects matter more than raw pixels."
                if topic_key == 'performance':
                    return "Busy fights and particles stress frames."
            if 'rpg' in genre_tokens or 'role' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Builds, skills, and quest flow carry the experience."
                if topic_key in ('story','immersion'):
                    return "Companions, questlines, and world lore do the lifting."
            if 'platformer' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Jumps, timing, and precision are the read."
            if 'racing' in genre_tokens or 'racer' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Handling, braking, and cornering are the feel."
                if topic_key == 'presentation':
                    return "Sense of speed and camera work sell the laps."
            if 'fighting' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Hit confirm windows, cancels, and matchup knowledge matter."
            if 'strategy' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Macro calls and micro execution define the loop."
            if 'simulation' in genre_tokens or 'sim' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Systems and feedback loops are the focus."
            if 'horror' in genre_tokens:
                if topic_key in ('story','immersion'):
                    return "Tension, audio cues, and resource pressure set the mood."
                if topic_key == 'performance':
                    return "Dark scenes and post-processing can tax frames."
            if 'roguelike' in genre_tokens or 'roguelite' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Runs, meta progression, and build variety keep it moving."
            if 'soulslike' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "I-frames, stamina, and punish windows are the skill check."
            if 'metroidvania' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Movement, upgrades, and route-finding do the work."
            if 'puzzle' in genre_tokens:
                if topic_key in ('gameplay','mechanics'):
                    return "Clarity of rules and the 'aha' moments drive the loop."
            return None

        # Tone flourishes
        def flavor_casual():
            openers = [
                "Okay so",
                "Honestly",
                "Real talk",
                "Low-key",
                "Not gonna lie",
                "Hear me out",
            ]
            closers = [
                "no spin.",
                "as it is.",
                "that’s the read.",
                "nothing more, nothing less.",
                "just observations.",
                "no pitch.",
            ]
            return rnd.choice(openers), rnd.choice(closers)

        def flavor_meme():
            openers = [
                "No cap,",
                "POV:",
                "Certified hood classic:",
                "This goes dummy:",
                "Skill issue? Not here:",
                "Breaking:",
            ]
            closers = [
                "that’s the read.",
                "no spin.",
                "just how it plays.",
                "call it neutral.",
                "not a sales pitch.",
                "observational vibes only.",
            ]
            return rnd.choice(openers), rnd.choice(closers)

        def flavor_streamer():
            openers = [
                "Chat, listen—",
                "Yo stream,",
                "Okay team,",
                "Clip this—",
                "Mods,",
                "Production,",
            ]
            closers = [
                "that's the content.",
                "and we're cooking.",
                "mic drop.",
                "we gaming.",
                "print it.",
                "that's the tweet.",
            ]
            return rnd.choice(openers), rnd.choice(closers)

        def flavor_discord():
            openers = [
                "Heads up:",
                "ngl,",
                "hot take:",
                "FYI",
                "pls read:",
                "tldr:",
            ]
            closers = [
                "thoughts? 🤔",
                "pls discuss.",
                "opinions welcome.",
                "that’s all.",
                "not prescriptive.",
                "no pitch.",
                "observations only.",
            ]
            return rnd.choice(openers), rnd.choice(closers)

        def flavor_brutal():
            # No fluff, straight to point. Keep it UK English and inclusive, but candid.
            openers = [
                "Blunt take:",
                "Straight up:",
                "No fluff:",
                "Honestly:",
                "Cutting to it:",
            ]
            closers = [
                "that’s the reality.",
                "no sugar-coat.",
                "call it as seen.",
                "facts over vibes.",
                "that’s the read.",
            ]
            return rnd.choice(openers), rnd.choice(closers)

        if t == 'meme':
            opener, closer = flavor_meme()
        elif t == 'streamer':
            opener, closer = flavor_streamer()
        elif t == 'discord':
            opener, closer = flavor_discord()
        elif t == 'brutal':
            opener, closer = flavor_brutal()
        else:
            opener, closer = flavor_casual()

        # Build two compact sentences using topic-aware templates
        left = (topic or "Gameplay").lower()
        perf_hint = ("performance" in left) or ("technical" in left) or ("fps" in lower) or ("stutter" in lower)

        def pick(options):
            return rnd.choice(options)

        # Topic-specific lines (default creative pools; will be overridden by subscores if provided)
        topic_lines = {
            'gameplay': (
                [
                    (
                        f"{opener} on-pitch play is {adj}, {closer}" if is_sports else
                        f"{opener} the gameplay is {adj}, {closer}"
                    ),
                    (
                        f"passing feels {pick(['crisp','snappy','buttery'])} and movement reads your intent." if is_sports else
                        f"inputs feel {pick(['tight','snappy','buttery'])} and timing rewards you."
                    ),
                ],
                [
                    ("build-up play finds space if you work for it." if is_sports else "the loop sinks its hooks fast."),
                    ("finishing feels earned when you line it up." if is_sports else "reads and reactions actually matter."),
                    ("defence positioning matters—patterns open then close." if is_sports else "skill checks feel fair."),
                    ("set-pieces are a little mini-game of their own." if is_sports else "reads and reactions actually matter."),
                ]
            ),
            'mechanics': (
                [
                    f"{opener} the mechanics are {adj}, {closer}",
                    (
                        "systems balance pace, positioning, and stamina nicely." if is_sports else
                        "systems click together like Lego for gremlins (that's us)."
                    ),
                ],
                [
                    ("through balls vs safe passes is a live decision every play." if is_sports else "risk-reward is tuned just right."),
                    ("first touch matters; bad control will punish you." if is_sports else "inputs translate straight to dopamine."),
                    ("formations and tactics actually show up on the pitch." if is_sports else "skill ceiling peeks through quick."),
                ]
            ),
            'performance': (
                [
                    f"{opener} the performance needs a buff, {closer}",
                    f"thermals are cooking and frames sometimes faceplant.",
                ],
                [
                    "shader cache is playing Tetris on first launch.",
                    "fans spin up like a jet mid-boss.",
                    "frametime graph looks like a heartbeat monitor.",
                    "a hotfix could change the story overnight.",
                ]
            ),
            'story': (
                [
                    f"{opener} the story delivery is {adj}, {closer}",
                    "dialogue lands and the stakes escalate cleanly.",
                ],
                [
                    "lore actually cooks instead of dumping walls of text.",
                    "setpieces carry weight without dragging.",
                    "character arcs get room to breathe.",
                    "quests respect your time (mostly).",
                ]
            ),
            'immersion': (
                [
                    f"{opener} immersion is {adj}, {closer}",
                    "it nails that 'one more run' hypnosis.",
                ],
                [
                    ("crowd noise and broadcast chatter sell the stadium vibe." if is_sports else "sound cues and haptics sell the fantasy."),
                    "worldbuilding feels lived-in, not copy-paste.",
                    "pace rarely hiccups once it clicks.",
                    "UI stays out of the way when it should.",
                ]
            ),
            'presentation': (
                [
                    (
                        f"{opener} broadcast package looks {adj}, {closer}" if is_sports else f"{opener} graphics are {adj}, {closer}"
                    ),
                    (
                        "stadium atmosphere pops on key moments." if is_sports else "art direction drips and lighting sings."
                    ),
                ],
                [
                    ("although commentary cadence still misses a beat." if is_sports else "although the soundtrack slaps in key moments."),
                    "but the soundtrack absolutely carries key beats.",
                    "meanwhile the audio mix does numbers when it matters.",
                    "VFX do the heavy lifting without blinding you.",
                    "UI is readable without screaming.",
                    "camera work rarely fights the action.",
                ]
            ),
            'graphics': (
                [
                    f"{opener} the visuals are {adj}, {closer}",
                    "materials and particles show up to flex.",
                ],
                [
                    "stylistic choices age better than raw pixels.",
                    "color grading sets a vibe instantly.",
                    "animation sells weight and impact.",
                    "post-processing is tasteful (mostly).",
                ]
            ),
            'innovation': (
                [
                    f"{opener} the ideas go {adj}, {closer}",
                    "systems interlock in clever ways.",
                ],
                [
                    "genre remix feels fresh without trying too hard.",
                    "you can smell the 'just one more experiment' energy.",
                    "it finds new lines to color outside.",
                    "a couple swings miss, but the hits land loud.",
                ]
            ),
            'community': (
                [
                    f"{opener} the community scene is {adj}, {closer}",
                    "lobbies feel alive and the meta keeps moving.",
                ],
                [
                    "queues are quick and salt stays mostly in the shaker.",
                    "modders already cooking side dishes.",
                    "events give reasons to log back in.",
                    "dev posts don't ghost for months.",
                ]
            ),
        }

        # Map topic tag to template key
        topic_key = 'gameplay'
        if perf_hint:
            topic_key = 'performance'
        elif topic:
            map_to = {
                'Core Gameplay': 'gameplay',
                'Gameplay': 'gameplay',
                'Mechanics': 'mechanics',
                'Performance': 'performance',
                'Story': 'story',
                'Immersion': 'immersion',
                'Presentation': 'presentation',
                'Graphics': 'graphics',
                'Innovation': 'innovation',
                'Community': 'community',
                'Monetisation': 'monetisation',
            }
            topic_key = map_to.get(topic, 'gameplay')

        # Special handling for monetisation to talk menus and fairness explicitly
        if topic_key == 'monetisation':
            # crude signal detection from provided text
            has_p2w = any(k in lower for k in ["p2w: yes", "pay to win", "pay-to-win", "gameplay advantage", "stat boost", "xp boost", "xp advantage", "power boost"]) or ("p2w" in lower and "no" not in lower)
            cosmetic_only = any(k in lower for k in ["cosmetic", "p2w: no", "no p2w", "no pay to win", "no microtransaction", "no mtx", "perfect"]) and not has_p2w
            mixed = ("p2w: mixed" in lower) or (any(k in lower for k in ["battle pass", "item shop", "loot box", "gacha"])) and not has_p2w and not cosmetic_only

            if has_p2w:
                s1 = pick([
                    f"{opener} pay-to-win elements are present—calling it plainly, {closer}",
                    f"{opener} monetisation crosses into pay-to-win, {closer}",
                ])
                s2 = pick([
                    "spend buys a competitive edge; skill isn’t the only factor.",
                    "progress and power lean on your wallet more than skill.",
                    "credit card pressure shows up in competitive modes.",
                ])
            elif cosmetic_only:
                s1 = pick([
                    f"{opener} it's mostly cosmetic bits—fair play, {closer}",
                    f"{opener} monetisation stays in its lane, {closer}",
                ])
                # Default to this exact line for cosmetic-only/no-P2W cases
                s2 = "no gameplay edge—just drip if you’re into it."
            elif mixed:
                s1 = pick([
                    f"{opener} monetisation gives you a nudge, {closer}",
                    f"{opener} the shop is present but not overbearing, {closer}",
                ])
                s2 = pick([
                    "menus prod you now and then; fairness reads decent.",
                    "upsell appears but stays optional.",
                    "not egregious—pop-ups are present.",
                ])
            else:
                s1 = pick([
                    f"{opener} monetisation exists, {closer}",
                    f"{opener} there's a shop, {closer}",
                ])
                s2 = pick([
                    "hard to judge fairness from here—check before you buy.",
                    "can't rate fairness without more info.",
                    "unclear on advantage—treat as 'unknown' for now.",
                ])
        else:
            # If subscores provided, build a metric-aligned summary instead of generic flavour (no numbers; qualitative only)
            built = False
            def band(v):
                try:
                    f = float(v)
                except Exception:
                    return None
                if f >= 80: return 'high'
                if f >= 60: return 'mid'
                return 'low'
            def choose(desc_map, v):
                b = band(v)
                if b is None: return None
                return desc_map.get(b)
            if isinstance(subscores, dict):
                # Gameplay/mechanics
                if topic_key in ('gameplay','mechanics'):
                    cg = subscores.get('core_gameplay') or {}
                    mc_d = choose({'high': 'tight and responsive','mid': 'serviceable with a few quirks','low': 'a bit slippy and inconsistent'}, cg.get('mechanics_controls'))
                    bal_d = choose({'high': 'feels fair','mid': 'mostly fair with swingy moments','low': 'needs tuning'}, cg.get('balance'))
                    rep_d = choose({'high': 'keeps you coming back','mid': 'has a decent loop','low': 'runs thin after a while'}, cg.get('replayability'))
                    frags = []
                    if mc_d: frags.append(f"controls feel {mc_d}")
                    if bal_d: frags.append(f"balance {bal_d}")
                    if rep_d: frags.append(f"replayability {rep_d}")
                    if frags:
                        s1 = f"{opener} the core loop clicks: " + ", ".join(frags) + f". {closer}"
                        s2 = context_vibe(topic_key) or "Net: strengths and gaps are clear without fluff."
                        built = True
                # Performance
                if not built and topic_key == 'performance':
                    tp = subscores.get('technical_performance') or {}
                    fs_d = choose({'high': 'frames hold steady','mid': 'mostly smooth with the odd dip','low': 'choppy in spots'}, tp.get('frame_stability'))
                    sr_d = choose({'high': 'stable build with few hiccups','mid': 'some quirks here and there','low': 'crashes or bugs show up'}, tp.get('stability_reliability'))
                    op_d = choose({'high': 'well-optimised across the board','mid': 'fine on modern kit','low': 'needs optimisation work'}, tp.get('optimisation'))
                    frags = [p for p in [fs_d, sr_d, op_d] if p]
                    if frags:
                        s1 = f"{opener} performance vibe: " + "; ".join(frags) + f". {closer}"
                        s2 = context_vibe(topic_key) or "Stutter can show; settings tweaks may help."
                        built = True
                # Presentation
                if not built and topic_key == 'presentation':
                    pr = subscores.get('presentation') or {}
                    ga_d = choose({'high': 'art direction pops','mid': 'clean look with some highlights','low': 'flat in places'}, pr.get('graphics_art'))
                    sm_d = choose({'high': 'soundtrack hums and the mix lands','mid': 'good mix overall','low': 'forgettable audio mix'}, pr.get('sound_music'))
                    im_d = choose({'high': 'easy to lose yourself','mid': 'absorbing enough','low': 'struggles to pull you in'}, pr.get('immersion_factor'))
                    frags = [p for p in [ga_d, sm_d, im_d] if p]
                    if frags:
                        s1 = f"{opener} presentation lands: " + "; ".join(frags) + f". {closer}"
                        s2 = context_vibe(topic_key) or "Audio/visuals pull their weight where it counts."
                        built = True
                # Story & immersion
                if not built and topic_key in ('story','immersion'):
                    si = subscores.get('story_immersion') or {}
                    nv_d = choose({'high': 'story lands and sticks the beats','mid': 'story holds together','low': 'story runs thin'}, si.get('narrative_quality'))
                    wb_d = choose({'high': 'the world feels lived-in','mid': 'the world has shape and texture','low': 'the world feels sparse'}, si.get('worldbuilding'))
                    cd_d = choose({'high': 'characters get meaningful arcs','mid': 'decent character moments','low': 'thin character work'}, si.get('character_development'))
                    frags = [p for p in [nv_d, wb_d, cd_d] if p]
                    if frags:
                        s1 = f"{opener} story & immersion: " + "; ".join(frags) + f". {closer}"
                        s2 = context_vibe(topic_key) or "Expect delivery in line with that mix."
                        built = True
            if not built:
                first_lines, second_pool = topic_lines.get(topic_key, topic_lines['gameplay'])
                s1 = pick(first_lines)
                # Swap in a genre-aware context line if available
                s2 = context_vibe(topic_key) or pick(second_pool)

        out = f"{s1} {s2}"
        # Trim extra spaces just in case
        out = ' '.join(out.split())
        return _to_uk_english(out)
    except Exception:
        # Ultra-safe fallback if anything goes wrong here
        return f"{text}"

@app.post('/api/text/rewrite', response_model=ToneRewriteResponse)
async def rewrite_text_claude(body: ToneRewriteRequest):
    """Rewrite input text in a gamer-friendly tone via Anthropic Claude 3.5 Sonnet.

    Requires ANTHROPIC_API_KEY in environment. If absent, falls back to a simple local rephrase.
    """
    toneStyles = {
        'casual': 'casual gamer vibes',
        'meme': 'high meme energy',
        'streamer': 'streamer commentary style',
        'discord': 'Discord chat energy with emojis',
        'brutal': BRUTAL_TONE_STYLE
    }
    tone = (body.tone or 'casual').lower()
    tone_desc = toneStyles.get(tone, toneStyles['casual'])
    if not body.text or not isinstance(body.text, str):
        raise HTTPException(status_code=400, detail='text is required')

    # Fallback when no Anthropic key is configured
    if not ANTHROPIC_API_KEY:
        # Pass a light topic hint based on common metric keys in the text
        hint = None
        low = body.text.lower()
        for k in ["core_gameplay","gameplay","mechanics","performance","technical","story","immersion","presentation","graphics","innovation","community"]:
            if k in low:
                hint = k
                break
        # Enrich hint with sports cue if title/genres indicate sports
        try:
            sports_cues = ['sports','football','soccer','fc','fifa','madden','nhl','nba']
            gt = (body.game_title or '').lower()
            gs = ' '.join((body.genres or [])).lower()
            if any(x in gt for x in sports_cues) or any(x in gs for x in sports_cues):
                hint = (hint + ' sports') if hint else 'sports'
        except Exception:
            pass
        return ToneRewriteResponse(text=_fallback_spicy_rewrite(body.text, tone, hint, subscores=body.subscores, genres=body.genres), used_model=None, provider='fallback')

    try:
        api_url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        system_prompt = (
            "Rewrite text to be fun, playful, and gamer-friendly in 1-2 punchy sentences. "
            "Be specific and evocative; avoid generic words like 'nice', 'good', 'great', 'solid'. "
            "Use UK English spelling. Use light gaming slang, avoid profanity, stay inclusive. "
            "For monetisation topics: be candid and factual—if pay-to-win (P2W) or spend-for-advantage exists, say it plainly; "
            "if fairness is unknown, state it's unknown; do not downplay upsell/menu pressure. "
            "If the topic is monetisation, do not talk about gameplay loops, mechanics, balance, or replayability; focus strictly on shop/MTX, fairness, and menu pressure. "
            "If monetisation is cosmetic-only/no P2W, a good phrasing is: 'no gameplay edge—just drip if you’re into it.' "
            "If the context is a sports title (e.g., EA Sports FC/FIFA/Madden/NHL/NBA), avoid combat/boss language; focus on on-pitch play, passing, finishing, defence, stamina. "
            "If subscores are provided, briefly align the phrasing with those metrics (e.g., mechanics & controls, balance, replayability) using qualitative language only (no numbers), and avoid irrelevant terms like 'pacing' where it doesn't fit. "
            "No prefaces like 'Quick take'. "
            f"Style: {tone_desc}."
        )
        payload = {
            'model': ANTHROPIC_MODEL,
            'max_tokens': 400,
            'system': system_prompt,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': f"Rewrite the following: \n\n{body.text}\n\nContext (optional): title={body.game_title or ''}; genres={(body.genres or [])}; subscores={(json.dumps(body.subscores) if body.subscores else '{}')}"}
                    ]
                }
            ]
        }
        resp = requests.post(api_url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        out = ''
        try:
            parts = data.get('content') or []
            for p in parts:
                if isinstance(p, dict) and p.get('type') == 'text' and isinstance(p.get('text'), str):
                    out += p['text']
        except Exception:
            out = ''
        if not out:
            out = data.get('content', '') if isinstance(data.get('content'), str) else ''
        if not out:
            out = 'Could not parse Claude response; please try again.'
        # Enforce monetisation on-topic: if the input text looks like monetisation, override with strict fallback
        low_in = (body.text or '').lower()
        if ('monetisation' in low_in) or ('monetization' in low_in) or ('p2w' in low_in):
            out = _fallback_spicy_rewrite(body.text, tone, 'monetisation', subscores=None, genres=body.genres)
        return ToneRewriteResponse(text=out.strip(), used_model=ANTHROPIC_MODEL, provider='anthropic')
    except Exception as e:
        print(f"Anthropic rewrite error: {e}")
    return ToneRewriteResponse(text=_fallback_spicy_rewrite(body.text, tone, subscores=body.subscores, genres=body.genres), used_model=None, provider='fallback')


@app.post('/api/text/rewrite-batch', response_model=ToneRewriteBatchResponse)
async def rewrite_text_batch(body: ToneRewriteBatchRequest):
    toneStyles = {
        'casual': 'casual gamer vibes',
        'meme': 'high meme energy',
        'streamer': 'streamer commentary style',
        'discord': 'Discord chat energy with emojis',
        'brutal': BRUTAL_TONE_STYLE
    }
    if not body.items or not isinstance(body.items, list):
        raise HTTPException(status_code=400, detail='items is required')
    tone = (body.tone or 'casual').lower()
    tone_desc = toneStyles.get(tone, toneStyles['casual'])

    # Fallback: generate spicy rewrites per item
    if not ANTHROPIC_API_KEY:
        out_items = []
        for i in body.items:
            hint = i.key.lower() if isinstance(i.key, str) else None
            # If this is a monetisation field, force topic to 'monetisation' and ignore subscores
            is_monetisation = isinstance(i.key, str) and 'monetisation' in i.key.lower()
            # Add sports hint if context provided
            try:
                sports_cues = ['sports','football','soccer','fc','fifa','madden','nhl','nba']
                gt = (body.game_title or '').lower()
                gs = ' '.join((body.genres or [])).lower()
                if any(x in gt for x in sports_cues) or any(x in gs for x in sports_cues):
                    hint = f"{hint or ''} sports".strip()
            except Exception:
                pass
            out_items.append(
                ToneRewriteBatchItem(
                    key=i.key,
                    text=_fallback_spicy_rewrite(
                        i.text,
                        tone,
                        ('monetisation' if is_monetisation else hint),
                        subscores=(None if is_monetisation else body.subscores),
                        genres=body.genres
                    )
                )
            )
        return ToneRewriteBatchResponse(items=out_items, provider='fallback', used_model=None)

    # Anthropic call: join items into a single prompt to reduce requests
    try:
        api_url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        system_prompt = (
            "Rewrite each value to be fun, playful, and gamer-friendly in 1-2 punchy sentences. "
            "Be specific and evocative (e.g., talk mechanics vs performance), avoid generic fillers (nice/good/great/solid). "
            "Use UK English spelling. Use light gaming slang, inclusive tone, no profanity. "
            "For monetisation keys/fields: be candid—if P2W or spend-for-advantage exists, say it plainly; if unknown, say 'unknown'. "
            "For keys named 'monetisation.*', do not talk about gameplay loops, mechanics, balance, or replayability; focus strictly on shop/MTX, fairness, and menu pressure. "
            "If monetisation is cosmetic-only/no P2W, prefer: 'no gameplay edge—just drip if you’re into it.' "
            "Avoid combat/boss terminology for sports titles (EA Sports FC/FIFA/Madden/NHL/NBA); focus on on-pitch play and broadcast vibe. "
            "If subscores are provided, align phrasing with those values using qualitative descriptions (no numeric mentions), and avoid irrelevant terms like 'pacing' where it doesn't fit. "
            f"Style: {tone_desc}. Return strict JSON mapping keys to rewrites."
        )
        payload_text = {
            k: v for k, v in ((i.key, i.text) for i in body.items if isinstance(i.key, str) and isinstance(i.text, str))
        }
        ctx_title = body.game_title or ''
        ctx_genres = ', '.join(body.genres or [])
        user_text = (
            "Rewrite each field in this JSON and return JSON with the same keys only, values replaced with rewrites.\n\n" +
            json.dumps(payload_text) +
            f"\n\nContext (optional): title={ctx_title}; genres=[{ctx_genres}]; subscores={(json.dumps(body.subscores) if body.subscores else '{}')}"
        )
        payload = {
            'model': ANTHROPIC_MODEL,
            'max_tokens': 1200,
            'system': system_prompt,
            'messages': [
                { 'role': 'user', 'content': [ { 'type': 'text', 'text': user_text } ] }
            ]
        }
        resp = requests.post(api_url, headers=headers, json=payload, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        # Attempt to parse JSON from Claude response
        content_text = ''
        try:
            parts = data.get('content') or []
            for p in parts:
                if isinstance(p, dict) and p.get('type') == 'text' and isinstance(p.get('text'), str):
                    content_text += p['text']
        except Exception:
            content_text = ''
        mapping = {}
        try:
            mapping = json.loads(content_text)
        except Exception:
            # Fallback to returning inputs unchanged
            mapping = payload_text
        # Enforce monetisation keys to use strict fallback (LLM output can drift into gameplay)
        enforced_items = {}
        for k in payload_text.keys():
            v = str(mapping.get(k, payload_text.get(k, '')))
            if isinstance(k, str) and 'monetisation' in k.lower():
                v = _fallback_spicy_rewrite(payload_text.get(k, v), tone, 'monetisation', subscores=None, genres=body.genres)
            enforced_items[k] = v
        out_items = [ToneRewriteBatchItem(key=k, text=enforced_items[k]) for k in payload_text.keys()]
        return ToneRewriteBatchResponse(items=out_items, used_model=ANTHROPIC_MODEL, provider='anthropic')
    except Exception as e:
        print(f"Anthropic batch rewrite error: {e}")
        out_items = []
        for i in body.items:
            hint = i.key.lower() if isinstance(i.key, str) else None
            out_items.append(ToneRewriteBatchItem(key=i.key, text=_fallback_spicy_rewrite(i.text, tone, hint, subscores=body.subscores, genres=body.genres)))
        return ToneRewriteBatchResponse(items=out_items, provider='fallback', used_model=None)

# ---------------- Admin: reset legacy and rescan ----------------

@app.post('/api/admin/reset-and-rescan')
async def admin_reset_and_rescan(remove_legacy_archive: bool = True, limit: Optional[int] = None, only_game_id: Optional[int] = None):
    """Delete existing scores and optional legacy v1 archives, then rescan all games.
    - remove_legacy_archive: when true, deletes scores_archive rows for scoring_version=1
    - limit: optionally cap the number of games to rescan (ordered by id)
    Returns a summary of rescan results and any errors.
    """
    # Collect game ids first
    with get_db() as conn:
        if only_game_id is not None:
            rows = conn.execute("SELECT id FROM games WHERE id = ?", (only_game_id,)).fetchall()
        else:
            rows = conn.execute("SELECT id FROM games ORDER BY id ASC").fetchall()
        game_ids = [r['id'] for r in rows]
        if limit is not None:
            try:
                lim = int(limit)
                if lim >= 0:
                    game_ids = game_ids[:lim]
            except Exception:
                pass
        # Wipe existing scores for selected games
        if game_ids:
            placeholders = ','.join(['?'] * len(game_ids))
            conn.execute(f"DELETE FROM scores WHERE game_id IN ({placeholders})", game_ids)
        # Remove legacy v1 archive if requested
        if remove_legacy_archive:
            conn.execute("DELETE FROM scores_archive WHERE scoring_version = 1")
        conn.commit()

    # Rescan sequentially using the same logic as /scan
    results = []
    errors = []
    for gid in game_ids:
        try:
            resp = await scan_game(gid)
            results.append({"game_id": gid, "status": resp.get("status", "unknown")})
        except Exception as e:
            errors.append({"game_id": gid, "error": str(e)})
    return {"rescanned": len(results), "errors": errors}

# ---------------- Helper: auto-apply monetisation defaults ----------------

def apply_monetisation_overrides_if_match(conn: sqlite3.Connection, game_id: int, title: str) -> bool:
    """Check if game title matches known patterns and apply monetisation overrides if so.
    Returns True if override was applied, False otherwise.
    """
    patterns = [
        {
            'match': lambda t: 'fortnite' in t and 'battle' in t,
            'types': ["Free-to-Play","Battle Pass","Cosmetic MTX","Item Shop","Loot Boxes: No","P2W: No"],
            'notes': "Cosmetic-only purchases; rotating shop; no gameplay advantages."
        },
        {
            'match': lambda t: 'ea sports fc' in t and any(x in t for x in [' 24',' 25',' 26']),
            'types': ["Full Price","Ultimate Team (FUT-like)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "Ultimate Team card packs and seasonal pass; spend influences online modes (mixed)."
        },
        # EA Sports titles (FIFA, Madden, NHL, NBA Live, etc.)
        {
            'match': lambda t: ('fifa' in t) and any(x in t for x in ['20','21','22','23','24','25']),
            'types': ["Full Price","Ultimate Team (FUT)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "FIFA Ultimate Team with card packs; spend affects competitive online modes."
        },
        {
            'match': lambda t: ('madden nfl' in t or 'madden' in t) and any(x in t for x in ['20','21','22','23','24','25']),
            'types': ["Full Price","Ultimate Team (MUT)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "Madden Ultimate Team with card packs; spend affects competitive online modes."
        },
        {
            'match': lambda t: ('nhl' in t) and any(x in t for x in ['20','21','22','23','24','25']),
            'types': ["Full Price","Ultimate Team (HUT)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "Hockey Ultimate Team with card packs; spend affects competitive online modes."
        },
        {
            'match': lambda t: ('nba live' in t) and any(x in t for x in ['19','20','21','22','23']),
            'types': ["Full Price","Ultimate Team","Packs/Player Cards","In-Game Currency","P2W: Mixed"],
            'notes': "NBA Live Ultimate Team with card packs; spend affects competitive modes."
        },
        {
            'match': lambda t: 'legend of zelda' in t and 'breath of the wild' in t,
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Single purchase; no in-game store; no P2W."
        },
        {
            'match': lambda t: 'legend of zelda' in t and ('tears of the kingdom' in t or 'totk' in t),
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Single purchase; no in-game store; no P2W."
        },
        {
            'match': lambda t: 'witcher 3' in t,
            'types': ["Base Game","Paid Expansions","No Loot Boxes","No Battle Pass","P2W: No"],
            'notes': "Paid expansions (Hearts of Stone, Blood and Wine); no microtransactions; no P2W."
        },
        {
            'match': lambda t: 'elden ring' in t and 'nightreign' not in t,
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Base game; no in-game purchases; no P2W."
        },
        {
            'match': lambda t: 'red dead redemption 2' in t,
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Story mode unaffected by online MTX; base game has no P2W."
        },
        {
            'match': lambda t: 'god of war (2018)' in t or (t.strip() == 'god of war' and 'ragnar' not in t),
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Single-player; no in-game purchases; no pay-to-win."
        },
        {
            'match': lambda t: 'the last of us part i' in t or 'the last of us part ii' in t or (t.strip() == 'the last of us'),
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Single-player campaign; no in-game purchases; no pay-to-win."
        },
        {
            'match': lambda t: t.strip() in ('skate 2','skate 3'),
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","P2W: No"],
            'notes': "Legacy titles; no in-game purchases; no P2W."
        },
        {
            'match': lambda t: (
                ("marvel" in t and ("spider-man" in t or "spider man" in t or "spiderman" in t)) or
                ("miles morales" in t)
            ),
            'types': ["Base Game","Paid Expansions","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Single-player; optional paid DLC (The City That Never Sleeps / Remastered/Miles include content); no in-game purchases; no pay-to-win."
        },
        {
            'match': lambda t: 'marvel snap' in t,
            'types': ["Free-to-Play","Season Pass","Card Upgrades","In-Game Currency","Random Series Drops","P2W: Mixed"],
            'notes': "F2P CCG with season pass and progression; spend can accelerate collection and competitive advantage (mixed)."
        },
        {
            'match': lambda t: ("marvel's avengers" in t) or ("marvel's avengers" in t),
            'types': ["Full Price","Cosmetic MTX","In-Game Currency","Boosters (retired)","P2W: No"],
            'notes': "Primarily cosmetics; boosters removed; live service sunset."
        },
        {
            'match': lambda t: 'god of war' in t and 'ragnar' in t,
            'types': ["Base Game","Free DLC: Valhalla","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Base game + free Valhalla DLC; no in-game purchases; no pay-to-win."
        },
        # Skate series (legacy console releases; DLC packs, no MTX systems)
        {
            'match': lambda t: 'skate 2' in t,
            'types': ["Base Game","Paid DLC (legacy)","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Console-era release; optional DLC packs; no in-game store or P2W."
        },
        {
            'match': lambda t: 'skate 3' in t,
            'types': ["Base Game","Paid DLC (legacy)","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Console-era release; optional DLC packs; no in-game store or P2W."
        },
        {
            'match': lambda t: (t.strip().rstrip('.') == 'skate') or ('skate (2007)' in t),
            'types': ["Base Game","Paid DLC (legacy)","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "2007 base title; optional DLC; no MTX/loot boxes/battle pass; no P2W."
        },
        # Nightreign (2024 indie action platformer; single purchase, no MTX)
        {
            'match': lambda t: 'nightreign' in t,
            'types': ["Base Game","Paid DLC","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Indie roguelike platformer; one-time purchase; no in-game store or P2W."
        }
    ]
    
    if not title:
        return False
    
    tl = title.lower()
    for p in patterns:
        try:
            if p['match'](tl):
                monetisation_json = json.dumps(p['types'])
                # Check if override already exists
                existing = conn.execute("SELECT id FROM score_overrides WHERE game_id = ?", (game_id,)).fetchone()
                if existing:
                    # Only update if monetisation fields are empty/null
                    existing_override = conn.execute("SELECT monetisation_types, monetisation_notes FROM score_overrides WHERE game_id = ?", (game_id,)).fetchone()
                    if not existing_override[0] and not existing_override[1]:  # Both monetisation fields are empty
                        conn.execute("UPDATE score_overrides SET monetisation_types = ?, monetisation_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE game_id = ?",
                                     (monetisation_json, p['notes'], game_id))
                        return True
                else:
                    # Insert new override
                    conn.execute("INSERT INTO score_overrides (game_id, monetisation_types, monetisation_notes) VALUES (?, ?, ?)",
                                 (game_id, monetisation_json, p['notes']))
                    return True
                break
        except Exception:
            # Skip on pattern error
            continue
    return False

# ---------------- Admin: apply monetisation defaults ----------------

@app.post('/api/admin/apply-monetisation-defaults')
async def admin_apply_monetisation_defaults(recalc: bool = True, limit: Optional[int] = None) -> dict:
    """Apply default monetisation overrides for known titles by name heuristics.
    - recalc: when true, rescans each affected game to bake fairness into scores
    - limit: optionally cap the number of games processed (ordered by id)
    Returns summary per game with override status and fairness.
    """
    patterns = [
        {
            'match': lambda t: 'fortnite' in t and 'battle' in t,
            'types': ["Free-to-Play","Battle Pass","Cosmetic MTX","Item Shop","Loot Boxes: No","P2W: No"],
            'notes': "Cosmetic-only purchases; rotating shop; no gameplay advantages."
        },
        {
            'match': lambda t: 'ea sports fc' in t and any(x in t for x in [' 24',' 25',' 26']),
            'types': ["Full Price","Ultimate Team (FUT-like)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "Ultimate Team card packs and seasonal pass; spend influences online modes (mixed)."
        },
        # EA Sports titles (FIFA, Madden, NHL, NBA Live, etc.)
        {
            'match': lambda t: ('fifa' in t) and any(x in t for x in ['20','21','22','23','24','25']),
            'types': ["Full Price","Ultimate Team (FUT)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "FIFA Ultimate Team with card packs; spend affects competitive online modes."
        },
        {
            'match': lambda t: ('madden nfl' in t or 'madden' in t) and any(x in t for x in ['20','21','22','23','24','25']),
            'types': ["Full Price","Ultimate Team (MUT)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "Madden Ultimate Team with card packs; spend affects competitive online modes."
        },
        {
            'match': lambda t: ('nhl' in t) and any(x in t for x in ['20','21','22','23','24','25']),
            'types': ["Full Price","Ultimate Team (HUT)","Packs/Player Cards","Season Pass","In-Game Currency","P2W: Mixed"],
            'notes': "Hockey Ultimate Team with card packs; spend affects competitive online modes."
        },
        {
            'match': lambda t: ('nba live' in t) and any(x in t for x in ['19','20','21','22','23']),
            'types': ["Full Price","Ultimate Team","Packs/Player Cards","In-Game Currency","P2W: Mixed"],
            'notes': "NBA Live Ultimate Team with card packs; spend affects competitive modes."
        },
        {
            'match': lambda t: 'legend of zelda' in t and 'breath of the wild' in t,
            'types': ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Single purchase; no in-game store; no P2W."
        },
        {
            'match': lambda t: 'witcher 3' in t,
            'types': ["Base Game","Paid Expansions","No Loot Boxes","No Battle Pass","P2W: No"],
            'notes': "Paid expansions (Hearts of Stone, Blood and Wine); no microtransactions; no P2W."
        },
        {
            'match': lambda t: (
                ("marvel" in t and ("spider-man" in t or "spider man" in t or "spiderman" in t)) or
                ("miles morales" in t)
            ),
            'types': ["Base Game","Paid Expansions","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Single-player; optional paid DLC (The City That Never Sleeps / Remastered/Miles include content); no in-game purchases; no pay-to-win."
        },
        {
            'match': lambda t: 'marvel snap' in t,
            'types': ["Free-to-Play","Season Pass","Card Upgrades","In-Game Currency","Random Series Drops","P2W: Mixed"],
            'notes': "F2P CCG with season pass and progression; spend can accelerate collection and competitive advantage (mixed)."
        },
        {
            'match': lambda t: ("marvel’s avengers" in t) or ("marvel's avengers" in t),
            'types': ["Full Price","Cosmetic MTX","In-Game Currency","Boosters (retired)","P2W: No"],
            'notes': "Primarily cosmetics; boosters removed; live service sunset."
        },
        {
            'match': lambda t: 'god of war' in t and 'ragnar' in t,
            'types': ["Base Game","Free DLC: Valhalla","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Base game + free Valhalla DLC; no in-game purchases; no pay-to-win."
        },
        # Skate series (legacy console releases; DLC packs, no MTX systems)
        {
            'match': lambda t: 'skate 2' in t,
            'types': ["Base Game","Paid DLC (legacy)","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Console-era release; optional DLC packs; no in-game store or P2W."
        },
        {
            'match': lambda t: 'skate 3' in t,
            'types': ["Base Game","Paid DLC (legacy)","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Console-era release; optional DLC packs; no in-game store or P2W."
        },
        {
            'match': lambda t: (t.strip().rstrip('.') == 'skate') or ('skate (2007)' in t),
            'types': ["Base Game","Paid DLC (legacy)","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "2007 base title; optional DLC; no MTX/loot boxes/battle pass; no P2W."
        },
        # Nightreign (2024 indie action platformer; single purchase, no MTX)
        {
            'match': lambda t: 'nightreign' in t,
            'types': ["Base Game","Paid DLC","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"],
            'notes': "Indie roguelike platformer; one-time purchase; no in-game store or P2W."
        }
    ]
    processed = []
    applied_ids: list[int] = []
    # Phase 1: Apply overrides (DB write)
    with get_db() as conn:
        rows = conn.execute("SELECT id, title FROM games ORDER BY id ASC").fetchall()
        if limit is not None:
            try:
                lim = int(limit)
                if lim >= 0:
                    rows = rows[:lim]
            except Exception:
                pass
        for r in rows:
            gid = r['id']
            title = r['title'] or ''
            tl = title.lower()
            applied = False
            for p in patterns:
                try:
                    if p['match'](tl):
                        monetisation_json = json.dumps(p['types'])
                        exists = conn.execute("SELECT id FROM score_overrides WHERE game_id = ?", (gid,)).fetchone()
                        if exists:
                            conn.execute("UPDATE score_overrides SET monetisation_types = ?, monetisation_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE game_id = ?",
                                         (monetisation_json, p['notes'], gid))
                        else:
                            conn.execute("INSERT INTO score_overrides (game_id, monetisation_types, monetisation_notes) VALUES (?, ?, ?)",
                                         (gid, monetisation_json, p['notes']))
                        applied = True
                        break
                except Exception as _e:
                    # skip on pattern error
                    pass
            if applied:
                applied_ids.append(gid)
        conn.commit()
    # Phase 2: Rescan outside DB context to avoid locks
    if recalc and applied_ids:
        for gid in applied_ids:
            try:
                await scan_game(gid, force=True)
            except Exception:
                pass
    # Phase 3: Build summary (new DB context)
    with get_db() as conn2:
        for gid in [r['id'] for r in rows]:
            title = next((r['title'] for r in rows if r['id'] == gid), '')
            fairness = None
            try:
                srow = conn2.execute("SELECT reasoning FROM scores WHERE game_id = ?", (gid,)).fetchone()
                if srow and srow[0]:
                    reason = json.loads(srow[0])
                    md = (reason or {}).get('monetisation', {}).get('detailed', {})
                    if isinstance(md, dict):
                        fairness = {
                            'label': md.get('fairness_label'),
                            'color': md.get('fairness_color')
                        }
            except Exception:
                pass
            processed.append({
                'game_id': gid,
                'title': title,
                'override_applied': gid in applied_ids,
                'fairness': fairness
            })
    return { 'count': len(processed), 'results': processed }

# ---------------- Admin: Monetise Zelda franchise (bulk) ----------------

@app.post('/api/admin/monetise-zelda')
async def admin_monetise_zelda(recalc: bool = True, pages: int = 2, page_size: int = 40) -> dict:
    """Search RAWG for 'zelda' across pages, upsert games into DB, apply monetisation overrides,
    and optionally rescan to bake into scores. Returns a summary per affected game.

    Notes:
    - Mainline Legend of Zelda titles: Base Game; No MTX; No Loot Boxes; No Battle Pass; Single-player; P2W: No
    - Hyrule Warriors titles: Full Price; Paid DLC/Expansion Pass; No MTX; No Loot Boxes; No Battle Pass; P2W: No
    - Cadence of Hyrule: Base Game; Paid DLC; No MTX; No Loot Boxes; No Battle Pass; P2W: No
    """
    pages = max(1, min(5, int(pages)))
    page_size = max(1, min(40, int(page_size)))

    # Phase 1: Populate/refresh games via RAWG search
    seen_ids = set()
    for p in range(1, pages + 1):
        try:
            results = rawg_client.search_games('zelda', page_size=page_size, page=p)
        except Exception:
            results = {"results": []}
        with get_db() as conn:
            for game_data in results.get("results", []):
                rawg_id = game_data.get("id")
                if not rawg_id:
                    continue
                title = game_data.get("name", "Unknown Title")
                cover_image = game_data.get("background_image")
                # Release date/year from search payload
                rel = game_data.get('released')
                rel_year = None
                if isinstance(rel, str) and len(rel) >= 4:
                    try:
                        rel_year = int(rel[:4])
                    except Exception:
                        rel_year = None
                # Extract first platform name for legacy column
                platform = "multi-platform"
                platform_names: list[str] = []
                raw_platforms = game_data.get("platforms") or []
                if isinstance(raw_platforms, list):
                    for pl in raw_platforms:
                        if isinstance(pl, dict):
                            po = pl.get('platform') if 'platform' in pl else pl
                            if isinstance(po, dict) and isinstance(po.get('name'), str):
                                platform_names.append(po['name'])
                single_platform = platform_names[0] if platform_names else platform
                conn.execute(
                    """
                    INSERT OR IGNORE INTO games (title, rawg_id, platform, cover_image, release_year, release_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (title, rawg_id, single_platform, cover_image, rel_year, rel)
                )
                if cover_image:
                    conn.execute(
                        """
                        UPDATE games SET cover_image = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE rawg_id = ? AND (cover_image IS NULL OR cover_image = '')
                        """,
                        (cover_image, rawg_id)
                    )
                if single_platform and single_platform != platform:
                    conn.execute(
                        """
                        UPDATE games SET platform = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE rawg_id = ? AND (platform IS NULL OR platform = 'multi-platform')
                        """,
                        (single_platform, rawg_id)
                    )
                if rel_year:
                    conn.execute("UPDATE games SET release_year = ?, updated_at = CURRENT_TIMESTAMP WHERE rawg_id = ? AND (release_year IS NULL)", (rel_year, rawg_id))
                if isinstance(rel, str) and rel:
                    conn.execute("UPDATE games SET release_date = ?, updated_at = CURRENT_TIMESTAMP WHERE rawg_id = ? AND (release_date IS NULL)", (rel, rawg_id))
                row = conn.execute("SELECT id FROM games WHERE rawg_id = ?", (rawg_id,)).fetchone()
                if row:
                    seen_ids.add(int(row['id']))
            conn.commit()

    # Phase 2: Apply monetisation overrides based on title heuristics
    processed = []
    affected_ids: list[int] = []
    with get_db() as conn:
        # Select by id set OR fallback to title like search if none were newly seen
        rows = []
        if seen_ids:
            placeholders = ','.join(['?'] * len(seen_ids))
            rows = conn.execute(f"SELECT id, title FROM games WHERE id IN ({placeholders})", list(seen_ids)).fetchall()
        else:
            rows = conn.execute("SELECT id, title FROM games WHERE lower(title) LIKE '%zelda%' OR lower(title) LIKE '%hyrule warriors%' OR lower(title) LIKE '%cadence of hyrule%'").fetchall()

        for r in rows:
            gid = int(r['id'])
            title = (r['title'] or '').lower()
            types: list[str]
            notes: str
            if 'hyrule warriors' in title:
                types = ["Full Price","Paid DLC / Expansion Pass","No Microtransactions","No Loot Boxes","No Battle Pass","P2W: No"]
                notes = "Musou spin-off; Expansion Pass/paid DLC; no MTX/loot boxes; no P2W."
            elif 'cadence of hyrule' in title:
                types = ["Base Game","Paid DLC","No Microtransactions","No Loot Boxes","No Battle Pass","P2W: No"]
                notes = "Rhythm-action spin-off; paid DLC; no in-game purchases/MTX; no P2W."
            elif 'zelda' in title:  # default mainline LoZ pattern
                types = ["Base Game","No Microtransactions","No Loot Boxes","No Battle Pass","Single-player","P2W: No"]
                notes = "Single-player mainline entry; no in-game purchases; no P2W."
            else:
                continue
            monetisation_json = json.dumps(types)
            exists = conn.execute("SELECT id FROM score_overrides WHERE game_id = ?", (gid,)).fetchone()
            if exists:
                conn.execute(
                    "UPDATE score_overrides SET monetisation_types = ?, monetisation_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE game_id = ?",
                    (monetisation_json, notes, gid)
                )
            else:
                conn.execute(
                    "INSERT INTO score_overrides (game_id, monetisation_types, monetisation_notes) VALUES (?, ?, ?)",
                    (gid, monetisation_json, notes)
                )
            affected_ids.append(gid)
        conn.commit()

    # Phase 3: Rescan to bake into scores
    rescanned = []
    if recalc and affected_ids:
        for gid in affected_ids:
            try:
                await scan_game(gid, force=True)
                rescanned.append(gid)
            except Exception:
                pass

    # Phase 4: Summary with fairness labels
    summary = []
    with get_db() as conn2:
        for gid in affected_ids:
            title = conn2.execute("SELECT title FROM games WHERE id = ?", (gid,)).fetchone()
            fairness = None
            try:
                srow = conn2.execute("SELECT reasoning FROM scores WHERE game_id = ?", (gid,)).fetchone()
                if srow and srow[0]:
                    reason = json.loads(srow[0])
                    md = (reason or {}).get('monetisation', {}).get('detailed', {})
                    if isinstance(md, dict):
                        fairness = {
                            'label': md.get('fairness_label'),
                            'color': md.get('fairness_color')
                        }
            except Exception:
                pass
            summary.append({
                'game_id': gid,
                'title': title['title'] if title else None,
                'rescanned': gid in rescanned,
                'fairness': fairness
            })

    return { 'franchise': 'zelda', 'affected': len(affected_ids), 'summary': summary }

# ---------------- Legacy Scoring (v1) ----------------

@app.post('/api/admin/backfill-release-year')
async def admin_backfill_release_year(limit: Optional[int] = None) -> dict:
    """Populate missing games.release_year from RAWG game details for rows where it's NULL.
    Returns the number of rows updated and a sample list.
    """
    updated = 0
    processed = []
    with get_db() as conn:
        rows = conn.execute("SELECT id, rawg_id FROM games WHERE release_year IS NULL AND rawg_id IS NOT NULL ORDER BY id ASC").fetchall()
        if limit is not None:
            try:
                lim = int(limit)
                if lim >= 0:
                    rows = rows[:lim]
            except Exception:
                pass
        for r in rows:
            gid = r['id']
            rid = r['rawg_id']
            try:
                details = rawg_client.get_game_details(int(rid)) if rid else {}
                rel = details.get('released') if isinstance(details, dict) else None
                year = None
                if isinstance(rel, str) and len(rel) >= 4:
                    try:
                        year = int(rel[:4])
                    except Exception:
                        year = None
                if year:
                    conn.execute("UPDATE games SET release_year = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (year, gid))
                    updated += 1
                    processed.append({'game_id': gid, 'release_year': year})
            except Exception:
                continue
        conn.commit()
    return {'updated': updated, 'sample': processed[:10]}

@app.post('/api/admin/backfill-release-date')
async def admin_backfill_release_date(limit: Optional[int] = None) -> dict:
    """Populate missing games.release_date (YYYY-MM-DD) from RAWG game details for rows where it's NULL.
    Also sets release_year if it's still missing. Returns number of rows updated and a sample list.
    """
    updated = 0
    processed = []
    with get_db() as conn:
        rows = conn.execute("SELECT id, rawg_id FROM games WHERE release_date IS NULL AND rawg_id IS NOT NULL ORDER BY id ASC").fetchall()
        if limit is not None:
            try:
                lim = int(limit)
                if lim >= 0:
                    rows = rows[:lim]
            except Exception:
                pass
        for r in rows:
            gid = r['id']
            rid = r['rawg_id']
            try:
                details = rawg_client.get_game_details(int(rid)) if rid else {}
                rel_full = details.get('released') if isinstance(details, dict) else None
                if isinstance(rel_full, str) and len(rel_full) >= 4:
                    # Set date
                    conn.execute("UPDATE games SET release_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (rel_full, gid))
                    # Also set year if still null
                    try:
                        year = int(rel_full[:4])
                        conn.execute("UPDATE games SET release_year = COALESCE(release_year, ?), updated_at = CURRENT_TIMESTAMP WHERE id = ?", (year, gid))
                    except Exception:
                        pass
                    updated += 1
                    processed.append({'game_id': gid, 'release_date': rel_full})
            except Exception:
                continue
        conn.commit()
    return {'updated': updated, 'sample': processed[:10]}

def generate_scores_from_api_v1(game_data: dict, steam_data: dict = None) -> dict:
    """Original legacy scoring algorithm (version 1) preserved for rollback/reference."""
    raw_metacritic = game_data.get("metacritic")
    if not isinstance(raw_metacritic, (int, float)) or raw_metacritic is None:
        raw_metacritic = 70
    metacritic = int(max(0, min(100, raw_metacritic)))
    reviews_score = metacritic
    release_year = 2020
    if isinstance(game_data.get("released"), str) and len(game_data["released"]) >= 4:
        try:
            release_year = int(game_data["released"][:4])
        except ValueError:
            pass
    graphics_base = min(100, 60 + (release_year - 2010) * 2)
    graphic_score = min(100, graphics_base + (metacritic - 70) * 0.3)
    microtransactions_score = 85
    if steam_data and steam_data.get("price_overview"):
        microtransactions_score = 80
    rating_raw = game_data.get("rating")
    if not isinstance(rating_raw, (int, float)):
        rating_raw = 0
    rating = float(max(0, min(5, rating_raw)))
    game_mechanics_score = min(100, max(0, (rating * 20) + (metacritic * 0.3)))
    completeness_score = 80
    playtime_val = game_data.get("playtime")
    if not isinstance(playtime_val, (int, float)):
        playtime_val = 0
    if playtime_val:
        if playtime_val > 20:
            completeness_score = 90
        elif playtime_val > 10:
            completeness_score = 85
        else:
            completeness_score = 75
    genres = game_data.get("genres") or []
    if not isinstance(genres, list):
        genres = []
    genre_names = []
    for g in genres:
        if isinstance(g, dict):
            n = g.get("name")
            if isinstance(n, str):
                genre_names.append(n.lower())
    story_score = 75
    if "rpg" in genre_names or "adventure" in genre_names:
        story_score = min(100, metacritic + 5)
    elif "action" in genre_names:
        story_score = min(100, metacritic - 5)
    accessibility_score = 70
    if game_data.get("esrb_rating"):
        accessibility_score = 75
    overall_score = (
        reviews_score * 0.25 +
        graphic_score * 0.15 +
        microtransactions_score * 0.10 +
        game_mechanics_score * 0.20 +
        completeness_score * 0.15 +
        story_score * 0.10 +
        accessibility_score * 0.05
    )
    metacritic_count = game_data.get('metacritic_count') or 'multiple'
    reasoning = {
        'reviews_score': {'short': f'Metacritic: {metacritic}/100','detailed': f'Legacy v1 critic aggregate ({metacritic_count} sources).'},
        'graphic_score': {'short': f'Graphics heuristic {release_year}','detailed': 'Legacy graphics formula based on release year + metacritic delta.'},
        'microtransactions_score': {'short': 'Monetisation heuristic','detailed': 'Basic assumption; slight penalty if Steam pricing present.'},
        'game_mechanics_score': {'short': f'Rating {rating}/5','detailed': 'Combined RAWG rating + critic influence.'},
        'completeness_score': {'short': f'Playtime {playtime_val or 0}h','detailed': 'Legacy content length heuristic.'},
        'story_quality_score': {'short': 'Genre-based story estimate','detailed': 'Genre adjusted narrative proxy.'},
        'accessibility_score': {'short': 'Baseline accessibility','detailed': 'ESRB presence small bonus (legacy).'},
        'overall_score': {'short': f'Legacy Overall {overall_score:.1f}','detailed': 'Weighted legacy aggregate including reviews & accessibility.'}
    }

# ---------------- Community Telemetry Helpers ----------------
def _scale_positive(value: Optional[int], high: int) -> float:
    """Log/linear hybrid scaler to 0-100 for positive count metrics."""
    if not value or value <= 0:
        return 10.0
    # Use log scaling up to 'high' reference threshold
    try:
        ratio = min(1.0, math.log10(value + 1) / math.log10(high + 1))
    except (ValueError, ZeroDivisionError):
        ratio = 0.0
    # Smooth floor so small but non-zero still meaningful
    return max(10.0, round(ratio * 100, 2))

def fetch_steam_ccu(steam_id: int) -> Optional[int]:
    """Fetch current concurrent player count from Steam (public endpoint)."""
    try:
        url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
        resp = requests.get(url, params={"appid": steam_id}, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        return data.get('response', {}).get('player_count')
    except requests.RequestException:
        return None

def fetch_steam_reviews_summary(steam_id: int) -> dict:
    """Fetch Steam review summary (public appreviews endpoint). Returns dict or empty."""
    try:
        url = f"https://store.steampowered.com/appreviews/{steam_id}"
        params = {"json": 1, "language": "all", "purchase_type": "all"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}
        qs = data.get('query_summary', {})
        return {
            'total_positive': qs.get('total_positive'),
            'total_negative': qs.get('total_negative'),
            'total_reviews': qs.get('total_reviews'),
            'review_score': qs.get('review_score'),
            'review_score_desc': qs.get('review_score_desc'),
            'weighted_vote_score': qs.get('weighted_vote_score')
        }
    except requests.RequestException:
        return {}

def fetch_steam_achievements(steam_id: int) -> dict:
    """Fetch global achievement percentages; returns average percent & sample size if possible."""
    try:
        url = "https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
        resp = requests.get(url, params={"gameid": steam_id}, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}
        achieves = data.get('achievementpercentages', {}).get('achievements', [])
        if not achieves:
            return {}
        total = len(achieves)
        avg = sum(a.get('percent', 0) for a in achieves) / total if total else 0
        return {'achievements_sampled': total, 'achievements_avg_percent': round(avg,2)}
    except requests.RequestException:
        return {}

def compute_and_store_community_telemetry(conn: sqlite3.Connection, game_id: int, rawg_details: dict, steam_id: Optional[int] = None) -> dict:
    """Extract enriched community signals (RAWG + optional Steam) and persist snapshot with confidence."""
    ratings_count = rawg_details.get('ratings_count') or 0
    added = rawg_details.get('added') or 0
    updated_at = rawg_details.get('updated') or rawg_details.get('updated_at')

    steam_ccu = None
    steam_reviews_total = None
    steam_payload = None
    steam_reviews_summary = {}
    steam_achievements = {}
    if steam_id:
        # Try reuse of appdetails already fetched earlier if available else request again
        try:
            steam_details = steam_client.get_app_details(steam_id)
            if steam_details:
                steam_reviews_total = steam_details.get('recommendations', {}).get('total')
                steam_payload = {k: steam_details.get(k) for k in ['recommendations','price_overview','release_date','dlc']}
        except Exception:
            pass
        steam_ccu = fetch_steam_ccu(steam_id)
        steam_reviews_summary = fetch_steam_reviews_summary(steam_id)
        steam_achievements = fetch_steam_achievements(steam_id)

    # Derive submetrics via helper to allow reuse
    recomputed = recompute_telemetry_submetrics({
        'ratings_count': ratings_count,
        'added_count': added,
        'updated_rawg_at': updated_at,
        'steam_ccu': steam_ccu,
        'steam_reviews_total': steam_reviews_total,
        'steam_positive_reviews': steam_reviews_summary.get('total_positive'),
        'steam_negative_reviews': steam_reviews_summary.get('total_negative')
    })

    telemetry = {
        'ratings_count': ratings_count,
        'added_count': added,
        'updated_rawg_at': updated_at,
        'steam_ccu': steam_ccu,
        'steam_reviews_total': steam_reviews_total,
        'steam_positive_reviews': steam_reviews_summary.get('total_positive'),
        'steam_negative_reviews': steam_reviews_summary.get('total_negative'),
        **recomputed
    }
    # Attach review score & achievements
    telemetry['steam_review_score'] = steam_reviews_summary.get('review_score')
    telemetry['steam_weighted_vote'] = steam_reviews_summary.get('weighted_vote_score')
    telemetry['steam_achievements_sampled'] = steam_achievements.get('achievements_sampled')
    telemetry['steam_achievements_avg_percent'] = steam_achievements.get('achievements_avg_percent')

    raw_payload_full = json.dumps({'rawg_full': rawg_details})
    steam_payload_json = json.dumps(steam_payload) if steam_payload else None

    # Upsert with new columns
    existing = conn.execute("SELECT game_id FROM game_community_telemetry WHERE game_id = ?", (game_id,)).fetchone()
    if existing:
        conn.execute(
            """UPDATE game_community_telemetry
            SET ratings_count = ?, added_count = ?, updated_rawg_at = ?, steam_ccu = ?, steam_reviews_total = ?, confidence_score = ?,
                raw_payload = ?, steam_payload = ?, steam_positive_reviews = ?, steam_negative_reviews = ?, steam_review_score = ?,
                steam_weighted_vote = ?, steam_achievements_sampled = ?, steam_achievements_avg_percent = ?, last_scan_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE game_id = ?""",
            (ratings_count, added, updated_at, steam_ccu, steam_reviews_total, telemetry['confidence_score'], raw_payload_full, steam_payload_json,
             telemetry['steam_positive_reviews'], telemetry['steam_negative_reviews'], telemetry['steam_review_score'], telemetry['steam_weighted_vote'],
             telemetry['steam_achievements_sampled'], telemetry['steam_achievements_avg_percent'], game_id)
        )
    else:
        conn.execute(
            """INSERT INTO game_community_telemetry (game_id, ratings_count, added_count, updated_rawg_at, steam_ccu, steam_reviews_total, confidence_score, raw_payload, steam_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (game_id, ratings_count, added, updated_at, steam_ccu, steam_reviews_total, telemetry['confidence_score'], raw_payload_full, steam_payload_json)
        )
        # Follow-up update to add extended columns if first insert (simplify code path)
        conn.execute("UPDATE game_community_telemetry SET steam_positive_reviews = ?, steam_negative_reviews = ?, steam_review_score = ?, steam_weighted_vote = ?, steam_achievements_sampled = ?, steam_achievements_avg_percent = ? WHERE game_id = ?",
                     (telemetry['steam_positive_reviews'], telemetry['steam_negative_reviews'], telemetry['steam_review_score'], telemetry['steam_weighted_vote'], telemetry['steam_achievements_sampled'], telemetry['steam_achievements_avg_percent'], game_id))
    conn.commit()
    return telemetry

def recompute_telemetry_submetrics(base: dict) -> dict:
    ratings_count = base.get('ratings_count') or 0
    added = base.get('added_count') or 0
    # Submetrics: multiplayer proxy from participation counts (slightly higher ceiling)
    multiplayer_online = _scale_positive(ratings_count, high=6000)
    # Steam review positivity moderation (reduced impact, range -10..+10 scaled 20%)
    pos = base.get('steam_positive_reviews') or 0
    neg = base.get('steam_negative_reviews') or 0
    steam_ratio_factor = 0.0
    total_reviews = pos + neg
    if total_reviews > 50:
        positivity = pos / total_reviews
        # Map 0.4..0.9 -> -10..+10
        norm = (positivity - 0.4) / 0.5
        raw_factor = (norm * 20) - 10
        steam_ratio_factor = max(-10, min(10, raw_factor))
    community_engagement = round(
        (_scale_positive(ratings_count, 6000) * 0.45) +
        (_scale_positive(added, 4000) * 0.35) +
        (steam_ratio_factor * 0.20), 2)
    # Longevity recency
    longevity_component = 60.0
    updated_at = base.get('updated_rawg_at')
    if updated_at:
        try:
            last_dt = datetime.fromisoformat(updated_at.replace('Z','+00:00')) if 'T' in updated_at else datetime.fromisoformat(updated_at)
            delta_days = (datetime.utcnow() - last_dt).days
            if delta_days <= 30:
                longevity_component += 15
            elif delta_days <= 90:
                longevity_component += 10
            elif delta_days <= 180:
                longevity_component += 5
            elif delta_days > 365:
                longevity_component -= 5
        except Exception:
            pass
    if ratings_count > 3000 and added > 1500:
        longevity_component += 5
    longevity_component = max(40, min(95, longevity_component))
    # Confidence scoring
    steam_ccu = base.get('steam_ccu') or 0
    steam_ccu_scaled = _scale_positive(steam_ccu, high=50000) if steam_ccu else None
    recency_score = 50
    try:
        if updated_at:
            last_dt = datetime.fromisoformat(updated_at.replace('Z','+00:00')) if 'T' in updated_at else datetime.fromisoformat(updated_at)
            d = (datetime.utcnow() - last_dt).days
            if d <= 30: recency_score = 95
            elif d <= 90: recency_score = 80
            elif d <= 180: recency_score = 65
            elif d <= 365: recency_score = 50
            else: recency_score = 35
    except Exception:
        pass
    weights = {
        'ratings': 0.3,
        'added': 0.2,
        'recency': 0.25,
        'steam': 0.25 if steam_ccu_scaled is not None else 0.0
    }
    weight_norm = sum(v for k,v in weights.items() if not (k=='steam' and steam_ccu_scaled is None))
    conf = (
        _scale_positive(ratings_count,5000)*weights['ratings'] +
        _scale_positive(added,3000)*weights['added'] +
        recency_score*weights['recency'] +
        (steam_ccu_scaled or 0)*weights['steam']
    )/weight_norm
    confidence_score = round(conf,2)
    return {
        'multiplayer_online': round(multiplayer_online,2),
        'community_engagement': round(community_engagement,2),
        'longevity': round(longevity_component,2),
        'confidence_score': confidence_score
    }

def apply_community_longevity_telemetry(score_data: dict, telemetry: dict) -> dict:
    """Override placeholder community longevity metrics with telemetry-driven values and recompute category + overall.
    telemetry keys: multiplayer_online, community_engagement, longevity
    """
    if 'reasoning' not in score_data:
        return score_data
    # Replace detailed submetrics if structure present; otherwise create stub
    cl_reason = score_data['reasoning'].setdefault('community_longevity', {
        'short': 'Community & Longevity (telemetry applied)',
        'detailed': {}
    })
    detailed = cl_reason.setdefault('detailed', {})
    detailed['multiplayer_online'] = telemetry['multiplayer_online']
    detailed['community_engagement'] = telemetry['community_engagement']
    detailed['longevity'] = telemetry['longevity']
    detailed['source'] = 'RAWG/Steam telemetry heuristic'
    if telemetry.get('confidence_score') is not None:
        detailed['confidence_score'] = telemetry['confidence_score']
    if telemetry.get('steam_ccu') is not None:
        detailed['steam_ccu'] = telemetry['steam_ccu']
    if telemetry.get('steam_reviews_total') is not None:
        detailed['steam_reviews_total'] = telemetry['steam_reviews_total']
    if telemetry.get('steam_positive_reviews') is not None:
        detailed['steam_positive_reviews'] = telemetry['steam_positive_reviews']
    if telemetry.get('steam_negative_reviews') is not None:
        detailed['steam_negative_reviews'] = telemetry['steam_negative_reviews']
    if telemetry.get('steam_review_score') is not None:
        detailed['steam_review_score'] = telemetry['steam_review_score']
    if telemetry.get('steam_weighted_vote') is not None:
        detailed['steam_weighted_vote'] = telemetry['steam_weighted_vote']
    if telemetry.get('steam_achievements_sampled') is not None:
        detailed['steam_achievements_sampled'] = telemetry['steam_achievements_sampled']
    if telemetry.get('steam_achievements_avg_percent') is not None:
        detailed['steam_achievements_avg_percent'] = telemetry['steam_achievements_avg_percent']

    # Recompute community_longevity_score with same weights 2/5,2/5,1/5
    community_score = (
        telemetry['multiplayer_online'] * (2/5) +
        telemetry['community_engagement'] * (2/5) +
        telemetry['longevity'] * (1/5)
    )
    score_data['community_longevity_score'] = round(community_score,1)
    # Recompute overall (exclude informational metrics as before)
    overall = (
        score_data['core_gameplay_score'] * 0.25 +
        score_data['story_immersion_score'] * 0.20 +
        score_data['presentation_score'] * 0.15 +
        score_data['technical_performance_score'] * 0.15 +
        score_data['completeness_score'] * 0.10 +
        score_data['innovation_creativity_score'] * 0.10 +
        score_data['community_longevity_score'] * 0.05
    )
    score_data['overall_score'] = round(overall,1)
    if 'overall_score' in score_data['reasoning']:
        score_data['reasoning']['overall_score']['short'] = f"Weighted Overall: {overall:.1f}/100"
    # Update community short line
    cl_reason['short'] = f"Community & Longevity: {community_score:.1f}/100 (telemetry)"
    return score_data

@app.get('/api/games/{game_id}/community-telemetry')
async def get_community_telemetry(game_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM game_community_telemetry WHERE game_id = ?", (game_id,)).fetchone()
        if not row:
            return {"game_id": game_id, "telemetry": None}
        data = dict(row)
        # Provide derived submetrics (recompute with current logic for forward compatibility)
        derived = recompute_telemetry_submetrics({
            'ratings_count': data.get('ratings_count'),
            'added_count': data.get('added_count'),
            'updated_rawg_at': data.get('updated_rawg_at'),
            'steam_ccu': data.get('steam_ccu')
        })
        data['derived'] = derived
        return {"game_id": game_id, "telemetry": data}

# --- MVP Intelligence Endpoints ---
@app.get('/api/games/{game_id}/innovation-metrics')
async def get_innovation_metrics(game_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM game_innovation_metrics WHERE game_id = ?", (game_id,)).fetchone()
        if not row:
            return {"game_id": game_id, "innovation": None}
        data = dict(row)
        try:
            data['summary'] = json.loads(data['summary_json']) if data.get('summary_json') else {}
        except Exception:
            data['summary'] = {}
        return {"game_id": game_id, "innovation": data}

@app.get('/api/games/{game_id}/accessibility-features')
async def get_accessibility_features_metrics(game_id: int):
    with get_db() as conn:
        rows = conn.execute("SELECT feature_key, present, confidence, evidence, created_at FROM game_accessibility_features WHERE game_id = ?", (game_id,)).fetchall()
        feats = []
        for r in rows:
            feats.append({
                'feature_key': r[0],
                'present': bool(r[1]),
                'confidence': r[2],
                'evidence': r[3],
                'created_at': r[4]
            })
        return {"game_id": game_id, "features": feats}

@app.get('/api/games/{game_id}/life-support-inferred')
async def get_life_support_inferred(game_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM game_life_support_inference WHERE game_id = ?", (game_id,)).fetchone()
        if not row:
            return {"game_id": game_id, "life_support_inferred": None}
        data = dict(row)
        try:
            data['evidence'] = json.loads(data['evidence_json']) if data.get('evidence_json') else {}
        except Exception:
            data['evidence'] = {}
        return {"game_id": game_id, "life_support_inferred": data}

# Life support helper
def apply_life_support(score_data: dict, life_row: sqlite3.Row, persist: bool = False, conn=None):
    """Apply life support adjustments to community longevity & overall.
    Status mapping:
      eternal: +10, active: +5, sunset: -5, offline: -10, unknown: 0
    Only recompute if delta != 0 or for annotation. Adds reasoning.life_support.
    If persist=True updates DB (requires conn and assumes scores already inserted/updated).
    """
    status = (life_row['support_status'] or 'unknown').lower()
    delta_map = {'eternal':10,'active':5,'sunset':-5,'offline':-10,'unknown':0}
    delta = delta_map.get(status,0)
    orig = score_data.get('community_longevity_score') or 0
    if delta:
        new_comm = max(0,min(100,orig+delta))
        score_data['community_longevity_score'] = round(new_comm,1)
        # Recompute overall
        overall = (
            score_data['core_gameplay_score'] * 0.25 +
            score_data['story_immersion_score'] * 0.20 +
            score_data['presentation_score'] * 0.15 +
            score_data['technical_performance_score'] * 0.15 +
            score_data['completeness_score'] * 0.10 +
            score_data['innovation_creativity_score'] * 0.10 +
            score_data['community_longevity_score'] * 0.05
        )
        score_data['overall_score'] = round(overall,1)
        if 'overall_score' in score_data.get('reasoning',{}):
            score_data['reasoning']['overall_score']['short'] = f"Weighted Overall: {overall:.1f}/100"
    # annotate reasoning
    score_data.setdefault('reasoning',{})
    ls_detail = {
        'status': status,
        'delta_applied': delta,
        'last_update_date': life_row['last_update_date'],
        'next_update_hint': life_row['next_update_hint'],
        'notes': life_row['notes']
    }
    score_data['reasoning']['life_support'] = {
        'short': f"Life Support: {status.title()} ({'+' if delta>0 else ''}{delta})",
        'detailed': ls_detail
    }
    # enrich community longevity detailed block
    try:
        cl_det = score_data['reasoning'].get('community_longevity',{}).get('detailed',{})
        if isinstance(cl_det, dict):
            cl_det['life_support_status'] = status
            cl_det['life_support_delta'] = delta
    except Exception:
        pass
    if persist and conn is not None:
        try:
            conn.execute("UPDATE scores SET community_longevity_score = ?, overall_score = ?, reasoning = ?, updated_at = CURRENT_TIMESTAMP WHERE game_id = ?",
                         (score_data['community_longevity_score'], score_data['overall_score'], json.dumps(score_data['reasoning']), life_row['game_id']))
            conn.commit()
        except Exception as e:
            print(f"Persist life support failed: {e}")
    return score_data

    

@app.get('/api/games/{game_id}/scores')
async def get_scores_by_version(game_id: int, version: int = SCORING_VERSION, recalc: bool = False):
    """Retrieve scores for a specific scoring version. For version=1 (legacy) can recalc if not archived."""
    with get_db() as conn:
        if version == SCORING_VERSION:
            row = conn.execute("SELECT * FROM scores WHERE game_id = ?", (game_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail='Scores not found for current version')
            sd = dict(row)
            try:
                sd['reasoning'] = json.loads(sd['reasoning'])
            except Exception:
                pass
            sd['scoring_version'] = SCORING_VERSION
            return sd
        elif version == 1:
            archived = conn.execute("SELECT payload_json FROM scores_archive WHERE game_id = ? AND scoring_version = 1", (game_id,)).fetchone()
            if archived and not recalc:
                return json.loads(archived[0])
            # Recalculate on demand (does not overwrite archive unless absent)
            game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
            if not game:
                raise HTTPException(status_code=404, detail='Game not found')
            rawg_id = game['rawg_id']
            rawg_details = rawg_client.get_game_details(rawg_id) if rawg_id else {}
            payload = generate_scores_from_api_v1(rawg_details)
            if not archived:
                try:
                    conn.execute("INSERT OR IGNORE INTO scores_archive (game_id, scoring_version, payload_json) VALUES (?, ?, ?)", (game_id, 1, json.dumps(payload)))
                    conn.commit()
                except Exception:
                    pass
            return payload
        else:
            raise HTTPException(status_code=400, detail='Unsupported scoring version')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)