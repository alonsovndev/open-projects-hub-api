# Architectural Decision Records (ADR)

This directory contains records of architectural decisions made in the Open Projects Hub API.

## What is an ADR?

An Architectural Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## Format

Each ADR includes:
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Date**: When the decision was made
- **Context**: What circumstances led to this decision
- **Decision**: What was decided
- **Consequences**: What are the positive and negative outcomes
- **Alternatives**: What other options were considered

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./ADR-001-cross-feature-queries-for-performance.md) | Cross-Feature Queries for Performance Optimization | Accepted | 2026-05-21 |
| [ADR-002](./ADR-002-centralized-validation-pattern.md) | Centralized Validation Pattern | Accepted | 2026-05-21 |
| [ADR-003](./ADR-003-dto-based-use-cases.md) | DTO-Based Use Cases (Command Pattern) | Accepted | 2026-05-21 |
| [ADR-004](./ADR-004-dependency-inversion-for-repositories.md) | Dependency Inversion for Repositories | Accepted | 2026-05-21 |

## How to Create an ADR

1. Copy the template from an existing ADR
2. Number it sequentially (ADR-XXX)
3. Use kebab-case for filename: `ADR-XXX-short-descriptive-title.md`
4. Update the index table above
5. Commit with message: `docs: add ADR-XXX <title>`

## ADR Lifecycle

- **Proposed**: Under discussion, not yet implemented
- **Accepted**: Decision made and implemented
- **Deprecated**: No longer recommended, but not yet removed
- **Superseded**: Replaced by a newer ADR (link to replacement)

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
