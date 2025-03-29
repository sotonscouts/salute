from typing import TYPE_CHECKING, Annotated, Any, cast

import strawberry as sb
import strawberry_django as sd
from django.db.models import QuerySet
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import HasPerm, HasSourcePerm

from salute.accounts.models import User
from salute.people import models

if TYPE_CHECKING:
    from salute.roles.graphql.graph_types import Role


@sd.filter(models.Person, lookups=True)
class PersonFilter:
    display_name: sb.auto
    membership_number: sb.auto


@sd.order(models.Person)
class PersonOrder:
    first_name: sb.auto
    display_name: sb.auto


@sd.type(
    models.Person,
    filters=PersonFilter,
    order=PersonOrder,  # type: ignore[literal-required]
)
class Person(sb.relay.Node):
    first_name: str
    display_name: str
    formatted_membership_number: str = sd.field(only="membership_number")
    contact_email: str | None = sd.field(
        only="tsa_email",
        select_related="workspace_account",
        extensions=[HasSourcePerm("person.view_pii", fail_silently=True)],
    )

    roles: sd.relay.ListConnectionWithTotalCount[Annotated["Role", sb.lazy("salute.roles.graphql.graph_types")]] = (
        sd.connection(
            description="List roles",
            extensions=[HasPerm("role.list", message="You don't have permission to list roles.", fail_silently=False)],
        )
    )

    @classmethod
    def get_queryset(
        cls, queryset: models.PersonQuerySet | QuerySet, info: sb.Info, **kwargs: Any
    ) -> models.PersonQuerySet | QuerySet:
        user = get_current_user(info)
        if not user.is_authenticated:
            return queryset.none()

        user = cast(User, user)
        # When the strawberry optimiser is determining the queryset relations, it will call this method.
        # In such calls, the queryset is not a PersonQuerySet, but a Django QuerySet.
        if hasattr(queryset, "for_user"):
            return queryset.for_user(user)
        return queryset
