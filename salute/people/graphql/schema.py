import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm, HasRetvalPerm

from salute.people import models as people_models

from .graph_types import Person


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
