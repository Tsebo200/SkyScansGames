from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime, timedelta
import os
from contextlib import contextmanager
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time
from functools import lru_cache

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")

app = FastAPI(title="SkyScansGames API", version="1.0.0")

# Configuration
RAWG_API_KEY = os.getenv("RAWG_API_KEY", "demo")  # Get from environment or use demo
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "")
CACHE_TTL = 3600  # 1 hour cache

# Caching configuration
API_CACHE_TTL = 1800  # 30 minutes for API responses
SEARCH_CACHE_TTL = 600  # 10 minutes for search results

@lru_cache(maxsize=100)
def get_cache_key(url: str, params: str = "") -> str:
    """Generate cache key from URL and parameters"""
    key_data = f"{url}|{params}"
    return hashlib.md5(key_data.encode()).hexdigest()

def get_cached_response(cache_key: str) -> dict:
    """Get cached API response from database"""
    with get_db() as conn:
        result = conn.execute("""
            SELECT response, expires_at FROM api_cache 
            WHERE id = ? AND expires_at > datetime('now')
        """, (cache_key,)).fetchone()
        
        if result:
            return json.loads(result[0])
    return None

def set_cached_response(cache_key: str, response: dict, ttl: int):
    """Cache API response in database"""
    expires_at = time.time() + ttl
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO api_cache (id, url, response, expires_at)
            VALUES (?, '', ?, datetime(?, 'unixepoch'))
        """, (cache_key, json.dumps(response), expires_at))
        conn.commit()

# API Clients
class RAWGClient:
    BASE_URL = "https://api.rawg.io/api"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search_games(self, query: str, page_size: int = 10) -> dict:
        """Search for games using RAWG API with caching"""
        url = f"{self.BASE_URL}/games"
        params = {
            "key": self.api_key,
            "search": query,
            "page_size": page_size,
            "search_precise": True
        }
        
        # Create cache key
        cache_key = get_cache_key(url, str(params))
        
        # Check cache first
        cached_result = get_cached_response(cache_key)
        if cached_result:
            print(f"Cache hit for search: {query}")
            return cached_result
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Cache the result
            set_cached_response(cache_key, result, SEARCH_CACHE_TTL)
            return result
        except requests.RequestException as e:
            print(f"RAWG API error: {e}")
            # If API key is invalid, return demo games for testing
            if "401" in str(e) or "Unauthorized" in str(e):
                demo_result = self._get_demo_games(query)
                # Cache demo result for shorter time
                set_cached_response(cache_key, demo_result, 300)  # 5 minutes
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
DATABASE_URL = "skyscans_games.db"

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
                generation INTEGER,
                platform TEXT,
                engine TEXT,
                rawg_id INTEGER,
                steam_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')

        # Cache table for API responses
        conn.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
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

def generate_scores_from_api(game_data: dict, steam_data: dict = None) -> dict:
    """Generate scores based on RAWG and Steam API data"""
    
    # Base scores from RAWG metacritic score
    metacritic = game_data.get("metacritic", 70)
    reviews_score = min(100, max(0, metacritic))
    
    # Graphics score based on release year and platforms
    release_year = int(game_data.get("released", "2020")[:4]) if game_data.get("released") else 2020
    graphics_base = min(100, 60 + (release_year - 2010) * 2)  # Older games get lower base score
    graphic_score = min(100, graphics_base + (metacritic - 70) * 0.3)
    
    # Microtransactions score - assume good unless we have Steam data indicating otherwise
    microtransactions_score = 85  # Default good score
    if steam_data and steam_data.get("price_overview"):
        # If game has DLC or in-game purchases, slightly lower score
        microtransactions_score = 80
    
    # Game mechanics score based on user ratings and critic scores
    rating = game_data.get("rating", 3.5)
    game_mechanics_score = min(100, max(0, (rating * 20) + (metacritic * 0.3)))
    
    # Completeness score based on game length and content
    completeness_score = 80  # Default good score
    if game_data.get("playtime"):
        playtime = game_data.get("playtime", 0)
        if playtime > 20:
            completeness_score = 90
        elif playtime > 10:
            completeness_score = 85
        else:
            completeness_score = 75
    
    # Story quality score - estimate based on genre and critic reception
    genres = game_data.get("genres", [])
    genre_names = [g.get("name", "").lower() for g in genres]
    story_score = 75  # Default
    if "rpg" in genre_names or "adventure" in genre_names:
        story_score = min(100, metacritic + 5)  # RPGs and adventures often have better stories
    elif "action" in genre_names:
        story_score = min(100, metacritic - 5)  # Action games may focus less on story
    
    # Accessibility score - basic estimation
    accessibility_score = 70  # Default moderate score
    if game_data.get("esrb_rating"):
        # Games with ESRB ratings tend to have better accessibility considerations
        accessibility_score = 75
    
    # Overall score as weighted average
    overall_score = (
        reviews_score * 0.25 +
        graphic_score * 0.15 +
        microtransactions_score * 0.10 +
        game_mechanics_score * 0.20 +
        completeness_score * 0.15 +
        story_score * 0.10 +
        accessibility_score * 0.05
    )
    
    # Generate reasoning based on the data
    metacritic_count = game_data.get('metacritic_count', 'multiple')
    data_source_note = "Note: Scores are based on data from RAWG.io, which aggregates information from various sources. Actual scores may vary slightly from official sources."
    
    reasoning = {
        "reviews_score": {
            "short": f"RAWG-reported Metacritic: {metacritic}/100",
            "detailed": f"Based on critic reviews aggregated by RAWG.io. The game received a score of {metacritic}/100 from {metacritic_count} critic reviews. {data_source_note}"
        },
        "graphic_score": {
            "short": f"Graphics quality for {release_year} release",
            "detailed": f"Graphics score estimated based on release year ({release_year}) and critic reception from RAWG data. Modern games receive higher base scores, adjusted by critic feedback."
        },
        "microtransactions_score": {
            "short": "Estimated based on platform and pricing model",
            "detailed": "Score based on the game's monetization strategy as reported by available data sources. Games with straightforward pricing models receive higher scores."
        },
        "game_mechanics_score": {
            "short": f"User rating: {rating}/5 stars (RAWG)",
            "detailed": f"Gameplay quality assessed through user ratings ({rating}/5) from RAWG.io and critic reception. Combines community feedback with professional analysis."
        },
        "completeness_score": {
            "short": f"Estimated playtime: {game_data.get('playtime', 'Unknown')} hours",
            "detailed": f"Content completeness evaluated based on estimated playtime and game scope from RAWG data. Longer games with more content receive higher scores."
        },
        "story_quality_score": {
            "short": f"Genre-based story quality estimate",
            "detailed": f"Story quality estimated based on game genre ({', '.join(genre_names) if genre_names else 'Unknown'}) and overall critic reception from RAWG. RPGs and adventures typically have stronger narratives."
        },
        "accessibility_score": {
            "short": "Basic accessibility assessment",
            "detailed": "Accessibility score based on ESRB rating and general game design principles from available data. Modern games with accessibility features receive higher scores."
        },
        "overall_score": {
            "short": f"Weighted average: {overall_score:.1f}/100",
            "detailed": f"Overall score calculated as a weighted average of all metrics using data from RAWG.io. {data_source_note}"
        }
    }
    
    return {
        "reviews_score": round(reviews_score, 1),
        "graphic_score": round(graphic_score, 1),
        "microtransactions_score": round(microtransactions_score, 1),
        "game_mechanics_score": round(game_mechanics_score, 1),
        "completeness_score": round(completeness_score, 1),
        "story_quality_score": round(story_score, 1),
        "accessibility_score": round(accessibility_score, 1),
        "overall_score": round(overall_score, 1),
        "reasoning": reasoning
    }
# Initialize database on startup
# init_db()  # Removed from here - will be called in startup event

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Game(BaseModel):
    id: int
    title: str
    generation: Optional[int] = None
    platform: Optional[str] = None
    engine: Optional[str] = None
    rawg_id: Optional[int] = None
    steam_id: Optional[int] = None

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

class GameWithScores(BaseModel):
    game: Game
    scores: Optional[ScoreMetrics] = None

@app.get("/api/games/search", response_model=List[Game])
async def search_games(q: str = "", gen: Optional[int] = None):
    if not q:
        # If no query, return local games
        with get_db() as conn:
            results = conn.execute("SELECT * FROM games").fetchall()
            return [Game(**dict(row)) for row in results]
    
    # Search RAWG API first
    rawg_results = rawg_client.search_games(q, page_size=10)
    
    games = []
    with get_db() as conn:
        for game_data in rawg_results.get("results", []):
            # Check if game already exists in database
            existing = conn.execute("SELECT * FROM games WHERE rawg_id = ?", (game_data["id"],)).fetchone()
            
            if existing:
                game = Game(**dict(existing))
            else:
                # Insert new game into database
                conn.execute("""
                    INSERT INTO games (title, rawg_id, platform, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    game_data["name"],
                    game_data["id"],
                    "multi-platform"  # Default platform
                ))
                
                # Get the inserted game
                game_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                game_row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
                game = Game(**dict(game_row))
            
            games.append(game)
        
        conn.commit()
    
    return games

