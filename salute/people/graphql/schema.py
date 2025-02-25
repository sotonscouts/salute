from collections.abc import Iterable
from typing import cast

import strawberry as sb
import strawberry_django as sd
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import HasPerm

from salute.accounts.models import User
from salute.people import models as people_models

from .graph_types import Person


@sb.type
class PeopleQuery:
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
