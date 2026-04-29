def get_config_value(config: dict, key: str, default=None, expected_type=None):
    """
    Helper function to fetch a configuration dictionary.
    :param key: The value with validation and casting.
    :param config: Tey to fetch from the configuration.
    :param default: The default value to return if the key is missing.
    :param expected_type: The expected type for validation and casting.
    :return: The configuration value.
    """
    value = config.get(key, default)
    if value is None:
        raise ValueError(f"Missing required configuration key: '{key}'")

    # Attempt to cast the value to the expected type
    if expected_type:
        try:
            value = expected_type(value)
        except (ValueError, TypeError) as e:
            raise TypeError(
                f"Configuration key '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}"
            ) from e

    # Custom validation for port ranges
    if key == "port" and not (1 <= value <= 65535):
        raise ValueError(f"Configuration key '{key}' must be a valid port number (1-65535), got {value}")

    return value