@app.post("/api/games/{game_id}/scan")
async def scan_game(game_id: int):
    with get_db() as conn:
        # Check if game exists
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Check if scores already exist
        scores = conn.execute("SELECT * FROM scores WHERE game_id = ?", (game_id,)).fetchone()
        if scores:
            score_dict = dict(scores)
            score_dict["reasoning"] = json.loads(score_dict["reasoning"])
            return {"status": "completed", "scores": score_dict}

        # Get detailed game data from RAWG API
        game_dict = dict(game)
        rawg_id = game_dict.get("rawg_id")
        
        if rawg_id:
            # Get detailed game data from RAWG
            rawg_details = rawg_client.get_game_details(rawg_id)
            
            # Debug logging for data verification
            print(f"RAWG data for game {rawg_id}: Metacritic={rawg_details.get('metacritic')}, Rating={rawg_details.get('rating')}")
            
            steam_data = {}
            
            # Try to get Steam data if steam_id exists
            steam_id = game_dict.get("steam_id")
            if steam_id:
                steam_data = steam_client.get_app_details(steam_id)
            
            # Generate scores from API data
            score_data = generate_scores_from_api(rawg_details, steam_data)
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

        # Insert scores into database
        conn.execute("""
            INSERT INTO scores (game_id, reviews_score, graphic_score, microtransactions_score,
                              game_mechanics_score, completeness_score, story_quality_score,
                              accessibility_score, overall_score, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id,
            score_data["reviews_score"],
            score_data["graphic_score"],
            score_data["microtransactions_score"],
            score_data["game_mechanics_score"],
            score_data["completeness_score"],
            score_data["story_quality_score"],
            score_data["accessibility_score"],
            score_data["overall_score"],
            json.dumps(score_data["reasoning"])
        ))
        conn.commit()

        return {"status": "completed", "scores": score_data}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)