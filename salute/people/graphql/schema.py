from collections.abc import Iterable
from typing import cast

import strawberry as sb
import strawberry_django as sd
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import HasPerm, HasRetvalPerm

from salute.accounts.models import User
from salute.people import models as people_models

from .graph_types import Person


@sb.type
class PeopleQuery:
    @sd.field(
        description="Get a person by ID",
        extensions=[
            HasRetvalPerm("person.view", message="You don't have permission to view that person.", fail_silently=False)
        ],
    )
    def person(self, person_id: sb.relay.GlobalID, info: sb.Info) -> Person:
        return people_models.Person.objects.get(id=person_id.node_id)  # type: ignore[return-value]

    @sd.connection(
        sd.relay.ListConnectionWithTotalCount[Person],
        description="List people",
        extensions=[HasPerm("person.list", message="You don't have permission to list people.", fail_silently=False)],
    )
    def people(self, info: sb.Info) -> Iterable[people_models.Person]:
        user = get_current_user(info)
        assert user.is_authenticated
        user = cast(User, user)
        qs: Iterable[people_models.Person] = people_models.Person.objects.for_user(user)
        return qs
