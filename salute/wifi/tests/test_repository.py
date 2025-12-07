import pytest

from salute.integrations.workspace.factories import WorkspaceAccountFactory
from salute.people.factories import PersonFactory
from salute.wifi.factories import WifiAccountFactory
from salute.wifi.repository import generate_wifi_username


@pytest.mark.django_db
class TestGenerateWifiUsername:
    def test_generate_wifi_username__no_workspace_account(self) -> None:
        person = PersonFactory(preferred_name="John", last_name="Doe")
        assert generate_wifi_username(person) == "john.doe"

    def test_generate_wifi_username__with_workspace_account(self) -> None:
        person = PersonFactory(preferred_name="John", last_name="Doe")
        WorkspaceAccountFactory(person=person, primary_email="jonny@example.com")
        assert generate_wifi_username(person) == "jonny"

    def test_generate_wifi_username__with_special_characters(self) -> None:
        person = PersonFactory(preferred_name="John", last_name="O'Leary")
        assert generate_wifi_username(person) == "john.oleary"

    def test_generate_wifi_username__with_existing_username(self) -> None:
        person = PersonFactory(preferred_name="John", last_name="Doe")
        WifiAccountFactory(username="john.doe")
        assert generate_wifi_username(person) == "john.doe1"
