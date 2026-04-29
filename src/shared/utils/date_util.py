from datetime import datetime


def get_current_datetime() -> datetime:
    """
    Get the current datetime.
    :return: Current datetime as a datetime object.
    """
    return datetime.now()


def get_current_date() -> str:
    """
    Get the current date in ISO format (YYYY-MM-DD).
    :return: Current date as a string.
    """
    return datetime.now().date().isoformat()
