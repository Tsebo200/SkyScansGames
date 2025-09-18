# Tasks: SkyScansGames

**Input**: Design documents from `/specs/001-skyscansgames-an-ai/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack (Python + React), libraries (FastAPI, React), structure (backend/, frontend/)
2. Load optional design documents:
   → data-model.md: Extract entities (Game, ScoreMetrics, User) → model tasks
   → contracts/: api.yaml → contract test tasks
   → research.md: Extract decisions (AI with Hugging Face, caching) → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, endpoints
   → Integration: DB, API mocks, caching
   → Polish: frontend components, styling, tests
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests? Yes
   → All entities have models? Yes
   → All endpoints implemented? Yes
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- Adjust based on plan.md structure

## Phase 3.1: Setup
- [ ] T001 Create backend/ and frontend/ directories per plan.md
- [ ] T002 Initialize Python project in backend/ with FastAPI dependencies
- [ ] T003 Initialize React project in frontend/
- [ ] T004 [P] Configure linting (black for Python, eslint for JS)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T005 [P] Contract test GET /games/search in backend/tests/contract/test_search.py
- [ ] T006 [P] Contract test POST /games/{id}/scan in backend/tests/contract/test_scan.py
- [ ] T007 [P] Contract test GET /games/{id}/scores in backend/tests/contract/test_scores.py
- [ ] T008 [P] Integration test search and scan flow in backend/tests/integration/test_scan_flow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T009 [P] Game model in backend/src/models/game.py
- [ ] T010 [P] ScoreMetrics model in backend/src/models/score_metrics.py
- [ ] T011 [P] User model in backend/src/models/user.py
- [ ] T012 [P] GameService in backend/src/services/game_service.py
- [ ] T013 [P] ScoringService (AI mock) in backend/src/services/scoring_service.py
- [ ] T014 GET /games/search endpoint in backend/src/api/search.py
- [ ] T015 POST /games/{id}/scan endpoint in backend/src/api/scan.py
- [ ] T016 GET /games/{id}/scores endpoint in backend/src/api/scores.py
- [ ] T017 Input validation in backend/src/validation.py
- [ ] T018 Error handling in backend/src/errors.py

## Phase 3.4: Integration
- [ ] T019 Connect to SQLite DB in backend/src/database.py
- [ ] T020 Mock API integrations (RAWG, Steam) in backend/src/services/api_service.py
- [ ] T021 Implement caching with cachetools in backend/src/cache.py
- [ ] T022 CORS middleware in backend/src/middleware.py

## Phase 3.5: Polish
- [ ] T023 [P] Frontend search component in frontend/src/components/SearchBar.js
- [ ] T024 [P] Frontend score display in frontend/src/components/ScoreDashboard.js
- [ ] T025 [P] Glassmorphism CSS in frontend/src/styles/glassmorphism.css
- [ ] T026 [P] Light/dark mode toggle in frontend/src/components/ThemeToggle.js
- [ ] T027 [P] Unit tests for scoring in backend/tests/unit/test_scoring.py
- [ ] T028 Performance optimization (<2s scan)
- [ ] T029 [P] Update README.md with usage
- [ ] T030 Run quickstart.md scenarios

## Dependencies
- Tests (T005-T008) before implementation (T009-T018)
- T009-T011 blocks T012-T013
- T012-T013 blocks T014-T016
- T019 blocks T020-T022
- Implementation before polish (T023-T030)

## Parallel Example
```
# Launch T005-T008 together:
Task: "Contract test GET /games/search in backend/tests/contract/test_search.py"
Task: "Contract test POST /games/{id}/scan in backend/tests/contract/test_scan.py"
Task: "Contract test GET /games/{id}/scores in backend/tests/contract/test_scores.py"
Task: "Integration test search and scan flow in backend/tests/integration/test_scan_flow.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- For MVP: Use mocks for AI and APIs initially
- Focus on local testing in browser

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task