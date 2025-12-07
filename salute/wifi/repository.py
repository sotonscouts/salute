from __future__ import annotations

from xkcdpass import xkcd_password as xp  # type: ignore[import-untyped]

from salute.people.models import Person
from salute.wifi.models import WifiAccount, WifiAccountGroup


def generate_wifi_username(person: Person) -> str:
    """
    Generate a WiFi username for a person, ensuring uniqueness.
    """
    try:
        # Use primary email username
        username_base = person.workspace_account.primary_email.split("@")[0]
    except Person.workspace_account.RelatedObjectDoesNotExist:
        # Use cleaned display name if no workspace account is found
        username_base = (
            person.display_name.replace(" ", ".").replace("..", ".").replace("\\", "").replace("/", "").replace("'", "")
        )

    username_base = username_base.lower()

    if not WifiAccount.objects.filter(username=username_base).exists():
        return username_base

    existing_accounts = WifiAccount.objects.filter(username__istartswith=f"{username_base}")
    n = existing_accounts.count()
    return f"{username_base}{n}"


def generate_wifi_password() -> str:
    wordfile = xp.locate_wordfile()
    mywords = xp.generate_wordlist(wordfile=wordfile, min_length=5, max_length=8)

    return xp.generate_xkcdpassword(mywords, numwords=3, delimiter="-")


def create_wifi_account(person: Person, *, group: WifiAccountGroup | None = None) -> WifiAccount:
    if group is None:
        group = WifiAccountGroup.objects.get(is_default=True)

    return WifiAccount.objects.create(
        person=person,
        group=group,
        username=generate_wifi_username(person),
        password=generate_wifi_password(),
    )


def get_wifi_account_for_person(person: Person) -> WifiAccount:
    try:
        return WifiAccount.objects.filter(person=person).get()
    except WifiAccount.DoesNotExist:
        return create_wifi_account(person)
