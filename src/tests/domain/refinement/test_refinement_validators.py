"""Tests for RefinementValidators, focused on the documented note-length boundaries."""

import pytest

from src.app.features.refinement.domain.validators.refinement_validators import RefinementValidators
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError


class TestRawNotesLength:
    """FR-002-06 caps refinement input at 5000 characters."""

    def test_notes_at_the_cap_are_accepted(self):
        """Test that exactly 5000 characters passes."""
        RefinementValidators.validate_raw_notes("a" * RefinementValidators.MAX_NOTES_LENGTH)

    def test_notes_one_over_the_cap_are_rejected(self):
        """Test that 5001 characters is rejected with the limit named."""
        with pytest.raises(ValidationError, match="cannot exceed 5000 characters"):
            RefinementValidators.validate_raw_notes("a" * (RefinementValidators.MAX_NOTES_LENGTH + 1))

    def test_notes_at_the_minimum_are_accepted(self):
        """Test that exactly 20 characters passes."""
        RefinementValidators.validate_raw_notes("a" * RefinementValidators.MIN_NOTES_LENGTH)

    def test_notes_below_the_minimum_are_rejected(self):
        """Test that 19 characters is rejected."""
        with pytest.raises(ValidationError, match="at least 20 characters"):
            RefinementValidators.validate_raw_notes("a" * (RefinementValidators.MIN_NOTES_LENGTH - 1))

    def test_empty_notes_are_rejected(self):
        """Test that blank input is rejected before the length checks."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            RefinementValidators.validate_raw_notes("   ")
