"""Per-workspace caps on users and on free AI credits."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceLimits:
    max_users: int
    ai_credits_ceiling: int
    credits_per_user: int
