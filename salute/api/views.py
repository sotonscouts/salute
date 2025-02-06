from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from strawberry.django.views import AsyncGraphQLView


class SaluteAsyncGraphQLView(AsyncGraphQLView):
    async def render_graphql_ide(self, request: HttpRequest) -> HttpResponse:
        user = await request.auser()

        # Block use of GraphiQL for unauthenticated users
        if not user.is_authenticated and not settings.ALLOW_UNAUTHENTICATED_GRAPHIQL:
            raise Http404()

        return await super().render_graphql_ide(request)
