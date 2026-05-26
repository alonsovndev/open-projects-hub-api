# ADR-003: DTO-Based Use Cases

**Status**: Accepted  
**Date**: 2026-05-21  
**Decision Makers**: Solo developer  
**Affected Components**: `src/app/features/*/application/use_cases/`, `src/app/features/*/application/dtos/`

---

## Context

Use cases were accepting many individual parameters (5+), leading to:

- Long method signatures that are hard to read and maintain
- Route handlers that manually unpack DTOs into individual parameters
- Inconsistent parameter ordering across use cases
- Difficulty adding new optional parameters without breaking signatures

### Example of the Problem

```python
# Use case with too many parameters
async def execute(
    self,
    name: str,
    code: str,
    client_id: str,
    description: str,
    status: str,
    start_date: datetime,
    created_by: str,
) -> ProjectResponse:
    pass

# Route handler manually unpacking
await use_case.execute(
    name=payload.name,
    code=payload.code,
    client_id=payload.client_id,
    description=payload.description,
    status=payload.status,
    start_date=payload.start_date,
    created_by=user_id,
)
```

---

## Decision

**Use cases accept DTOs as input (Command Pattern) with a maximum of 2-3 parameters.**

Specifically:
- Use case `execute()` methods accept a request DTO as the primary parameter
- Context parameters (e.g., `created_by` from JWT) are passed separately
- Maximum 2-3 parameters per use case method: `request` + context
- Route handlers pass DTOs directly without unpacking
- DTOs use `ConfigDict(alias_generator=to_camel)` for camelCase JSON

### Implementation

```python
# Use case accepts DTO
class CreateProjectUseCase:
    async def execute(
        self,
        request: CreateProjectRequest,
        created_by: str,
    ) -> ProjectResponse:
        pass

# Route handler passes DTO directly
@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    payload: CreateProjectRequest,
    current_user: Dict[str, Any] = Depends(require_admin),
    use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
) -> ProjectResponse:
    return await handler.execute_with_payload_extraction(
        execute_fn=lambda user_id: use_case.execute(request=payload, created_by=user_id),
        current_user=current_user,
    )
```

### DTO Definition

```python
class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str
    code: str
    client_id: str
    description: Optional[str] = None
    status: str = "active"
```

---

## Consequences

### Positive

✅ **Cleaner signatures**: Max 2-3 parameters, easy to read  
✅ **No unpacking**: Route handlers pass DTOs directly  
✅ **Easier testing**: Test fixtures create DTOs instead of many kwargs  
✅ **Consistent API**: All use cases follow the same pattern  
✅ **Easy extension**: Add fields to DTO without changing use case signature  
✅ **camelCase JSON**: Consistent API contract via alias generator  

### Negative

⚠️ **DTO proliferation**: Each operation may need its own request DTO  
⚠️ **Indirection**: One more layer between route and use case logic  

### Accepted Trade-offs

- **DTO count** → **Clean use case signatures**
- **One more type** → **No manual parameter unpacking**

---

## Alternatives Considered

### Option A: Individual Parameters (PREVIOUS)
- **Effort**: Already existed
- **Readability**: Poor (5+ parameters)
- **Best for**: Simple operations with 1-2 parameters

### Option B: Keyword Arguments (**kwargs)
- **Effort**: Minimal
- **Readability**: Poor (no type hints, IDE support lost)
- **Best for**: Dynamic/unknown parameter sets

### Option C: Builder Pattern
- **Effort**: 4-6 hours
- **Readability**: Good but verbose for simple operations
- **Best for**: Complex objects with many optional fields

### Option D: DTO-Based Command Pattern (CHOSEN)
- **Effort**: Already implemented
- **Readability**: Excellent (typed, self-documenting)
- **Best for**: REST APIs with structured request bodies

---

## When to Revisit

Reconsider this decision if:

1. **Simple queries**: Read-only use cases with 1-2 parameters may not need DTOs
2. **Performance critical**: DTO creation overhead becomes measurable (unlikely)
3. **Dynamic payloads**: Endpoints accept arbitrary/unknown fields

---

## References

- Command Pattern: GoF Design Patterns
- Clean Architecture: Use cases are application layer, DTOs are the interface
- Related code: `src/app/features/*/application/dtos/`
- Route patterns: `src/app/features/*/presentation/routes/`

---

## Notes

This pattern aligns with REST best practices:
- Request bodies map to DTOs
- DTOs define the API contract
- Use cases implement business logic
- Routes orchestrate the flow
