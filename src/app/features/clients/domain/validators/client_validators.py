"""Shared validation logic for client domain."""


class ClientValidators:
    """Centralized validation rules for client entities and DTOs."""

    # Validation constants
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 200
    MAX_COMPANY_LENGTH = 200
    MAX_EMAIL_LENGTH = 255
    MAX_PHONE_LENGTH = 50

    @staticmethod
    def validate_name(name: str) -> None:
        """
        Validate client name.

        Args:
            name: Client name to validate

        Raises:
            ValueError: If name is invalid
        """
        if not name or not name.strip():
            raise ValueError("Client name cannot be empty")

        if len(name) > ClientValidators.MAX_NAME_LENGTH:
            raise ValueError(f"Client name cannot exceed {ClientValidators.MAX_NAME_LENGTH} characters")

    @staticmethod
    def validate_company(company: str) -> None:
        """
        Validate company name.

        Args:
            company: Company name to validate

        Raises:
            ValueError: If company name is invalid
        """
        if len(company) > ClientValidators.MAX_COMPANY_LENGTH:
            raise ValueError(f"Company name cannot exceed {ClientValidators.MAX_COMPANY_LENGTH} characters")
