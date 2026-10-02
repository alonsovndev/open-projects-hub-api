"""Links to the web app's code-entry pages, embedded in verification and reset emails."""

from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class EmailLinks:
    base_url: str

    def verify_email(self, email: str, code: str, set_password: bool) -> str:
        params = {"email": email, "code": code}
        if set_password:
            params["setPassword"] = "1"
        return f"{self.base_url.rstrip('/')}/verify-email?{urlencode(params)}"

    def reset_password(self, email: str, code: str) -> str:
        return f"{self.base_url.rstrip('/')}/reset-password?{urlencode({'email': email, 'code': code})}"
