# Research Findings: SkyScansGames

## Decision: Tech Stack
**Chosen**: Python 3.11 (backend) + React (frontend)  
**Rationale**: Free and open-source, easy to learn and use, accurate for data processing and AI integration. Python excels in AI/ML with libraries like scikit-learn and Hugging Face. React provides a robust SPA framework with good accessibility support.  
**Alternatives Considered**: 
- Node.js + Express: Considered for full JS stack, but Python better for AI.
- Vue.js: Lighter than React, but React has better ecosystem for complex UIs.
- Django: Full-featured, but FastAPI more modern for APIs.

## Decision: AI Model Implementation
**Chosen**: Hugging Face Transformers for NLP on reviews + scikit-learn for scoring aggregation  
**Rationale**: Free, easy to use, accurate for sentiment analysis on reviews and classification for other metrics. Hugging Face provides pre-trained models for text analysis. Scikit-learn for simple regression/classification on numerical data.  
**Alternatives Considered**: 
- TensorFlow/PyTorch: More powerful but complex for this scope.
- Custom ML models: Time-consuming, less accurate without large datasets.
- Rule-based scoring: Simpler but less accurate.

## Decision: API Integration
**Chosen**: Requests library with aiohttp for async calls, rate limiting via ratelimit library  
**Rationale**: Free, easy to use, accurate data fetching. Async for performance. Rate limiting to respect fair use.  
**Alternatives Considered**: 
- urllib: Built-in but less convenient.
- Scraping: Violates terms, less reliable.

## Decision: Caching Strategy
**Chosen**: In-memory caching with cachetools, Redis optional for persistence  
**Rationale**: Free, easy to implement, respects fair use by reducing API calls. Cachetools simple for Python.  
**Alternatives Considered**: 
- No caching: Would exceed API limits.
- File-based: Slower than memory.

## Decision: Debouncing for Search
**Chosen**: Lodash debounce in frontend  
**Rationale**: Free, easy to use, accurate for reducing API calls on search input.  
**Alternatives Considered**: 
- Custom debounce: Reinvent wheel.
- No debouncing: Too many requests.

## Decision: Glassmorphism Design
**Chosen**: CSS backdrop-filter with CSS custom properties for themes  
**Rationale**: Free, easy to implement, follows trends while ensuring WCAG AA contrast by using high contrast colors in themes.  
**Alternatives Considered**: 
- Images: Less accessible.
- Libraries like glassmorphism-css: Unnecessary overhead.

## Decision: Accessibility (WCAG AA)
**Chosen**: Semantic HTML, ARIA labels, color contrast tools  
**Rationale**: Ensures compliance, free tools available.  
**Alternatives Considered**: 
- Ignore: Violates requirements.
- Full audit: Overkill for initial.

## Decision: Database Longevity Score
**Chosen**: Rule-based on game metadata (e.g., if indie or AAA, decentralized if blockchain-based)  
**Rationale**: Simple, accurate enough for scoring.  
**Alternatives Considered**: 
- External data: Hard to find.

## Decision: Game Engine Detection
**Chosen**: Regex on game descriptions or API metadata  
**Rationale**: Free, easy, accurate for common engines.  
**Alternatives Considered**: 
- ML classification: Overkill.

## Summary
All NEEDS CLARIFICATION resolved. Tech choices prioritize free, easy, accurate tools. AI model uses existing libraries for reliability.