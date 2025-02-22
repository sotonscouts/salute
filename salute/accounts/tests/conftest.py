from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from salute.accounts.factories import UserFactory
from salute.people.factories import PersonFactory

if TYPE_CHECKING:
    from salute.accounts.models import User


@pytest.fixture
def user() -> User:
    return UserFactory(person=None)


@pytest.fixture
def user_with_person() -> User:
    return UserFactory(person=PersonFactory())
