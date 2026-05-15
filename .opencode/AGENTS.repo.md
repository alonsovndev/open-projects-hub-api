# Repository Agent Instructions

This file contains repository-specific rules and preferences.

## Scope

- Apply only to this repository.
- Do not duplicate global rules from ${HOME}/.config/opencode.

## What to Define Here

1. Domain boundaries and terminology for this repo
2. Build, test, and lint commands
3. Security and data constraints unique to this repo
4. Performance and reliability goals
5. Any local conventions not already covered globally

## Token Discipline

- Keep this file short.
- Link to local docs instead of copying large guides.
- Add only rules that are specific to this repository.

## Code Style and Naming Conventions

### Self-Documenting Code

- Use descriptive, meaningful variable names that clearly indicate their purpose
- Avoid single-letter or abbreviated variable names except in very limited contexts:
  - Loop counters in simple iterations (e.g., `i`, `j`)
  - Mathematical formulas where convention dictates (e.g., `x`, `y`)
- **Never use generic names like `v`, `val`, `tmp`, `data` without additional context**
- Examples:
  - ❌ `v: str` → ✅ `theme_value: str`
  - ❌ `val: int` → ✅ `user_count: int`
  - ❌ `tmp: dict` → ✅ `preferences_dict: dict`
  - ❌ `data: list` → ✅ `project_items: list`

### Comments

- **Do not add obvious comments** that merely restate what the code does
- Comments should explain **WHY**, not **WHAT**
- Good comments explain:
  - Business logic rationale
  - Non-obvious algorithmic choices
  - Workarounds for external constraints
  - Important warnings or gotchas
- Examples:
  - ❌ `# Set theme to light` (obvious)
  - ❌ `# Loop through users` (obvious)
  - ❌ `# Return the result` (obvious)
  - ✅ `# Using bcrypt rounds=12 per security team requirement (2024-05)`
  - ✅ `# Cache for 5min to avoid rate limiting from external API`
  - ✅ `# HACK: API returns null instead of empty array, normalizing here`
