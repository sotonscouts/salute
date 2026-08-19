import argparse
from typing import Any

from django.core.management.base import BaseCommand
from google.oauth2 import service_account
from googleapiclient.discovery import build

from django.conf import settings
from salute.integrations.workspace.models import WorkspaceAccount
from salute.integrations.workspace.service import WorkspaceService
from salute.people.models import Person
import xkcdpass as xp

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]

DEFAULT_OU_PATH = "/People"


class Command(BaseCommand):
    help = "Create a new Workspace user"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("membership_number", type=str, help="The membership number of the person to create a Workspace user for")


    def generate_workspace_password() -> str:
        wordfile = xp.locate_wordfile()
        mywords = xp.generate_wordlist(wordfile=wordfile, min_length=5, max_length=8)

        return xp.generate_xkcdpassword(mywords, numwords=3, delimiter="-")

    def handle(self, *args: str, **options: str) -> None:
        credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)  # type: ignore[no-untyped-call]
        delegated_credentials = credentials.with_subject("service-salute@southamptoncityscouts.org.uk")
        service = build("admin", "directory_v1", credentials=delegated_credentials)

        person = Person.objects.get(membership_number=options["membership_number"])
        if person.workspace_account is not None:
            self.stdout.write(self.style.WARNING(f"Person {person} already has a Workspace account"))
            return

        self.stdout.write(self.style.SUCCESS(f"Creating Workspace user for {person}"))
        username = person.username_base

        expected_username = f"{username}@{settings.GOOGLE_DOMAIN}"

        if WorkspaceAccount.objects.filter(primary_email=expected_username).exists():
            self.stdout.write(self.style.WARNING(f"Workspace account {expected_username} already exists"))
            return

        password = self.generate_workspace_password()

        self.stdout.write(self.style.SUCCESS(f"Creating Workspace user {expected_username} with password {password}"))

        payload = {
            "primaryEmail": expected_username,
            "password": password,
            "name": {
                "givenName": person.first_name,
                "familyName": person.last_name,
            },
            "changePasswordAtNextLogin": True,
            "recoveryEmail": person.tsa_email,
            "recoveryPhone": person.phone_number,
            "orgUnitPath": DEFAULT_OU_PATH,
            "externalIds": [
                {
                    "type": "organization",
                    "value": person.formatted_membership_number,
                },
            ],
        }

        print(payload)

        return

        response = service.users().insert(body=).execute()

        self.stdout.write(self.style.SUCCESS(f"Created Workspace user {expected_username} with password {password}"))