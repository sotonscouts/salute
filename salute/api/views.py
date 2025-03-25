from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import Http404
from strawberry.django.views import AsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse

from salute.api.auth0.auth import (
    RequestAuthenticationError,
    authenticate_user_with_bearer_token,
)

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse, HttpResponseBase


class SaluteAsyncGraphQLView(AsyncGraphQLView):
    async def render_graphql_ide(self, request: HttpRequest) -> HttpResponse:
        user = await request.auser()

        # Block use of GraphiQL for unauthenticated users
        if not user.is_authenticated and not settings.ALLOW_UNAUTHENTICATED_GRAPHIQL:  # type: ignore[misc]
            raise Http404()

        return await super().render_graphql_ide(request)

    async def dispatch(  # type: ignore[override]
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseBase:
        response_data = await sync_to_async(self._authenticate_request)(request)
        if response_data is not None:
            return self.create_response(response_data=response_data, sub_response=await self.get_sub_response(request))

        return await super().dispatch(request, *args, **kwargs)

    def _authenticate_request(self, request: HttpRequest) -> GraphQLHTTPResponse | None:
        """
        Authenticate the request.

        :returns: An error response, or None if the request may continue.
        """
        if request.user.is_authenticated:
            return None

        # Check for a Bearer token Authorization header
        if header := request.headers.get("Authorization"):
            if header.startswith("Bearer "):
                token = header.removeprefix("Bearer ")
                try:
                    auth_info = authenticate_user_with_bearer_token(token)
                except RequestAuthenticationError as e:
                    return {"data": None, "errors": e.errors}  # type: ignore[typeddict-item]

                # Mutate the request with the data we need.
                request.user = auth_info["user"]
                request.scopes = auth_info["scopes"]  # type: ignore[attr-defined]

        return None
