from __future__ import annotations

from typing import Any

from django.http import HttpRequest
from strawberry.django.context import StrawberryDjangoContext

from salute.roles.graphql.data_loaders import create_roles_dataloaders


class SaluteContext(StrawberryDjangoContext):
    def __init__(self, request: HttpRequest, response: Any = None, **kwargs: Any) -> None:
        super().__init__(request=request, response=response, **kwargs)
        self.roles = create_roles_dataloaders()
