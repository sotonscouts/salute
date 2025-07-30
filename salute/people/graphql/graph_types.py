from string import Template
from typing import TYPE_CHECKING, Annotated, Any, cast

import strawberry as sb
import strawberry_django as sd
from django.conf import settings
from django.db.models import QuerySet
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import HasPerm, HasSourcePerm

from salute.accounts.models import User
from salute.people import models
from salute.people.utils import format_phone_number

if TYPE_CHECKING:
    from salute.roles.graphql.graph_types import Accreditation, Role


@sd.filter_type(models.Person, lookups=True)
class PersonFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    display_name: sb.auto = sb.UNSET


@sd.order_type(models.Person)
class PersonOrder:
    first_name: sb.auto
    display_name: sb.auto


@sd.type(
    models.Person,
    filters=PersonFilter,
    ordering=PersonOrder,
)
class Person(sb.relay.Node):
    first_name: str
    display_name: str
    formatted_membership_number: str = sd.field(only="membership_number")

    roles: sd.relay.DjangoListConnection[Annotated["Role", sb.lazy("salute.roles.graphql.graph_types")]] = (
        sd.connection(
            description="List roles",
            extensions=[HasPerm("role.list", message="You don't have permission to list roles.", fail_silently=False)],
        )
    )

    accreditations: sd.relay.DjangoListConnection[
        Annotated["Accreditation", sb.lazy("salute.roles.graphql.graph_types")]
    ] = sd.connection(
        description="List accreditations",
        extensions=[
            HasPerm(
                "accreditation.list", message="You don't have permission to list accreditations.", fail_silently=False
            )
        ],
    )

    @sd.field(
        only="tsa_email",
        select_related="workspace_account",
        extensions=[HasSourcePerm("person.view", fail_silently=True)],
    )
    def contact_email(self, info: sb.Info) -> str | None:
        """
        Get the contact email for the person.

        This logic is repeated in the Person model.
        """
        try:
            return self.workspace_account.primary_email  # type: ignore
        except models.Person.workspace_account.RelatedObjectDoesNotExist:
            if info.context["request"].user.has_perm("person.view_pii", self):
                return self.tsa_email  # type: ignore[attr-defined]
        return None

    @sd.field(
        name="phoneNumber",
        description="Phone Number",
        only="phone_number",
        extensions=[HasSourcePerm("person.view_pii", fail_silently=True)],
    )
    def formatted_phone_number(self) -> str | None:
        return format_phone_number(self.phone_number)  # type: ignore[attr-defined]

    @sd.field(
        name="alternatePhoneNumber",
        description="Alternate Phone Number",
        only="alternate_phone_number",
        extensions=[HasSourcePerm("person.view_pii", fail_silently=True)],
    )
    def formatted_alternative_phone_number(self) -> str | None:
        return format_phone_number(self.alternate_phone_number)  # type: ignore[attr-defined]

    @sd.field(
        description="Link to the TSA person profile.",
        only="tsa_id",
    )
    def tsa_profile_link(self) -> str:
        template = Template(settings.TSA_PERSON_PROFILE_LINK_TEMPLATE)  # type: ignore[misc]
        return template.safe_substitute(tsaid=self.tsa_id)  # type: ignore[attr-defined]

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
