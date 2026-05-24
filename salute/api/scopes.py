from enum import StrEnum


class ApiScope(StrEnum):
    """OAuth scopes used by the Salute API."""

    SALUTE_USER = "salute:user"
    USER_READ = "user:read"
