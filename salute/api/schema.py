from collections.abc import Generator

import strawberry
from django.conf import settings
from graphql.validation import NoSchemaIntrospectionCustomRule
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry_django.permissions import IsAuthenticated

from salute.accounts.graphql.schema import AccountsQuery
from salute.hierarchy.graphql.schema import HierarchyQuery
from salute.locations.graphql.schema import LocationsQuery
from salute.mailing_groups.graphql.schema import MailingGroupsQuery
from salute.people.graphql.schema import PeopleQuery
from salute.roles.graphql.schema import RolesQuery


@strawberry.type
class PingQuery:
    @strawberry.field(extensions=[IsAuthenticated()])
    def ping(self) -> str:
        return "pong"


APP_QUERIES = (
    AccountsQuery,
    HierarchyQuery,
    LocationsQuery,
    MailingGroupsQuery,
    PeopleQuery,
    PingQuery,
    RolesQuery,
)


class DisableAnonymousIntrospection(strawberry.extensions.SchemaExtension):
    def on_validate(self) -> Generator[None, None, None]:
        """Block schema introspection for anonymous users when GraphiQL is off."""
        schema_context = self.execution_context.context
        request = schema_context.request
        if not request.user.is_authenticated and not settings.ALLOW_UNAUTHENTICATED_GRAPHIQL:  # type: ignore[misc]
            self.execution_context.validation_rules = self.execution_context.validation_rules + (
                NoSchemaIntrospectionCustomRule,
            )
        yield


schema = strawberry.Schema(
    query=merge_types("Query", APP_QUERIES),
    extensions=[
        DjangoOptimizerExtension,
        DisableAnonymousIntrospection,
    ],
)
