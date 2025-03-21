# ruff: noqa: A005
from dataclasses import dataclass


@dataclass
class Auth0TokenInfo:
    aud: str
    sub: str
    scopes: list[str]

    def get_google_uid(self) -> str | None:
        if not self.sub.startswith("google-oauth2|"):
            return None
        return self.sub.removeprefix("google-oauth2|")
