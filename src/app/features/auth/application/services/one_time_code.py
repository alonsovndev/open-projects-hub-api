"""Generation of the short codes emailed for password reset and email verification."""

import secrets


# Excludes 0, 1, O, I (visually ambiguous) per FR-008-03 / FR-009-02.
ONE_TIME_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
ONE_TIME_CODE_LENGTH = 6


def generate_one_time_code() -> str:
    return "".join(secrets.choice(ONE_TIME_CODE_ALPHABET) for _ in range(ONE_TIME_CODE_LENGTH))
