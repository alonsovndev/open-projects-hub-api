from pathlib import Path


class Paths:
    """
    A centralized class for managing all application paths.
    Ensures portability and consistency across different environments.
    """

    # Base directory of the project
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

    # Configuration directory
    CONFIG_DIR = BASE_DIR / "src/app/config"

    # Environment file path
    ENV_FILE_PATH = BASE_DIR / ".env"
