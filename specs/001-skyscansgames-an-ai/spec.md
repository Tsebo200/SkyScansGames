# Feature Specification: SkyScansGames: An AI Driven game scanner for quality check

**Feature Branch**: `001-skyscansgames-an-ai`  
**Created**: 18 September 2025  
**Status**: Draft  
**Input**: User description: "SkyScansGames: An AI Driven game scanner for quality check", The scanner should detect and calculate while giving a score based on metrics such as: 

THE GAMES RATING:
Fan Reviews and Professional Reviewers (Twitch feedback and IGN Reviewers).
Graphic Quality (what graphics technology is being used (RayTracing or HDR or CGI, .etc).
Microtransactions (battle passes, loot boxes, skins).
Add-on Costs (DLCs or anything that contributes to a better game extension experience that is being charged).
Game Mechanics Score (how well they work, and how intuitive it is).
Completeness (based on demo gameplay/trailer vs actual game on launch).
Story Quality Score (how unique is the concept that may reflect on current struggles in society).
Accessibility Score (based on Can I play (https://caniplaythat.com/)).
Detect The Game Engine and version of it in use (Unreal Engine, Unity).
Database Longevity Score (Is the database decentralised or decentralisable?).

I want it to return stats and give overal score of game based on these:
Reviews Score, Graphic Quality Score, Microtransactions Score, Game Mechanics Score, Completeness Score, Story Quality Score, Accessibility Score.

Scoring should be with percentages please and I want it display: Reviews Score, Graphic Quality Score, Microtransactions Score, Game Mechanics Score, Completeness Score, Story Quality Score, Accessibility Score. All in separate containers in the dashboard

I am thinking about using APIs like:
TwitchAPI, RAWGAPI, Steam API, OpenCritic API. In order to feed and train the model.

I want it to have a search bar to search for game titles all from Generation 7 until Genration 9 of games (Console and PC)
I would like to output this on a dashbaord that meet WCAG AA contrast. I want the dashboard to follow the glassmorphism/liquid glass design trend with light mode and dark mode switch in settings but I want it to still be accessible so please follow the WCAG AA contrast guide

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a gamer or game enthusiast, I want to search for a specific game title from console and PC generations 7-9, scan its quality using AI-driven metrics, and view a comprehensive score breakdown on an accessible dashboard so that I can make informed decisions about purchasing or playing the game.

### Acceptance Scenarios
1. **Given** a valid game title from generations 7-9 is entered in the search bar, **When** the scan is initiated, **Then** the system displays individual scores for Reviews, Graphic Quality, Microtransactions, Game Mechanics, Completeness, Story Quality, and Accessibility in separate containers, along with an overall score.
2. **Given** the dashboard is loaded, **When** the user toggles between light and dark mode, **Then** the interface maintains WCAG AA contrast compliance while following glassmorphism design trends.
3. **Given** a game is scanned, **When** the system detects the game engine and database longevity, **Then** this information is included in the output stats.

### Edge Cases
- What happens when the searched game title is not found in the database?
- How does the system handle games with incomplete data from APIs?
- What if the accessibility score cannot be determined due to lack of data from Can I Play?
- How are scores calculated when some metrics are unavailable? Follow the metrics but be fair and realistic and if in doubt check the reviews

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST allow users to search for game titles from console and PC generations 7-9 via a search bar.
- **FR-002**: System MUST detect and calculate a Reviews Score based on fan reviews and professional reviewers (e.g., Twitch feedback and IGN reviewers).
- **FR-003**: System MUST evaluate and score Graphic Quality based on technologies used (e.g., RayTracing, HDR, CGI).
- **FR-004**: System MUST assess and score Microtransactions including battle passes, loot boxes, and skins. Start with a tick and cross method (Yes / No)
- **FR-005**: System MUST evaluate Add-on Costs for DLCs and other charged extensions.
- **FR-006**: System MUST calculate a Game Mechanics Score based on how well mechanics work and their intuitiveness.
- **FR-007**: System MUST determine a Completeness Score by comparing demo/trailer gameplay to the actual launched game.
- **FR-008**: System MUST assess Story Quality Score based on uniqueness and reflection of societal struggles.
- **FR-009**: System MUST provide an Accessibility Score based on data from Can I Play (https://caniplaythat.com/).
- **FR-010**: System MUST detect the Game Engine and its version in use (e.g., Unreal Engine, Unity).
- **FR-011**: System MUST calculate a Database Longevity Score based on whether the database is decentralized or decentralizable.
- **FR-012**: System MUST return individual scores for Reviews, Graphic Quality, Microtransactions, Game Mechanics, Completeness, Story Quality, and Accessibility as percentages.
- **FR-013**: System MUST display all scores in separate containers on the dashboard.
- **FR-014**: System MUST provide an overall score based on the individual metrics.
- **FR-015**: System MUST output results on a dashboard that meets WCAG AA contrast guidelines.
- **FR-016**: System MUST follow glassmorphism/liquid glass design trends on the dashboard.
- **FR-017**: System MUST include a light mode and dark mode switch in settings, ensuring accessibility.
- **FR-018**: System MUST use APIs such as TwitchAPI, RAWGAPI, Steam API, and OpenCritic API to feed and train the AI model [NEEDS CLARIFICATION: How will these APIs be integrated without specifying implementation details?].

### Key Entities *(include if feature involves data)*
- **Game**: Represents a video game with attributes like title, generation, platform (console/PC), and associated metrics.
- **Score Metrics**: Includes individual scores (Reviews, Graphic Quality, etc.) and overall score, linked to a specific game.
- **User**: The person interacting with the scanner, with preferences for dashboard mode.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---
