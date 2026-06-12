"""Domain exceptions for stories feature."""


class StoryNotFoundError(Exception):
    """Raised when a story cannot be found."""

    def __init__(self, story_id: str):
        self.story_id = story_id
        super().__init__(f"Story not found: {story_id}")
