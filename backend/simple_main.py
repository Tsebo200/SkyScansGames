from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="SkyScansGames API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Game(BaseModel):
    id: int
    title: str
    generation: Optional[int] = None
    platform: Optional[str] = None
    rawg_id: Optional[int] = None

def get_detailed_reasoning(game_id, game_data, reviews_score, graphic_score, game_mechanics_score, completeness_score, story_score, accessibility_score, overall_score):
    """Generate detailed, honest reasoning for each metric"""
    
    metacritic = game_data["metacritic"]
    rating = game_data["rating"]
    release_year = int(game_data["released"][:4])
    playtime = game_data["playtime"]
    genres = game_data["genres"]
    genre_names = [g["name"].lower() for g in genres]
    
    game_names = {
        1: "God of War (2018)",
        2: "God of War Ragnarök", 
        3: "God of War I",
        4: "FIFA 23",
        5: "FIFA 22"
    }
    
    game_name = game_names.get(game_id, "Unknown Game")
    
    if game_id == 1:  # God of War (2018)
        return {
            "reviews_score": {
                "short": f"Critic Score: {metacritic}/100",
                "detailed": f"God of War (2018) received widespread critical acclaim with a Metacritic score of {metacritic}/100. Critics praised the game's narrative depth, combat system, and character development, calling it one of the best games of 2018."
            },
            "graphic_score": {
                "short": f"Excellent graphics for 2018 release",
                "detailed": f"Despite being released in 2018, God of War's graphics remain impressive with stunning Norse mythology-inspired art direction, detailed character models, and expansive open-world environments. The game's visual style perfectly complements its mature storytelling."
            },
            "microtransactions_score": {
                "short": "No microtransactions - premium experience",
                "detailed": "God of War (2018) follows a traditional premium pricing model with no microtransactions or loot boxes. The game is sold as a complete experience with all content included at purchase, which is increasingly rare in modern gaming."
            },
            "game_mechanics_score": {
                "short": f"Outstanding combat and exploration",
                "detailed": f"With a user rating of {rating}/5, God of War excels in its combat system combining Kratos' Leviathan Axe with Atreus' bow for varied gameplay. The exploration feels rewarding with meaningful discoveries and side activities."
            },
            "completeness_score": {
                "short": f"Solid {playtime} hour main campaign",
                "detailed": f"The main story provides about {playtime} hours of content with additional replayability through New Game+ mode and collectibles. While not the longest game, the quality of content makes it feel complete and satisfying."
            },
            "story_quality_score": {
                "short": f"Exceptional narrative depth",
                "detailed": f"As an action-adventure game, God of War delivers an emotionally powerful story about redemption and family. The character development of Kratos and Atreus is among the best in gaming, with mature themes handled exceptionally well."
            },
            "accessibility_score": {
                "short": "Mature rating with good accessibility",
                "detailed": f"Rated M for Mature due to violence and thematic elements, the game includes accessibility options like adjustable difficulty, subtitles, and colorblind support. The controls are intuitive once learned, though the combat has a learning curve."
            },
            "overall_score": {
                "short": f"Masterpiece: {round(overall_score, 1)}/100",
                "detailed": f"God of War (2018) represents gaming excellence with its perfect blend of storytelling, gameplay, and technical achievement. It's widely regarded as one of the greatest games of its generation and a must-play for action-adventure fans."
            }
        }
    
    elif game_id == 2:  # God of War Ragnarök
        return {
            "reviews_score": {
                "short": f"Universal acclaim: {metacritic}/100",
                "detailed": f"God of War Ragnarök achieved near-perfect critical reception with a Metacritic score of {metacritic}/100. Reviewers called it the worthy conclusion to Kratos' journey, praising its scope, storytelling, and technical achievements."
            },
            "graphic_score": {
                "short": f"State-of-the-art PS5 graphics",
                "detailed": f"Built for PS5, Ragnarök showcases cutting-edge graphics with ray tracing, 4K resolution, and smooth 60fps gameplay. The Norse world feels alive with dynamic weather, destructible environments, and incredible attention to detail."
            },
            "microtransactions_score": {
                "short": "Premium game with fair DLC",
                "detailed": f"The base game is complete with no microtransactions, though it includes optional DLC packs that expand the story. This approach respects players while providing additional content for those who want more of the Norse saga."
            },
            "game_mechanics_score": {
                "short": f"Refined combat and exploration",
                "detailed": f"Building on the 2018 foundation, Ragnarök offers {rating}/5 user-rated gameplay with improved combat variety, expanded exploration, and meaningful choices that affect the story. The Leviathan Axe and Blades of Chaos provide satisfying combat options."
            },
            "completeness_score": {
                "short": f"Extensive {playtime}+ hour experience",
                "detailed": f"With over {playtime} hours of main content plus substantial side activities, Ragnarök offers excellent value. The game includes multiple endings, extensive collectibles, and replayable challenges that extend the experience significantly."
            },
            "story_quality_score": {
                "short": f"Emotional conclusion to the saga",
                "detailed": f"The narrative reaches new heights with deeper character relationships, Norse mythology exploration, and emotional stakes. The game's themes of family, legacy, and redemption are handled with maturity and nuance."
            },
            "accessibility_score": {
                "short": "Mature content with accessibility features",
                "detailed": f"Rated M for violence and mature themes, Ragnarök includes comprehensive accessibility options including difficulty adjustment, control customization, and support for various disabilities. The game is more approachable than its predecessor."
            },
            "overall_score": {
                "short": f"Generation-defining masterpiece",
                "detailed": f"God of War Ragnarök is a technical and narrative triumph that pushes the boundaries of what action-adventure games can achieve. It's a fitting end to one of gaming's most beloved sagas and a benchmark for future titles."
            }
        }
    
    elif game_id == 3:  # God of War I
        return {
            "reviews_score": {
                "short": f"Classic excellence: {metacritic}/100",
                "detailed": f"Even nearly 20 years later, the original God of War maintains a strong Metacritic score of {metacritic}/100. It revolutionized action games with its cinematic style and brutal combat, influencing countless titles that followed."
            },
            "graphic_score": {
                "short": f"Impressive for 2005 PS2 era",
                "detailed": f"For a PS2 game from 2005, God of War I's graphics were groundbreaking with detailed character models, fluid animations, and cinematic camera work. While dated by modern standards, it still holds up as a technical achievement for its time."
            },
            "microtransactions_score": {
                "short": "Retro premium pricing model",
                "detailed": f"As a retro game, God of War I follows the traditional model of complete games without microtransactions. Players get the full experience at purchase price, which was standard for its era and remains preferable to modern monetization schemes."
            },
            "game_mechanics_score": {
                "short": f"Innovative combat for its time",
                "detailed": f"With a {rating}/5 user rating, the original God of War introduced revolutionary combat mechanics including contextual button prompts and brutal finishing moves. The puzzle-platforming elements added welcome variety to the action."
            },
            "completeness_score": {
                "short": f"Solid {playtime} hour classic experience",
                "detailed": f"The game provides about {playtime} hours of tightly crafted gameplay with multiple difficulty levels and unlockable content. While shorter than modern games, every moment feels purposeful and well-designed."
            },
            "story_quality_score": {
                "short": f"Mythology-driven action narrative",
                "detailed": f"God of War I weaves Greek mythology into an action-driven story of revenge and betrayal. The narrative serves the gameplay well, with each boss fight advancing the plot in memorable ways."
            },
            "accessibility_score": {
                "short": "Mature content, dated controls",
                "detailed": f"Rated M for violence and gore, the game has basic accessibility features typical of its era. Modern players may find the controls challenging, but the game includes multiple difficulty options to adjust the experience."
            },
            "overall_score": {
                "short": f"Timeless action game foundation",
                "detailed": f"God of War I laid the groundwork for one of gaming's most successful franchises. Its influence on action games remains evident today, and it still provides an entertaining experience for fans of classic action-adventure games."
            }
        }
    
    elif game_id in [4, 5]:  # FIFA games
        fifa_year = "2023" if game_id == 4 else "2022"
        return {
            "reviews_score": {
                "short": f"Sports game score: {metacritic}/100",
                "detailed": f"FIFA {fifa_year} received a Metacritic score of {metacritic}/100, which is solid for an annual sports title. The series consistently delivers polished gameplay with incremental improvements each year."
            },
            "graphic_score": {
                "short": f"Modern sports graphics quality",
                "detailed": f"FIFA {fifa_year} features current-generation graphics with detailed player models, realistic stadiums, and smooth animations. The visual presentation meets expectations for a premium sports simulation."
            },
            "microtransactions_score": {
                "short": "Mixed monetization approach",
                "detailed": f"Like most modern sports games, FIFA includes Ultimate Team with microtransactions for card packs. While the core gameplay is complete, the monetization strategy can feel aggressive for competitive players."
            },
            "game_mechanics_score": {
                "short": f"Polished sports simulation",
                "detailed": f"With a {rating}/5 user rating, FIFA {fifa_year} offers refined soccer mechanics with realistic physics, AI improvements, and various gameplay modes. The series continues to evolve with each iteration."
            },
            "completeness_score": {
                "short": f"Comprehensive sports package",
                "detailed": f"FIFA provides extensive content with multiple modes, leagues, and teams. The {playtime} hour estimate reflects focused gameplay sessions, but the game's depth supports hundreds of hours for dedicated players."
            },
            "story_quality_score": {
                "short": f"Sports simulation focus",
                "detailed": f"As a sports simulation, FIFA prioritizes gameplay over narrative. Career mode provides some story elements, but the focus remains on authentic soccer simulation rather than dramatic storytelling."
            },
            "accessibility_score": {
                "short": f"Family-friendly with options",
                "detailed": f"Rated E for Everyone, FIFA includes accessibility features like adjustable difficulty, control customization, and support for various input methods. The game is designed to be approachable for players of all skill levels."
            },
            "overall_score": {
                "short": f"Solid annual sports release",
                "detailed": f"FIFA {fifa_year} delivers the expected quality of an established sports franchise with incremental improvements and comprehensive content. It's the standard-bearer for soccer simulation gaming."
            }
        }
    
    # Default reasoning for any other games
    return {
        "reviews_score": {
            "short": f"Critic Score: {metacritic}/100",
            "detailed": f"Based on aggregated critic reviews from Metacritic and other sources."
        },
        "graphic_score": {
            "short": f"Graphics quality for {release_year}",
            "detailed": f"Visual quality assessment based on the game's release year and technical capabilities."
        },
        "microtransactions_score": {
            "short": "Monetization model assessment",
            "detailed": "Evaluation of the game's pricing strategy and additional content monetization."
        },
        "game_mechanics_score": {
            "short": f"User rating: {rating}/5 stars",
            "detailed": f"Gameplay quality based on user feedback and community ratings."
        },
        "completeness_score": {
            "short": f"Content length: {playtime} hours",
            "detailed": f"Assessment of game length and content completeness."
        },
        "story_quality_score": {
            "short": "Narrative quality assessment",
            "detailed": "Story and character development evaluation."
        },
        "accessibility_score": {
            "short": "Accessibility features",
            "detailed": "Evaluation of accessibility options and inclusive design."
        },
        "overall_score": {
            "short": f"Overall assessment: {round(overall_score, 1)}/100",
            "detailed": f"Comprehensive evaluation combining all quality metrics."
        }
    }

