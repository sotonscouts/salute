import strawberry
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension


@strawberry.type
class PingQuery:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


APP_QUERIES = (PingQuery,)

schema = strawberry.Schema(
    query=merge_types("Query", APP_QUERIES),
    extensions=[
        DjangoOptimizerExtension,
    ],
)
