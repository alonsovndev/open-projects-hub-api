# ADR-002: Centralized Validation Pattern

**Status**: Accepted  
**Date**: 2026-05-21  
**Decision Makers**: Solo developer  
**Affected Components**: `src/app/features/*/domain/validators/`

---

## Context

Validation logic was scattered across multiple layers:
- Pydantic DTO field validators
- Entity method-level validation
- Use case inline validation
- Route handler pre-checks

This led to:
- Inconsistent validation across features
- Duplicate validation rules
- Difficulty testing validation in isolation
- Unclear ownership of validation rules

### Example of the Problem

```python
# Validation scattered in multiple places
class ProjectEntity:
    def _validate_name(self, name):  # Wrapper method (anti-pattern)
        if not name or len(name) > 100:
            raise ValueError("Invalid name")

class CreateProjectUseCase:
    async def execute(self, name, code, ...):
        if not code or len(code) > 20:  # Inline validation
            raise ValueError("Invalid code")
```

---

## Decision

**We centralize all domain validation in `FeatureValidators` classes within each feature's domain layer.**

Specifically:
- Each feature has a `FeatureValidators` class (e.g., `ProjectValidators`, `ClientValidators`)
- Validators are static methods: `FeatureValidators.validate_xxx(value)`
- Entities call validators directly (no wrapper methods)
- Use cases call validators for cross-field or business rule validation
- Pydantic DTOs handle structural validation (required fields, types); domain validators handle business rules

### Implementation

```python
# src/app/features/projects/domain/validators/project_validators.py

class ProjectValidators:
    @staticmethod
    def validate_name(name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Project name is required")
        if len(name) > 100:
            raise ValueError("Project name must be 100 characters or less")

    @staticmethod
    def validate_code(code: str) -> None:
        if not code or not code.strip():
            raise ValueError("Project code is required")
        if len(code) > 20:
            raise ValueError("Project code must be 20 characters or less")
```

```python
# Entity calls validator directly (no wrapper)
class ProjectEntity:
    def update_details(self, name: str) -> None:
        ProjectValidators.validate_name(name)  # Direct call
        self._name = name
```

---

## Consequences

### Positive

✅ **Single source of truth**: All validation rules in one place per feature  
✅ **Easier testing**: Validators can be unit tested in isolation  
✅ **Consistent behavior**: Same validation across DTOs, entities, and use cases  
✅ **No wrapper methods**: Eliminates unnecessary indirection  
✅ **Clear ownership**: Domain layer owns validation rules  

### Negative

⚠️ **Validator class size**: Features with many entities may have large validator classes  
⚠️ **Import coupling**: Entities must import their feature's validator class  

### Accepted Trade-offs

- **Validator class size** → **Single source of truth**
- **Import coupling** → **Clear validation ownership**

---

## Alternatives Considered

### Option A: Pydantic-Only Validation
- **Effort**: Minimal (already in DTOs)
- **Coverage**: Structural only, not business rules
- **Best for**: Simple CRUD APIs

### Option B: Entity-Only Validation
- **Effort**: Moderate
- **Coverage**: Good, but scattered across entity methods
- **Best for**: Small features with few entities

### Option C: Centralized Validators (CHOSEN)
- **Effort**: Already implemented
- **Coverage**: Complete (structural + business rules)
- **Best for**: Features with complex validation requirements

### Option D: Validation Service Layer
- **Effort**: 3-4 hours
- **Coverage**: Complete but over-engineered
- **Best for**: Microservices with shared validation

---

## When to Revisit

Reconsider this decision if:

1. **Shared validation rules**: Multiple features need the same validators (consider shared validators)
2. **Dynamic validation**: Validation rules become configuration-driven
3. **External validation**: Third-party services need to validate our domain objects

---

## References

- Clean Architecture: Domain layer owns business rules
- Related code: `src/app/features/*/domain/validators/`
- Anti-pattern avoided: Wrapper methods that only pass through to validators

---

## Notes

This pattern ensures validation is:
- **Discoverable**: All rules in `validators/` directory
- **Testable**: Static methods are easy to unit test
- **Consistent**: Same rules applied regardless of entry point
- **Maintainable**: Change rule in one place, affects all callers
