from typing import Any, cast
from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand

from salute.integrations.email_octopus.client import EmailOctopusClient
from salute.integrations.email_octopus.models import EmailOctopusContact, EmailOctopusStatus
from salute.integrations.email_octopus.schemata import Contact, UpdateContactItem
from salute.people.models import Person, PersonQuerySet


class Stepper:
    def __init__(self, stdout: Any) -> None:
        self.stdout = stdout
        self.step_num = 1

    def step_heading(self, title: str) -> None:
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"STEP {self.step_num}: {title}")
        self.stdout.write("=" * 60 + "\n")
        self.step_num += 1


class Command(BaseCommand):
    help = "Sync email octopus contacts"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without making them",
        )

    def _get_tags_for_person(self, person: Person) -> list[str]:
        """Get the list of tags that should be applied to this person's contact.

        Args:
            person: The Person object

        Returns:
            List of tag names to apply
        """
        # Role Types (i.e Trustee, Chair, GLV, etc)
        role_types = (
            person.roles.filter(role_type__mailing_list_filterable=True)
            .values_list("role_type__name", flat=True)
            .distinct()
        )

        # Team Types (i.e 14-24 Team, Beaver Section Team, Helpers, etc)
        team_types = (
            person.roles.filter(team__team_type__mailing_list_filterable=True)
            .values_list("team__team_type__display_name", flat=True)
            .distinct()
        )

        tags = [f"Role Type: {role_type}" for role_type in role_types] + [
            f"Team Type: {team_type}" for team_type in team_types
        ]

        # Return sorted for consistency
        return sorted(set(tags))

    def _get_people_to_sync(self) -> PersonQuerySet:
        """Get a list of people to sync."""
        people_qs = cast(PersonQuerySet, Person.objects.all())
        people_qs = people_qs.annotate_is_member()
        return people_qs

    def get_deduplicated_people_by_email(self, people: PersonQuerySet) -> PersonQuerySet:
        """Deduplicate people by email address, keeping the person with the lowest UUID.

        :returns: A queryset of people with unique email addresses.
        """
        people_by_email: dict[str, Person] = {}
        duplicate_emails = set()

        for person in people:
            if not person.contact_email:
                self.stdout.write(self.style.WARNING(f"SKIP: {person.display_name} ({person.id}) - no contact email"))
                continue

            email_lower = person.contact_email.lower()

            if email_lower not in people_by_email:
                people_by_email[email_lower] = person
                continue

            # Duplicate email found
            duplicate_emails.add(email_lower)
            del people_by_email[email_lower]

            self.stdout.write(self.style.WARNING(f"DUPLICATE EMAIL: {email_lower}"))

        if duplicate_emails:
            self.stdout.write(
                self.style.WARNING(f"\nFound {len(duplicate_emails)} duplicate email(s) - removed both\n")
            )

        return Person.objects.filter(id__in=[person.id for person in people_by_email.values()])

    def _cleanup_orphaned_eo_contacts(self, client: EmailOctopusClient, list_id: str, *, dry_run: bool) -> int:
        """
        Remove any contacts from EO where it exists in the database, but the person is null.

        This indicates the person was deleted from salute but the EO contact was not cleaned
        up, leaving an orphaned contact.

        :returns: The number of orphaned contacts deleted (or that would be deleted in dry run)
        """
        orphaned_records = EmailOctopusContact.objects.filter(person__isnull=True)
        if not orphaned_records:
            self.stdout.write("No orphaned contacts to delete")
            return 0

        deleted_orphaned = 0

        for record in orphaned_records:
            contact_id_str = str(record.contact_id)
            self.stdout.write(f"  DELETE: Contact ID {contact_id_str} (orphaned record)")

            if not dry_run:
                try:
                    client.delete_contact(list_id, contact_id_str)
                    record.delete()
                    deleted_orphaned += 1
                    self.stdout.write(self.style.SUCCESS("    ✓ Deleted"))
                except Exception as e:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(f"    ✗ Failed: {e}"))

        if dry_run:
            orphaned_count = len(orphaned_records)
            self.stdout.write(f"\nWould delete {orphaned_count} orphaned contacts")
            return orphaned_count
        else:
            self.stdout.write(self.style.SUCCESS(f"\nDeleted {deleted_orphaned} orphaned contacts"))
            return deleted_orphaned

    def _cleanup_unknown_eo_contacts(self, client: EmailOctopusClient, list_id: str, *, dry_run: bool) -> int:
        eo_contacts = client.get_all_contacts(list_id)
        eo_contact_ids = {str(contact.id) for contact in eo_contacts}
        db_contact_ids = {str(rec.contact_id) for rec in EmailOctopusContact.objects.all()}

        # Quickly double check the previous step
        contacts_in_db_not_in_eo = db_contact_ids - eo_contact_ids
        if contacts_in_db_not_in_eo:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {len(contacts_in_db_not_in_eo)} contacts in database not in EO - these are orphaned records that should have been cleaned up by the previous step\n"  # noqa: E501
                )
            )  # noqa: E501
            for contact_id in contacts_in_db_not_in_eo:
                self.stdout.write(f"  ORPHANED RECORD: Contact ID {contact_id} exists in database but not in EO")
            EmailOctopusContact.objects.filter(contact_id__in=contacts_in_db_not_in_eo).delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {len(contacts_in_db_not_in_eo)} orphaned records from database")
            )

        contacts_in_eo_not_in_db = eo_contact_ids - db_contact_ids
        if not contacts_in_eo_not_in_db:
            self.stdout.write("No unknown contacts to delete")
            return 0

        # Delete the unknown contacts
        deleted_unknown = 0
        for unknown_contact_id in contacts_in_eo_not_in_db:
            self.stdout.write(f"  DELETE: Contact ID {unknown_contact_id} - not in database")

            if not dry_run:
                try:
                    client.delete_contact(list_id, unknown_contact_id)
                    deleted_unknown += 1
                    self.stdout.write(self.style.SUCCESS("    ✓ Deleted"))
                except Exception as e:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(f"    ✗ Failed: {e}"))

        if dry_run:
            self.stdout.write(f"\nWould delete {len(contacts_in_eo_not_in_db)} unknown contacts")
            return len(contacts_in_eo_not_in_db)
        else:
            self.stdout.write(self.style.SUCCESS(f"\nDeleted {deleted_unknown} unknown contacts"))
            return deleted_unknown

    def _add_contacts_for_people_missing_in_eo(
        self,
        client: EmailOctopusClient,
        list_id: str,
        people: PersonQuerySet,
        *,
        dry_run: bool,
    ) -> set[UUID]:
        """
        Add contacts to EO for any people that are missing a contact in EO.

        :returns: Set of person IDs that were added (or would be added in dry run)
        """
        people_without_contacts = people.filter(email_octopus_contact__isnull=True).annotate_is_member()
        if not people_without_contacts:
            self.stdout.write("No people missing in EO to add")
            return set()

        for person in people_without_contacts:
            if not person.contact_email:
                # Note: Should be unreachable.
                self.stdout.write(self.style.WARNING(f"  SKIP: {person.display_name} ({person.id}) - no email address"))
                continue

            self.stdout.write(f"  CREATE: {person.contact_email} - {person.display_name}")

            if not dry_run:
                try:
                    # Get tags for this person
                    tags = self._get_tags_for_person(person)

                    # Create contact in Email Octopus
                    new_contact = client.create_contact(
                        list_id=list_id,
                        email_address=person.contact_email,
                        fields={
                            "FirstName": person.first_name,
                            "LastName": person.last_name,
                            "MembershipNumber": person.formatted_membership_number,
                            "IsMember": "Yes" if person.is_member else "No",
                            "SaluteId": str(person.id),
                        },
                        tags=tags,
                        status="subscribed",
                    )

                    # Create database record linking to person
                    EmailOctopusContact.objects.create(
                        contact_id=new_contact.id,
                        person=person,
                    )

                    self.stdout.write(self.style.SUCCESS(f"    ✓ Created (ID: {new_contact.id})"))
                except Exception as e:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(f"    ✗ Failed: {e}"))

        return set(people_without_contacts.values_list("id", flat=True))

    def _compare_contact_to_person(self, contact: Contact, person: Person) -> list[str]:
        """
        Compare an EO contact to a Person and return a list of differences.

        :returns: List of human-readable strings describing any differences found
        """
        differences = []

        if contact.email_address.lower() != person.contact_email.lower():
            differences.append(f"EmailAddress: '{contact.email_address}' → '{person.contact_email}'")

        if contact.fields.first_name != person.first_name:
            differences.append(f"FirstName: '{contact.fields.first_name}' → '{person.first_name}'")

        if contact.fields.last_name != person.last_name:
            differences.append(f"LastName: '{contact.fields.last_name}' → '{person.last_name}'")

        if contact.fields.membership_number != person.formatted_membership_number:
            differences.append(
                f"MembershipNumber: '{contact.fields.membership_number}' → '{person.formatted_membership_number}'"
            )

        expected_is_member = "Yes" if person.is_member else "No"  # type: ignore
        if contact.fields.is_member != expected_is_member:
            differences.append(f"IsMember: '{contact.fields.is_member}' → '{expected_is_member}'")

        expected_salute_id = str(person.id)
        if contact.fields.salute_id != expected_salute_id:
            differences.append(f"SaluteId: '{contact.fields.salute_id}' → '{expected_salute_id}'")

        return differences

    def _sync_contact_tags(
        self, client: EmailOctopusClient, list_id: str, contact: Contact, person: Person
    ) -> dict[str, bool] | None:
        expected_tags = set(self._get_tags_for_person(person))
        current_tags = set(contact.tags)
        if expected_tags == current_tags:
            return None

        # The EO API is unreliable. Fetch the contact again to double check.
        contact = client.get_contact(list_id, contact.id)
        current_tags = set(contact.tags)
        if expected_tags == current_tags:
            return None

        print(
            f"Updating tags for contact {contact.email_address} ({contact.id}) - expected: {expected_tags}, current: {current_tags}"  # noqa: E501
        )
        return dict.fromkeys(expected_tags, True) | dict.fromkeys(current_tags - expected_tags, False)

    def _sync_existing_contacts(
        self, client: EmailOctopusClient, list_id: str, people: PersonQuerySet, *, dry_run: bool
    ) -> int:
        people = people.select_related("email_octopus_contact").annotate_is_member()

        if people.filter(email_octopus_contact__isnull=True).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Some people in this step are missing EO contacts - these should have been added in the previous step"  # noqa: E501
                )
            )

        eo_contacts = client.get_all_contacts(list_id)
        eo_contacts_by_id = {str(contact.id): contact for contact in eo_contacts}

        bulk_update_data: list[UpdateContactItem] = []

        for person in people.filter(email_octopus_contact__isnull=False):
            contact = eo_contacts_by_id.get(str(person.email_octopus_contact.contact_id))

            if not contact:
                self.stdout.write(
                    self.style.WARNING(
                        f"  SKIP: {person.contact_email} - EO contact not found, should have been added in previous step"  # noqa: E501
                    )
                )
                continue

            differences = self._compare_contact_to_person(contact, person)
            tag_updates = self._sync_contact_tags(client, list_id, contact, person)
            if not (differences or tag_updates):
                continue

            self.stdout.write(f"  DIFF: {person.contact_email} - {person.display_name}")
            for diff in differences:
                self.stdout.write(f"    - {diff}")

            all_fields = {
                "FirstName": person.first_name,
                "LastName": person.last_name,
                "MembershipNumber": person.formatted_membership_number,
                "IsMember": "Yes" if person.is_member else "No",
                "SaluteId": str(person.id),
            }

            data = {
                "id": contact.id,
                "email_address": person.contact_email,
                "fields": all_fields,
                # Note: We do not update status here - we only want to update fields and tags. Status should only be updated manually or in specific cases (e.g reactivating a contact that was unsubscribed by mistake), to avoid accidentally unsubscribing people or causing other unintended consequences.  # noqa: E501
            }

            if tag_updates is not None:
                data["tags"] = tag_updates

            bulk_update_data.append(UpdateContactItem.model_validate(data))

        if not bulk_update_data:
            self.stdout.write("  No contacts need updates")
        elif dry_run:
            self.stdout.write(f"\nWould update {len(bulk_update_data)} contacts")
        else:
            # Perform bulk update in batches of 100 (API limit)
            batch_size = 100
            total_updated = 0

            for i in range(0, len(bulk_update_data), batch_size):
                batch = bulk_update_data[i : i + batch_size]
                try:
                    client.bulk_update_contacts(list_id, batch)
                    total_updated += len(batch)
                    self.stdout.write(
                        self.style.SUCCESS(f"  Batch {i // batch_size + 1}: Updated {len(batch)} contacts")
                    )
                except Exception as e:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(f"  Batch {i // batch_size + 1}: Failed to update: {e}"))

            self.stdout.write(self.style.SUCCESS(f"\nUpdated {total_updated} contacts"))

        return len(bulk_update_data)

    def handle(self, *args: Any, **options: Any) -> None:
        api_key = settings.EMAIL_OCTOPUS_API_KEY  # type: ignore[misc]
        list_id = settings.EMAIL_OCTOPUS_LIST_ID  # type: ignore[misc]

        stepper = Stepper(self.stdout)

        client = EmailOctopusClient(api_key)
        is_dry_run = options["dry_run"]

        if is_dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))

        people = self._get_people_to_sync()
        people = self.get_deduplicated_people_by_email(people)
        self.stdout.write(self.style.SUCCESS(f"Found {people.count()} people to sync\n"))

        stepper.step_heading("Cleanup orphaned Email Octopus contacts")
        orphan_count = self._cleanup_orphaned_eo_contacts(client, list_id, dry_run=is_dry_run)

        stepper.step_heading("Cleanup unknown Email Octopus contacts")
        deleted_unknown = self._cleanup_unknown_eo_contacts(client, list_id, dry_run=is_dry_run)

        stepper.step_heading("Add missing people to Email Octopus")
        added_people = self._add_contacts_for_people_missing_in_eo(client, list_id, people, dry_run=is_dry_run)

        stepper.step_heading("Bulk update contacts")

        updated_people = self._sync_existing_contacts(
            client,
            list_id,
            people.exclude(id__in=added_people),  # Exclude people just added in this sync
            dry_run=is_dry_run,
        )

        stepper.step_heading("Updating subscription status in Salute based on EO unsubscribes")
        eo_contacts = client.get_all_contacts(list_id)
        eo_contact_status_by_id = {str(contact.id): contact.status for contact in eo_contacts}

        # Get all database records that have corresponding EO contacts
        db_contacts_to_update = []
        status_updates_count = 0

        for db_contact in EmailOctopusContact.objects.all():
            eo_status = eo_contact_status_by_id.get(str(db_contact.contact_id))
            if eo_status is None:
                # Contact not found in EO - this shouldn't happen after cleanup steps
                continue

            if db_contact.status != eo_status:
                db_contact.status = EmailOctopusStatus(eo_status)
                db_contacts_to_update.append(db_contact)
                status_updates_count += 1
                self.stdout.write(
                    f"  UPDATE STATUS: {db_contact.person.display_name if db_contact.person else 'Unknown'} - {db_contact.status} → {eo_status}"  # noqa: E501
                )  # noqa: E501

        if db_contacts_to_update:
            if not is_dry_run:
                EmailOctopusContact.objects.bulk_update(db_contacts_to_update, ["status"])
                self.stdout.write(self.style.SUCCESS(f"\nUpdated status for {len(db_contacts_to_update)} contacts"))
            else:
                self.stdout.write(f"\nWould update status for {len(db_contacts_to_update)} contacts")
        else:
            self.stdout.write("No status updates needed")

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("SYNC SUMMARY"))
        self.stdout.write("=" * 60)
        self.stdout.write(
            f"Orphaned contacts deleted: {orphan_count if not is_dry_run else f'{orphan_count} (would delete)'}"
        )
        self.stdout.write(
            f"Unknown contacts deleted: {deleted_unknown if not is_dry_run else f'{deleted_unknown} (would delete)'}"
        )
        created_count = len(added_people)
        self.stdout.write(
            f"People added to Email Octopus: {created_count if not is_dry_run else f'{created_count} (would add)'}"
        )
        self.stdout.write(
            f"Contacts bulk updated: {updated_people if not is_dry_run else f'{updated_people} (would update)'}"
        )
        self.stdout.write(f"Total people in filter: {len(people)}")

        self.stdout.write(
            f"Total contacts in Email Octopus (after sync): {len(eo_contacts) - deleted_unknown if not is_dry_run else 'N/A (dry run)'}"  # noqa: E501
        )
