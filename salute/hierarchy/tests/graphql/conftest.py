from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
import pytest_django

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


@pytest.fixture()
def use_dummy_tsa_unit_link_template(settings: Generator[pytest_django.fixtures.SettingsWrapper, None, None]) -> None:
    settings.TSA_UNIT_LINK_TEMPLATE = "https://example.com/units/$tsaid/"  # type: ignore[attr-defined]
