# Conventional Commits Reference

> Based on Conventional Commits v1.0.0 (https://www.conventionalcommits.org/)

## Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

| Type | Description | Example |
| --- | --- | --- |
| `feat` | New feature | `feat: add user registration` |
| `fix` | Bug fix | `fix: resolve login redirect loop` |
| `docs` | Documentation only | `docs: update API usage guide` |
| `style` | Code style (formatting, semicolons, etc.) | `style: fix indentation in auth module` |
| `refactor` | Code change that neither fixes a bug nor adds a feature | `refactor: extract validation logic into helper` |
| `perf` | Performance improvement | `perf: cache database query results` |
| `test` | Adding or updating tests | `test: add unit tests for payment service` |
| `build` | Build system or external dependencies | `build: upgrade TypeScript to v5.4` |
| `ci` | CI/CD configuration | `ci: add GitHub Actions workflow for staging` |
| `chore` | Maintenance tasks (deps, configs, tooling) | `chore: update .gitignore` |
| `revert` | Reverts a previous commit | `revert: revert feat: add user registration` |

## Scope

Optional. Describes the section of the codebase affected. Enclosed in parentheses after the type.

```
feat(auth): add OAuth2 login
fix(api): handle null response from payment gateway
docs(readme): add setup instructions
```

Common scope examples: `auth`, `api`, `ui`, `db`, `config`, `deps`, module or feature names.

## Description

- Imperative mood, present tense: "add" not "added" or "adds"
- Lowercase first letter
- No period at the end
- Keep under 72 characters

## Body

- Separated from description by a blank line
- Explain **what** and **why**, not how
- Wrap at 72 characters per line
- Use when the description alone is insufficient

```
fix(auth): prevent session fixation on login

The session ID was not being regenerated after successful
authentication, allowing an attacker to fixate a session.
Regenerate session ID immediately after credential validation.
```

## Breaking Changes

Indicated by `!` after the type/scope, or by a `BREAKING CHANGE:` footer.

```
feat(api)!: change authentication endpoint response format

BREAKING CHANGE: /api/auth/login now returns { token, user }
instead of { accessToken, refreshToken, userData }.
```

## Multiple Changes

If a single commit covers multiple concerns, use the most significant type. If changes are truly independent, split into separate commits.

## Choosing the Right Type

- Added a new endpoint or UI feature? → `feat`
- Fixed something that was broken? → `fix`
- Renamed variables, moved files, restructured without behavior change? → `refactor`
- Updated package versions? → `build` (if it affects build) or `chore`
- Changed only comments, README, or docs? → `docs`
- Added or modified test files only? → `test`
- Improved speed or resource usage? → `perf`
