# Contributing & Branching Strategy

We keep `Develop` always green and functional. All work merges via Pull Request.

## Branches
- main: protected; release-only (tags). Do not push directly.
- Develop: default working branch; must always build, analyze, and pass tests.
- feature/<slug>: new features
- fix/<slug>: bug fixes
- chore/<slug>: maintenance, docs, CI

## PR Requirements
- Small, focused PRs.
- `flutter analyze` passes.
- Tests added/updated for new behavior.
- No sensitive terms in code or commit messages (enforced by hooks).

## CI
- GitHub Actions run on PRs to Develop: analyze, tests, and debug builds on iOS/Android.

## Releases
- Use PR from Develop → main, then tag (e.g., v0.1.0). Changelogs in PR description.
