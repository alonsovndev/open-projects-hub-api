# ADR-001: Cross-Feature Queries for Performance Optimization

**Status**: Accepted  
**Date**: 2026-05-21  
**Decision Makers**: Solo developer  
**Affected Components**: `src/app/features/projects/infrastructure/repositories/`

---

## Context

The Projects feature needs to display story count metrics (total stories and completed stories) for each project. This requires aggregating data from the Stories feature's database table.

### Clean Architecture Constraint

In strict clean architecture, features should be loosely coupled:
- Each feature should only query its own tables
- Cross-feature data access should go through application layer contracts or events
- Infrastructure layer should not directly import models from other features

### Performance Requirement

The story counts are displayed in:
1. Project list endpoints (batch query for multiple projects)
2. Project detail endpoints (single project query)

For optimal performance, these counts should be fetched with:
- Single SQL queries with aggregation
- Minimal round trips to the database
- No N+1 query problems

---

## Decision

**We accept pragmatic cross-feature coupling at the infrastructure layer for performance-critical queries.**

Specifically:
- `ProjectRepositoryImpl` directly queries `StoryModel` from the Stories feature
- Uses efficient SQL aggregations (`COUNT`, `SUM(CASE)`)
- Implements both single (`get_story_counts`) and batch (`get_story_counts_batch`) methods
- Uses domain value objects (`StoryStatus.DONE.value`) instead of hardcoded strings

### Implementation

```python
# src/app/features/projects/infrastructure/repositories/project_repository_impl.py

from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.features.stories.domain.value_objects.story_status import StoryStatus

async def get_story_counts(self, project_id: UUID) -> Tuple[int, int]:
    stmt = select(
        func.count(StoryModel.id).label('total'),
        func.sum(case((StoryModel.status == StoryStatus.DONE.value, 1), else_=0)).label('completed')
    ).where(StoryModel.project_id == project_id)
    # ...
```

---

## Consequences

### Positive

✅ **Performance**: Single optimized SQL query instead of multiple round trips  
✅ **Simplicity**: No complex coordination layer needed  
✅ **Maintainability**: One developer can easily manage this coupling  
✅ **Monolith-friendly**: Features deploy together, coupling is not a deployment risk  
✅ **Type-safe**: Uses domain enums (`StoryStatus.DONE`) instead of magic strings  

### Negative

⚠️ **Feature coupling**: Projects infrastructure depends on Stories infrastructure  
⚠️ **Migration coordination**: Schema changes to Stories may require Projects updates  
⚠️ **Testing complexity**: Projects tests need Stories database setup  

### Accepted Trade-offs

- **Clean architecture purity** → **Query performance and simplicity**
- **Perfect decoupling** → **Pragmatic monolithic design**

---

## Alternatives Considered

### Option A: Accept Coupling (CHOSEN)
- **Effort**: Already implemented
- **Performance**: ⭐⭐⭐⭐⭐ (optimal)
- **Complexity**: ⭐ (minimal)
- **Best for**: Monolithic deployment, small teams

### Option B: Shared Query Service
- **Effort**: 2-3 hours
- **Performance**: ⭐⭐⭐⭐ (good)
- **Complexity**: ⭐⭐⭐ (moderate)
- **Best for**: Future microservices preparation

### Option C: Repository Bridge Pattern
- **Effort**: 1-2 hours
- **Performance**: ⭐⭐⭐⭐ (good)
- **Complexity**: ⭐⭐ (low-moderate)
- **Best for**: Middle ground between A and B

### Option D: Event-Driven with Materialized View
- **Effort**: 8+ hours
- **Performance**: ⭐⭐⭐⭐⭐ (optimal)
- **Complexity**: ⭐⭐⭐⭐⭐ (high)
- **Best for**: High-scale microservices

---

## When to Revisit

Reconsider this decision if:

1. **Team growth**: Team grows to 3+ developers working on separate features
2. **Microservices**: Planning to split into independently deployable services
3. **Feature velocity**: Cross-feature changes become deployment bottleneck
4. **Scale requirements**: Need event-driven architecture for performance

---

## References

- Clean Architecture (Robert C. Martin) - Chapter 22: The Clean Architecture
- Pragmatic Programmer (Hunt & Thomas) - "Good Enough Software"
- Repository pattern: `/docs/engineering/clean-architecture.md`
- Related code: `/src/app/features/projects/infrastructure/repositories/project_repository_impl.py`

---

## Notes

This decision prioritizes **shipping working software** over architectural purity. The coupling is:
- Documented and intentional
- Isolated to infrastructure layer
- Reversible when needed
- Appropriate for current deployment model

**Architecture score impact**: 9.0/10 (excellent for monolithic deployment)
