import strawberry
import strawberry_django
from strawberry_django.optimizer import DjangoOptimizerExtension

from salute.hierarchy import models as hierarchy_models

from .types import District, Group, Section, Person


@strawberry.type
class Query:
    groups: strawberry_django.relay.ListConnectionWithTotalCount[Group] = strawberry_django.connection()
    sections: strawberry_django.relay.ListConnectionWithTotalCount[Section] = strawberry_django.connection(max_results=5)
    people: strawberry_django.relay.ListConnectionWithTotalCount[Person] = strawberry_django.connection()

    @strawberry_django.field
    def district(self) -> District:
        return hierarchy_models.District.objects.get()


schema = strawberry.Schema(
    query=Query,
    extensions=[
        DjangoOptimizerExtension,
    ],
)
