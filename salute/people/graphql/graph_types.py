import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasSourcePerm

from salute.people import models


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