@app.get("/api/games/search", response_model=List[Game])
async def search_games(q: str = "", gen: Optional[int] = None):
    print(f"Search request: q='{q}', gen={gen}")

    # Return mock data for testing
    mock_games = [
        Game(id=1, title="God of War (2018)", generation=8, platform="PlayStation", rawg_id=58175),
        Game(id=2, title="God of War Ragnarök", generation=9, platform="PlayStation", rawg_id=494384),
        Game(id=3, title="God of War I", generation=6, platform="PlayStation", rawg_id=29179),
        Game(id=4, title="FIFA 23", generation=9, platform="Multi-platform", rawg_id=969052),
        Game(id=5, title="FIFA 22", generation=9, platform="Multi-platform", rawg_id=546464)
    ]

    if q.lower().startswith("god"):
        filtered_games = [g for g in mock_games if "god" in g.title.lower()]
    elif q.lower().startswith("fifa"):
        filtered_games = [g for g in mock_games if "fifa" in g.title.lower()]
    else:
        filtered_games = mock_games[:3]

    print(f"Returning {len(filtered_games)} mock games")
    return filtered_games

@app.post("/api/games/{game_id}/scan")
async def scan_game(game_id: int):
    print(f"Scan request for game ID: {game_id}")
    
    # Mock game data for scanning
    mock_game_data = {
        1: {  # God of War (2018)
            "metacritic": 94,
            "rating": 4.6,
            "released": "2018-04-20",
            "playtime": 12,
            "genres": [{"name": "Action"}, {"name": "Adventure"}],
            "esrb_rating": {"name": "M"}
        },
        2: {  # God of War Ragnarök
            "metacritic": 94,
            "rating": 4.7,
            "released": "2022-11-09",
            "playtime": 15,
            "genres": [{"name": "Action"}, {"name": "Adventure"}],
            "esrb_rating": {"name": "M"}
        },
        3: {  # God of War I
            "metacritic": 93,
            "rating": 4.5,
            "released": "2005-03-22",
            "playtime": 10,
            "genres": [{"name": "Action"}, {"name": "Adventure"}],
            "esrb_rating": {"name": "M"}
        },
        4: {  # FIFA 23
            "metacritic": 77,
            "rating": 3.8,
            "released": "2022-09-30",
            "playtime": 8,
            "genres": [{"name": "Sports"}],
            "esrb_rating": {"name": "E"}
        },
        5: {  # FIFA 22
            "metacritic": 76,
            "rating": 3.7,
            "released": "2021-10-01",
            "playtime": 8,
            "genres": [{"name": "Sports"}],
            "esrb_rating": {"name": "E"}
        }
    }
    
    if game_id not in mock_game_data:
        return {"error": f"Game with ID {game_id} not found"}
    
    game_data = mock_game_data[game_id]
    
    # Generate mock scores based on the game data
    metacritic = game_data["metacritic"]
    rating = game_data["rating"]
    release_year = int(game_data["released"][:4])
    playtime = game_data["playtime"]
    genres = game_data["genres"]
    
    # Calculate scores
    reviews_score = min(100, max(0, metacritic))
    graphics_base = min(100, 60 + (release_year - 2010) * 2)
    graphic_score = min(100, graphics_base + (metacritic - 70) * 0.3)
    microtransactions_score = 85
    game_mechanics_score = min(100, max(0, (rating * 20) + (metacritic * 0.3)))
    
    completeness_score = 80
    if playtime > 20:
        completeness_score = 90
    elif playtime > 10:
        completeness_score = 85
    else:
        completeness_score = 75
    
    genre_names = [g["name"].lower() for g in genres]
    story_score = 75
    if "rpg" in genre_names or "adventure" in genre_names:
        story_score = min(100, metacritic + 5)
    elif "action" in genre_names:
        story_score = min(100, metacritic - 5)
    
    accessibility_score = 75 if game_data.get("esrb_rating") else 70
    
    overall_score = (
        reviews_score * 0.25 +
        graphic_score * 0.15 +
        microtransactions_score * 0.10 +
        game_mechanics_score * 0.20 +
        completeness_score * 0.15 +
        story_score * 0.10 +
        accessibility_score * 0.05
    )
    
    scores = {
        "reviews_score": round(reviews_score, 1),
        "graphic_score": round(graphic_score, 1),
        "microtransactions_score": round(microtransactions_score, 1),
        "game_mechanics_score": round(game_mechanics_score, 1),
        "completeness_score": round(completeness_score, 1),
        "story_quality_score": round(story_score, 1),
        "accessibility_score": round(accessibility_score, 1),
        "overall_score": round(overall_score, 1),
        "reasoning": get_detailed_reasoning(game_id, game_data, reviews_score, graphic_score, game_mechanics_score, completeness_score, story_score, accessibility_score, overall_score)
    }
    
    print(f"Returning scores for game ID {game_id}: {scores['overall_score']}/100")
    return {"status": "completed", "scores": scores}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)