# Data Model: SkyScansGames

## Entity: Game
- **id**: Integer (primary key)
- **title**: String (required, unique)
- **generation**: Integer (7-9, required)
- **platform**: String (console/pc, required)
- **engine**: String (optional, detected)
- **release_date**: Date (optional)
- **description**: Text (optional)
- **Relationships**: One-to-one with ScoreMetrics

## Entity: ScoreMetrics
- **id**: Integer (primary key)
- **game_id**: Integer (foreign key to Game)
- **reviews_score**: Float (0-100, percentage)
- **graphic_score**: Float (0-100)
- **microtransactions_score**: Float (0-100)
- **game_mechanics_score**: Float (0-100)
- **completeness_score**: Float (0-100)
- **story_quality_score**: Float (0-100)
- **accessibility_score**: Float (0-100)
- **overall_score**: Float (0-100, calculated)
- **database_longevity_score**: Float (0-100, optional)
- **Relationships**: One-to-one with Game

## Entity: User
- **id**: Integer (primary key)
- **theme_preference**: String (light/dark, default light)
- **Relationships**: None (single user assumed)

## Validation Rules
- Game title: Non-empty, max 255 chars
- Scores: 0-100, nullable if not available
- Generation: 7,8,9 only
- Platform: 'console' or 'pc'

## State Transitions
- Game: Created → Scanned (scores added)
- Scores: None → Partial → Complete (all scores calculated)