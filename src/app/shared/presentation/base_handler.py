"""
Base route handler for abstracting common concerns in route handlers.

Provides:
- Standardized exception handling
- Use case execution wrapper
- Consistent error responses
- Reduced boilerplate in route handlers
"""

from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import HTTPException, status

from src.app.shared.logging import get_logger


log = get_logger(__name__)


T = TypeVar("T")


class ExceptionMapping:
    """Maps exception types to HTTP status codes and error messages."""

    def __init__(
        self,
        exception_type: type[Exception],
        status_code: int,
        detail: str | None = None,
        extract_message: bool = True,
    ):
        """
        Args:
            exception_type: The exception class to catch
            status_code: HTTP status code to return
            detail: Optional custom error message (if None, uses exception message)
            extract_message: Whether to extract message from exception.message attribute
        """
        self.exception_type = exception_type
        self.status_code = status_code
        self.detail = detail
        self.extract_message = extract_message


class BaseRouteHandler:
    """
    Base handler for route operations with standardized error handling.

    Usage:
        handler = BaseRouteHandler()
        result = await handler.execute(
            use_case.execute,
            payload=request_data,
            exception_mappings=[
                ExceptionMapping(NotFoundError, 404),
                ExceptionMapping(ValidationError, 400),
            ]
        )
    """

    @staticmethod
    async def execute(
        use_case_method: Callable[..., Any],
        exception_mappings: list[ExceptionMapping] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a use case with standardized exception handling.

        Args:
            use_case_method: The use case method to execute (e.g., use_case.execute)
            exception_mappings: List of exception-to-HTTP-status mappings
            **kwargs: Arguments to pass to the use case method

        Returns:
            Result from the use case execution

        Raises:
            HTTPException: On any exception (mapped or generic 500)
        """
        try:
            result = await use_case_method(**kwargs)
            return result

        except HTTPException:
            # Re-raise HTTPException as-is (already formatted)
            raise

        except Exception as e:
            # Try to match specific exception mappings first
            if exception_mappings:
                for mapping in exception_mappings:
                    if isinstance(e, mapping.exception_type):
                        detail = mapping.detail

                        # Extract message from exception if configured
                        if detail is None:
                            if mapping.extract_message and hasattr(e, "message"):
                                detail = str(e.message)
                            else:
                                detail = str(e)

                        log.warning(f"Handled exception {mapping.exception_type.__name__}: {detail}")
                        raise HTTPException(
                            status_code=mapping.status_code,
                            detail=detail,
                        )

            # Generic 500 error for unhandled exceptions
            log.error(f"Unhandled exception in route handler: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @staticmethod
    async def execute_with_payload_extraction(
        execute_fn: Callable[..., Any],
        current_user: dict[str, Any],
        exception_mappings: list[ExceptionMapping] | None = None,
    ) -> Any:
        """
        Execute use case with automatic user ID extraction from current_user.

        Useful for endpoints that require authentication and need to pass user_id
        to the use case. Accepts a callable that takes user_id as parameter.

        Args:
            execute_fn: Function that accepts user_id and executes the use case
            current_user: JWT payload with user claims (requires 'sub' key)
            exception_mappings: List of exception-to-HTTP-status mappings

        Returns:
            Result from the use case execution

        Raises:
            HTTPException: If user_id extraction fails or on use case exceptions
        """
        # Extract user_id
        user_id = current_user.get("sub")
        if not user_id:
            log.warning("JWT token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Execute the function with user_id
        async def wrapped_execute():
            return await execute_fn(user_id)

        return await BaseRouteHandler.execute(
            wrapped_execute,
            exception_mappings=exception_mappings,
        )
