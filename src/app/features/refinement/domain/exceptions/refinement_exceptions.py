"""Refinement domain exceptions."""


class StoryDraftNotFoundError(Exception):
    """Raised when a story draft is not found."""

    def __init__(self, draft_id: str):
        self.draft_id = draft_id
        super().__init__(f"Story draft not found: {draft_id}")
