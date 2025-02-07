import strawberry
from django.conf import settings
from graphql.validation import NoSchemaIntrospectionCustomRule
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry_django.permissions import IsAuthenticated

from salute.accounts.graphql.schema import AccountsQuery
from salute.hierarchy.graphql.schema import HierarchyQuery


@strawberry.type
class PingQuery:
    @strawberry.field(extensions=[IsAuthenticated()])
    def ping(self) -> str:
        return "pong"


APP_QUERIES = (
    AccountsQuery,
    HierarchyQuery,
    PingQuery,
)


class DisableAnonymousIntrospection(strawberry.extensions.SchemaExtension):
    async def on_validation_start(self) -> None:
        schema_context = self.execution_context.context
        request = schema_context.request
        user = await request.auser()

        # Block use of Query Introspection for unauthenticated users
        if not user.is_authenticated and not settings.ALLOW_UNAUTHENTICATED_GRAPHIQL:
            self.execution_context.validation_rules = self.execution_context.validation_rules + (
                NoSchemaIntrospectionCustomRule,
            )


schema = strawberry.Schema(
    query=merge_types("Query", APP_QUERIES),
    extensions=[
        DjangoOptimizerExtension,
        DisableAnonymousIntrospection,
    ],
)
