"""Project access code: the unguessable key a client stakeholder types to review a project."""

import re
import secrets


ACCESS_CODE_PREFIX = "PRJ-"
ACCESS_CODE_LENGTH = 8

# 32 symbols without O/0/I/1, so a code read aloud or off a screenshot survives retyping.
# 32^8 is about 1e12 combinations, which is what makes enumeration impractical.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_ACCESS_CODE_PATTERN = re.compile(rf"^{ACCESS_CODE_PREFIX}[{_ALPHABET}]{{{ACCESS_CODE_LENGTH}}}$")


def generate_access_code() -> str:
    """Return a new random access code, e.g. ``PRJ-7K3M9XQ2``."""
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(ACCESS_CODE_LENGTH))
    return f"{ACCESS_CODE_PREFIX}{suffix}"


def normalize_access_code(raw_code: str) -> str:
    """Uppercase and trim what a person typed, so ``prj-7k3m9xq2 `` matches the stored code."""
    return raw_code.strip().upper()


def is_valid_access_code(code: str) -> bool:
    """True when ``code`` has the generated shape. A cheap gate before touching the database."""
    return _ACCESS_CODE_PATTERN.match(code) is not None
