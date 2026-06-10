"""Factory functions for creating domain-specific loggers."""

from src.app.shared.logging.application_logger import ApplicationLogger
from src.app.shared.logging.business_logger import BusinessLogger
from src.app.shared.logging.integration_logger import IntegrationLogger
from src.app.shared.logging.logger import get_logger
from src.app.shared.logging.technical_logger import TechnicalLogger


def create_business_logger(name: str, user_id: str) -> BusinessLogger:
    """
    Create logger for business operations.

    Args:
        name: Logger name (typically __name__ of module)
        user_id: User ID performing the operation

    Returns:
        BusinessLogger instance with user context

    Example:
        log = create_business_logger(__name__, user_id="user-123")
        log.event("project.created", entity_id="proj-456")
    """
    return BusinessLogger(get_logger(name), user_id=user_id)


def create_technical_logger(name: str, component: str) -> TechnicalLogger:
    """
    Create logger for technical/infrastructure operations.

    Args:
        name: Logger name (typically __name__ of module)
        component: Component name (e.g., "database", "cache", "filesystem")

    Returns:
        TechnicalLogger instance with component context

    Example:
        log = create_technical_logger(__name__, component="database")
        log.operation("db.query", success=True, duration_ms=45)
    """
    return TechnicalLogger(get_logger(name), component=component)


def create_integration_logger(name: str, service_name: str) -> IntegrationLogger:
    """
    Create logger for external service integrations.

    Args:
        name: Logger name (typically __name__ of module)
        service_name: External service name (e.g., "openai", "stripe")

    Returns:
        IntegrationLogger instance with service context

    Example:
        log = create_integration_logger(__name__, service_name="openai")
        log.api_call("/v1/chat/completions", status_code=200)
    """
    return IntegrationLogger(get_logger(name), service_name=service_name)


def create_application_logger(name: str, component: str | None = None) -> ApplicationLogger:
    """
    Create logger for general application events (DEFAULT).

    Use this when specialized loggers don't fit.

    Args:
        name: Logger name (typically __name__ of module)
        component: Optional component name (e.g., "api", "migrations", "config")

    Returns:
        ApplicationLogger instance

    Example:
        log = create_application_logger(__name__, component="api")
        log.startup("Server started", port=8000, env="production")
    """
    return ApplicationLogger(get_logger(name), component=component)
