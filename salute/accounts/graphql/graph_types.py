from datetime import datetime

import strawberry_django
from strawberry import field, relay

from salute.accounts import models


@strawberry_django.type(models.User)
class User(relay.Node):
    email: str = field(description="Email address")
    last_login: datetime = field(description="Timestamp of most recent login")
