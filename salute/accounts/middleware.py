from __future__ import annotations

import typing
from http import HTTPStatus

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import AuthenticationFailed, JWTAuthentication

from salute.accounts.models import User

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


class TokenAuthMiddleware:
    """Handle token authentication. This must come after django.contrib.auth.middleware.AuthenticationMiddleware"""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.process_request(request)
        return self.get_response(request)

    def process_request(self, request: HttpRequest) -> HttpResponse:
        jwt_auth = JWTAuthentication()
        try:
            if auth_result := jwt_auth.authenticate(request):
                user, _token = auth_result
                request.user = typing.cast(User, user)
            return self.get_response(request)
        except AuthenticationFailed as e:
            return JsonResponse(e.get_codes(), status=HTTPStatus.UNAUTHORIZED)
