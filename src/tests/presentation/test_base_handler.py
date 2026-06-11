"""
Tests for BaseRouteHandler.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status

from src.app.shared.presentation.base_handler import BaseRouteHandler, ExceptionMapping


class CustomDomainError(Exception):
    """Test domain exception."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class CustomValidationError(Exception):
    """Test validation exception."""


class TestExceptionMapping:
    """Test ExceptionMapping configuration."""

    def test_exception_mapping_creation(self):
        """Test creating exception mapping."""
        mapping = ExceptionMapping(
            exception_type=ValueError,
            status_code=400,
            detail="Invalid value",
        )

        assert mapping.exception_type is ValueError
        assert mapping.status_code == 400
        assert mapping.detail == "Invalid value"
        assert mapping.extract_message is True


class TestBaseRouteHandler:
    """Test suite for BaseRouteHandler."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful use case execution."""
        mock_use_case = AsyncMock(return_value={"id": "123", "name": "Test"})

        result = await BaseRouteHandler.execute(
            mock_use_case,
            id="123",
        )

        assert result == {"id": "123", "name": "Test"}
        mock_use_case.assert_called_once_with(id="123")

    @pytest.mark.asyncio
    async def test_execute_with_mapped_exception(self):
        """Test exception mapping to specific HTTP status."""
        mock_use_case = AsyncMock(side_effect=CustomDomainError("Resource not found"))

        exception_mappings = [
            ExceptionMapping(CustomDomainError, status.HTTP_404_NOT_FOUND),
        ]

        with pytest.raises(HTTPException) as exc_info:
            await BaseRouteHandler.execute(
                mock_use_case,
                exception_mappings=exception_mappings,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Resource not found"

    @pytest.mark.asyncio
    async def test_execute_with_custom_detail_message(self):
        """Test exception mapping with custom error message."""
        mock_use_case = AsyncMock(side_effect=CustomValidationError("Field invalid"))

        exception_mappings = [
            ExceptionMapping(
                CustomValidationError,
                status.HTTP_400_BAD_REQUEST,
                detail="Validation failed",
            ),
        ]

        with pytest.raises(HTTPException) as exc_info:
            await BaseRouteHandler.execute(
                mock_use_case,
                exception_mappings=exception_mappings,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Validation failed"

    @pytest.mark.asyncio
    async def test_execute_with_unhandled_exception(self):
        """Test unhandled exception returns 500."""
        mock_use_case = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        with pytest.raises(HTTPException) as exc_info:
            await BaseRouteHandler.execute(mock_use_case)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"

    @pytest.mark.asyncio
    async def test_execute_with_multiple_exception_mappings(self):
        """Test multiple exception mappings."""
        mock_use_case = AsyncMock(side_effect=ValueError("Invalid input"))

        exception_mappings = [
            ExceptionMapping(CustomDomainError, 404),
            ExceptionMapping(ValueError, 400),
            ExceptionMapping(KeyError, 422),
        ]

        with pytest.raises(HTTPException) as exc_info:
            await BaseRouteHandler.execute(
                mock_use_case,
                exception_mappings=exception_mappings,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid input"

    @pytest.mark.asyncio
    async def test_execute_with_payload_extraction_success(self):
        """Test successful execution with user ID extraction."""
        mock_use_case = AsyncMock(return_value={"id": "123", "created_by": "user-456"})

        current_user = {"sub": "user-456", "email": "test@example.com"}

        async def execute_fn(user_id):
            return await mock_use_case(
                name="Test Project",
                description="Test",
                created_by=user_id,
            )

        result = await BaseRouteHandler.execute_with_payload_extraction(
            execute_fn=execute_fn,
            current_user=current_user,
        )

        assert result == {"id": "123", "created_by": "user-456"}
        mock_use_case.assert_called_once_with(
            name="Test Project",
            description="Test",
            created_by="user-456",
        )

    @pytest.mark.asyncio
    async def test_execute_with_payload_extraction_missing_sub(self):
        """Test execution fails when JWT token missing 'sub' claim."""
        mock_use_case = AsyncMock()

        current_user = {"email": "test@example.com"}  # Missing 'sub'

        async def execute_fn(user_id):
            return await mock_use_case(created_by=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await BaseRouteHandler.execute_with_payload_extraction(
                execute_fn=execute_fn,
                current_user=current_user,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token payload"

    @pytest.mark.asyncio
    async def test_execute_with_custom_lambda(self):
        """Test execution with custom lambda function."""
        mock_use_case = AsyncMock(return_value={"success": True})

        current_user = {"sub": "user-123"}

        async def execute_fn(user_id):
            return await mock_use_case(
                name="Test",
                description="Description",
                created_by=user_id,
            )

        result = await BaseRouteHandler.execute_with_payload_extraction(
            execute_fn=execute_fn,
            current_user=current_user,
        )

        assert result == {"success": True}
        mock_use_case.assert_called_once_with(
            name="Test",
            description="Description",
            created_by="user-123",
        )
