import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm, HasRetvalPerm

from salute.people import models as people_models

from .graph_types import Permit, PermitActivity, PermitCategory, PermitStatus, PermitType, Person


@sb.type
class PeopleQuery:
    @sd.field(
        description="Get a person by ID",
        extensions=[
            HasRetvalPerm("person.view", message="You don't have permission to view that person.", fail_silently=False)
        ],
        deprecation_reason="Use the `people` field instead.",
    )
    def person(self, person_id: sb.relay.GlobalID, info: sb.Info) -> Person:
        return people_models.Person.objects.get(id=person_id.node_id)  # type: ignore[return-value]

    people: sd.relay.DjangoListConnection[Person] = sd.connection(
        description="List people",
        extensions=[HasPerm("person.list", message="You don't have permission to list people.", fail_silently=False)],
    )

    permits: sd.relay.DjangoListConnection[Permit] = sd.connection(
        description="List permits",
        extensions=[HasPerm("permit.list", message="You don't have permission to list permits.", fail_silently=False)],
    )

    permit_activities: sd.relay.DjangoListConnection[PermitActivity] = sd.connection(
        description="List permit activities",
        extensions=[HasPerm("permit.list", message="You don't have permission to list permits.", fail_silently=False)],
    )
    permit_categories: sd.relay.DjangoListConnection[PermitCategory] = sd.connection(
        description="List permit categories",
        extensions=[HasPerm("permit.list", message="You don't have permission to list permits.", fail_silently=False)],
    )
    permit_types: sd.relay.DjangoListConnection[PermitType] = sd.connection(
        description="List permit types",
        extensions=[HasPerm("permit.list", message="You don't have permission to list permits.", fail_silently=False)],
    )
    permit_statuses: sd.relay.DjangoListConnection[PermitStatus] = sd.connection(
        description="List permit statuses",
        extensions=[HasPerm("permit.list", message="You don't have permission to list permits.", fail_silently=False)],
    )
