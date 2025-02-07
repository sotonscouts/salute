import pytest

from salute.accounts.factories import UserFactory


@pytest.mark.django_db
class TestUserFactory:
    def test_user_factory(self) -> None:
        user = UserFactory()

        assert user.email is not None
        assert user.is_active
