from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class User:
    id: str
    email: str
    password: str
    display_name: str
