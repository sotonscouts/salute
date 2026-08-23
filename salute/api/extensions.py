from collections.abc import Callable
from typing import Any, ClassVar

from django.contrib.auth.models import AnonymousUser
from strawberry.types.info import Info
from strawberry_django.permissions import DjangoNoPermission, DjangoPermissionExtension, _desc
from strawberry_django.resolvers import django_resolver

from salute.accounts.models import User
from salute.api.scopes import ApiScope


class IsPersonOrHasScope(DjangoPermissionExtension):
    """Mark a field as only resolvable by a person or a service account with the given scope."""

    DEFAULT_ERROR_MESSAGE: ClassVar[str] = "User is not a person or a service account with the required scope."
    SCHEMA_DIRECTIVE_DESCRIPTION: ClassVar[str | None] = _desc(  # type: ignore[no-untyped-call]
        "Can only be resolved by a person or a service account with the required scope.",
    )

    def __init__(
        self,
        scope: str,
        *,
        message: str | None = None,
        use_directives: bool = True,
        fail_silently: bool = True,
    ) -> None:
        super().__init__(
            message=message,
            use_directives=use_directives,
            fail_silently=fail_silently,
        )
        self.scope = scope

    @django_resolver(qs_hook=None)
    def resolve_for_user(
        self,
        resolver: Callable,
        user: User | AnonymousUser | None,  # type: ignore[override]
        *,
        info: Info,
        source: Any,
    ) -> Any:
        scopes: list[str] = info.context.request.scopes

        if user is None or not user.is_authenticated or not user.is_active:
            raise DjangoNoPermission

        if user.service_account:
            if self.scope not in scopes:
                raise DjangoNoPermission
        elif user.person:
            # Empty scopes means session auth; OAuth scope checks apply to bearer tokens only.
            if scopes and ApiScope.SALUTE_USER not in scopes:
                raise DjangoNoPermission
        elif scopes:
            raise DjangoNoPermission

        return resolver()


class HasPermOrScope(DjangoPermissionExtension):
    """Mark a field as resolvable by a user with the given permission, or a service account with the given scope."""

    DEFAULT_ERROR_MESSAGE: ClassVar[str] = "User does not have permission."
    SCHEMA_DIRECTIVE_DESCRIPTION: ClassVar[str | None] = _desc(  # type: ignore[no-untyped-call]
        "Can be resolved by a user with the required permission or a service account with the required scope.",
    )

    def __init__(
        self,
        perm: str,
        scope: ApiScope,
        *,
        message: str | None = None,
        use_directives: bool = True,
        fail_silently: bool = True,
    ) -> None:
        super().__init__(
            message=message,
            use_directives=use_directives,
            fail_silently=fail_silently,
        )
        self.perm = perm
        self.scope = scope

    @django_resolver(qs_hook=None)
    def resolve_for_user(
        self,
        resolver: Callable,
        user: User | AnonymousUser | None,  # type: ignore[override]
        *,
        info: Info,
        source: Any,
    ) -> Any:
        scopes: list[str] = info.context.request.scopes

        if user is None or not user.is_authenticated or not user.is_active:
            raise DjangoNoPermission

        if user.service_account:
            if self.scope not in scopes:
                raise DjangoNoPermission
        elif not user.has_perm(self.perm):
            raise DjangoNoPermission

        return resolver()


class IsServiceAccountWithScope(DjangoPermissionExtension):
    """Mark a field as only resolvable by a service account with the given scope."""

    DEFAULT_ERROR_MESSAGE: ClassVar[str] = "User is not a service account with the required scope."
    SCHEMA_DIRECTIVE_DESCRIPTION: ClassVar[str | None] = _desc(  # type: ignore[no-untyped-call]
        "Can only be resolved by a service account with the required scope.",
    )

    def __init__(
        self,
        scope: ApiScope,
        *,
        message: str | None = None,
        use_directives: bool = True,
        fail_silently: bool = True,
    ) -> None:
        super().__init__(
            message=message,
            use_directives=use_directives,
            fail_silently=fail_silently,
        )
        self.scope = scope

    @django_resolver(qs_hook=None)
    def resolve_for_user(
        self,
        resolver: Callable,
        user: User | AnonymousUser | None,  # type: ignore[override]
        *,
        info: Info,
        source: Any,
    ) -> Any:
        scopes: list[str] = info.context.request.scopes

        if user is None or not user.is_authenticated or not user.is_active or not user.service_account:
            raise DjangoNoPermission

        if self.scope not in scopes:
            raise DjangoNoPermission

        return resolver()
