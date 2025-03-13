import csv
import tomllib
from pathlib import Path
from typing import Any, Literal, TypedDict
from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Count, F, Q
from django.utils.timezone import get_current_timezone
from pydantic import BaseModel, TypeAdapter

from salute.hierarchy.constants import Weekday
from salute.hierarchy.models import District, Group, Section
from salute.integrations.tsa.client import MembershipAPIClient
from salute.integrations.tsa.schemata.units import UnitListingResult, UnitTypeID
from salute.people.models import Person
from salute.roles.models import Accreditation, AccreditationType, Role, RoleStatus, RoleType, Team, TeamType


class SyncReport(TypedDict):
    total_count: int
    added_count: int
    removed_count: int


class GroupInfo(BaseModel):
    unit_number: int
    location_name: str


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--clear-cache", action="store_true")
        parser.add_argument("--fetch-existing-people", action="store_true")
        parser.add_argument("--read-extra-data", action="store_true")

    def sync_groups(
        self,
        membership: MembershipAPIClient,
        district: District,
        *,
        units_for_district: list[UnitListingResult] | None = None,
        read_extra_data: bool = False,
    ) -> SyncReport:
        if units_for_district is None:
            units_for_district = membership.get_sub_units(parent_unit_id=district.tsa_id)

        if read_extra_data:
            ta = TypeAdapter(dict[str, GroupInfo])
            with Path("data/groups.toml").open("rb") as fh:
                group_data = ta.validate_python(tomllib.load(fh))

        group_tsa_ids: set[UUID] = set()
        added_count: int = 0
        for unit in filter(lambda unit: unit.unit_type_id == UnitTypeID.GROUP, units_for_district):
            unit_detail = membership.get_unit_detail(unit_id=unit.id)

            data = {
                "unit_name": unit.unit_name,
                "shortcode": unit.unit_shortcode,
                "district": district,
                "group_type": unit_detail.level_type,
                "charity_number": unit_detail.charity_number,
                "tsa_last_modified": unit_detail.admin_details.last_modified,
            }
            if read_extra_data:
                gdata = group_data[unit.unit_shortcode]
                data["local_unit_number"] = gdata.unit_number
                data["location_name"] = gdata.location_name

            group, _created = Group.objects.update_or_create(
                data,
                tsa_id=unit.id,
            )
            group_tsa_ids.add(group.tsa_id)
            if _created:
                added_count += 1

        # Warn if groups need removing, but do not actually remove them.
        if spurious_groups := Group.objects.exclude(tsa_id__in=group_tsa_ids):
            print(f"Warning: the following groups were found but do not exist: {spurious_groups}")

        return SyncReport(total_count=len(group_tsa_ids), added_count=added_count, removed_count=0)

    def sync_sections(
        self,
        membership: MembershipAPIClient,
        district: District,
        *,
        units_for_district: list[UnitListingResult] | None = None,
        read_extra_data: bool = False,
    ) -> SyncReport:
        if units_for_district is None:
            units_for_district = membership.get_sub_units(parent_unit_id=district.tsa_id)
        groups_by_tsa_id = {g.tsa_id: g for g in Group.objects.all()}
        districts_by_tsa_id = {d.tsa_id: d for d in District.objects.all()}

        if read_extra_data:
            with Path("data/sections.csv").open("r") as fh:
                section_weekday_data = {row["Shortcode"]: row for row in csv.DictReader(fh)}

        section_tsa_ids: set[UUID] = set()
        added_count: int = 0
        for unit in filter(
            lambda unit: unit.unit_type_id in [UnitTypeID.DISTRICT_SECTION, UnitTypeID.GROUP_SECTION],
            units_for_district,
        ):
            unit_detail = membership.get_unit_detail(unit_id=unit.id)
            section_data: dict[str, Any] = {
                "unit_name": unit.unit_name,
                "shortcode": unit.unit_shortcode,
                "section_type": unit_detail.section_type,
                "tsa_last_modified": unit_detail.admin_details.last_modified,
            }
            if read_extra_data:
                weekday = section_weekday_data[unit.unit_shortcode]["Weekday"].lower()
                nickname = section_weekday_data[unit.unit_shortcode]["Nickname"]
                section_data["usual_weekday"] = Weekday(weekday) if weekday != "-" else None
                section_data["nickname"] = nickname if nickname != "-" else ""

            if unit.unit_type_id == UnitTypeID.DISTRICT_SECTION:
                section_data["district"] = districts_by_tsa_id[unit_detail.parent_unit_id]
            elif unit.unit_type_id == UnitTypeID.GROUP_SECTION:
                section_data["group"] = groups_by_tsa_id[unit_detail.parent_unit_id]
            else:
                raise RuntimeError(f"Unknown section unit type: {unit.unit_type_id}")

            section, _created = Section.objects.update_or_create(
                section_data,
                tsa_id=unit.id,
            )
            section_tsa_ids.add(section.tsa_id)
            if _created:
                added_count += 1

        # Warn if sections need removing, but do not actually remove them.
        if spurious_sections := Section.objects.exclude(tsa_id__in=section_tsa_ids):
            print(f"Warning: the following sections were found but do not exist: {spurious_sections}")

        return SyncReport(total_count=len(section_tsa_ids), added_count=added_count, removed_count=0)

    def sync_district(
        self, membership: MembershipAPIClient, district_id: UUID, *, read_extra_data: bool = False
    ) -> District:
        district_details = membership.get_unit_detail(unit_id=district_id)

        district, _ = District.objects.update_or_create(
            {
                "unit_name": district_details.name,
                "shortcode": district_details.admin_details.unit_shortcode,
                "tsa_last_modified": district_details.admin_details.last_modified,
            },
            tsa_id=district_id,
        )
        return district

    def _sync_teams_for_unit(
        self,
        *,
        membership: MembershipAPIClient,
        unit: District | Group | Section,
        unit_parent_field: Literal["district", "group", "section"],
    ) -> None:
        teams = membership.get_teams_and_roles_for_unit(unit_id=unit.tsa_id)

        valid_team_ids: set[UUID] = set()
        team_id_mapping: dict[UUID, Team] = {}
        sub_teams = []

        for team in teams:
            if team.parent_team_id is not None:
                sub_teams.append(team)
                continue

            team_type, _ = TeamType.objects.update_or_create(
                defaults={"name": team.team_name}, create_defaults={"nickname": ""}, tsa_id=team.team_id
            )
            team_obj, _ = Team.objects.update_or_create(  # type: ignore[misc]
                {"allow_sub_team": team.allow_sub_team, "inherit_permissions": team.inherit_permissions},
                team_type=team_type,
                **{unit_parent_field: unit},  # type: ignore[arg-type]
            )
            team_id_mapping[team_obj.team_type.tsa_id] = team_obj  # Note: Notice this is unique within a unit
            valid_team_ids.add(team_obj.id)

            for role_type in team.roles:
                RoleType.objects.update_or_create(name=role_type.name)

        for subteam in sub_teams:
            team_type, _ = TeamType.objects.update_or_create(
                defaults={"name": subteam.team_name}, create_defaults={"nickname": ""}, tsa_id=subteam.team_id
            )
            assert subteam.parent_team_id is not None
            subteam_obj, _ = Team.objects.update_or_create(
                {"allow_sub_team": subteam.allow_sub_team, "inherit_permissions": subteam.inherit_permissions},
                team_type=team_type,
                parent_team=team_id_mapping[subteam.parent_team_id],
            )
            valid_team_ids.add(subteam_obj.id)

            for role_type in subteam.roles:
                RoleType.objects.update_or_create(name=role_type.name)

        spurious_teams = Team.objects.filter(
            Q(**{unit_parent_field: unit}) | Q(**{f"parent_team__{unit_parent_field}": unit})  # type: ignore[misc]
        ).exclude(id__in=valid_team_ids)
        if spurious_teams:
            print(f"Deleting teams that no longer exist: {spurious_teams}")
            spurious_teams.delete()

    def sync_teams_for_district(self, membership: MembershipAPIClient, district: District) -> None:
        self._sync_teams_for_unit(membership=membership, unit=district, unit_parent_field="district")

    def sync_teams_for_group(self, membership: MembershipAPIClient, group: Group) -> None:
        self._sync_teams_for_unit(membership=membership, unit=group, unit_parent_field="group")

    def sync_teams_for_section(self, membership: MembershipAPIClient, section: Section) -> None:
        self._sync_teams_for_unit(membership=membership, unit=section, unit_parent_field="section")

    def sync_accreditations_for_unit(
        self,
        *,
        membership: MembershipAPIClient,
        unit: District | Group,
        unit_parent_field: Literal["district", "group"],
    ) -> None:
        tsa_accreditations = membership.get_unit_accreditations(unit_id=unit.tsa_id)
        for accreditation in tsa_accreditations:
            accreditation_type, _ = AccreditationType.objects.update_or_create(
                {"name": accreditation.accreditation_name}, tsa_id=accreditation.accreditation_id
            )

            Accreditation.objects.update_or_create(
                {
                    "accreditation_type": accreditation_type,
                    "person": Person.objects.get(tsa_id=accreditation.person_id),
                    "team": Team.objects.get(
                        team_type__tsa_id=accreditation.team_id,
                        **{f"{unit_parent_field}__tsa_id": accreditation.unit_id},
                    ),
                    "status": accreditation.status,
                    "expires_at": accreditation.expires_at.astimezone(get_current_timezone()),
                    "granted_at": accreditation.granted_at.astimezone(get_current_timezone()),
                },
                tsa_id=accreditation.id,
            )

        expected_accreditation_ids: set[UUID] = {acc.id for acc in tsa_accreditations}
        spurious_accreditations = Accreditation.objects.filter(**{f"team__{unit_parent_field}": unit}).exclude(
            tsa_id__in=expected_accreditation_ids
        )
        if spurious_accreditations:
            print(f"Deleting accreditations that no longer exist: {spurious_accreditations}")
            spurious_accreditations.delete()

    def handle(self, *args: str, **options: str) -> None:
        fetch_existing_people = options["fetch_existing_people"]
        read_extra_data = bool(options["read_extra_data"])

        request_cache_dir = Path(settings.BASE_DIR) / ".requests-cache"
        # token = input("Enter token: ")
        token = ""
        membership = MembershipAPIClient(
            auth_token=token,
            request_cache_dir=request_cache_dir,
        )

        if options["clear_cache"]:
            if "DELETE" != input("Please type DELETE to clear the cache: "):
                return

            for file in request_cache_dir.glob("*.json"):
                file.unlink(missing_ok=True)

        sync_reports: dict[str, SyncReport] = {}
        district_id = UUID("608a27d8-d19f-afce-c777-287339746221")

        district = self.sync_district(membership, district_id, read_extra_data=read_extra_data)
        self.sync_teams_for_district(membership, district)

        # Fetch all sub units for district first, so we only make the request once.
        units = membership.get_sub_units(parent_unit_id=district.tsa_id)

        sync_reports["groups"] = self.sync_groups(
            membership, district, units_for_district=units, read_extra_data=read_extra_data
        )
        for group in Group.objects.all():
            self.sync_teams_for_group(membership, group)

        sync_reports["sections"] = self.sync_sections(
            membership, district, units_for_district=units, read_extra_data=read_extra_data
        )
        for section in Section.objects.all():
            self.sync_teams_for_section(membership, section)

        person_ids: set[UUID] = set()

        # Next, we need to find people in our district.
        # This is not directly queryable, we need to look for people with roles in our teams.
        for team in Team.objects.select_related("district", "group", "section", "team_type").all():
            if team.unit.tsa_id is None:
                print(f"Warning: could not identify unit for {team}")
                continue

            expected_role_ids: set[UUID] = set()
            roles = membership.get_team_roles(unit_id=team.unit.tsa_id, team_id=team.team_type.tsa_id)
            for role in roles:
                if role.person_id not in person_ids:
                    if fetch_existing_people:
                        person_info = membership.get_person_detail(person_id=role.person_id)
                        person, _ = Person.objects.update_or_create(
                            person_info.model_dump(exclude={"id"}), tsa_id=person_info.id
                        )
                    else:
                        try:
                            person = Person.objects.get(tsa_id=role.person_id)
                        except Person.DoesNotExist:
                            person_info = membership.get_person_detail(person_id=role.person_id)
                            person, _ = Person.objects.update_or_create(
                                person_info.model_dump(exclude={"id"}), tsa_id=person_info.id
                            )
                    person_ids.add(role.person_id)
                else:
                    person = Person.objects.get(tsa_id=role.person_id)

                role_type, rt_created = RoleType.objects.get_or_create(name=role.role_name)
                if rt_created:
                    print(f"Created role type: {role_type}")

                role_status, rs_created = RoleStatus.objects.get_or_create(name=role.role_status or "-")
                if rs_created:
                    print(f"Created role status: {role_status}")

                role_obj, _ = Role.objects.update_or_create(
                    {"team": team, "person": person, "role_type": role_type, "status": role_status},
                    tsa_id=role.role_id,
                )
                expected_role_ids.add(role_obj.id)

            spurious_roles = Role.objects.filter(team=team).exclude(id__in=expected_role_ids)
            if spurious_roles:
                print(f"Deleting roles that no longer exist: {spurious_roles}")
                spurious_roles.delete()

        # Now let's look at accreditations
        self.sync_accreditations_for_unit(membership=membership, unit=district, unit_parent_field="district")
        for group in Group.objects.all():
            self.sync_accreditations_for_unit(membership=membership, unit=group, unit_parent_field="group")

        people_without_roles_or_accreditations = Person.objects.annotate(
            accreditation_count=Count("accreditations"),
            role_count=Count("roles"),  # TODO: distinct?
            acc_and_role_count=F("accreditation_count") + F("role_count"),
        ).filter(acc_and_role_count=0)
        if people_without_roles_or_accreditations:
            print(
                f"Deleting people that no longer have a role or accreditation: {people_without_roles_or_accreditations}"
            )
            people_without_roles_or_accreditations.delete()

        # Finally, let's sync up Team Types if we're reading extra data
        if read_extra_data:
            with Path("data/team_types.csv").open("r") as fh:
                tt_data = {row["tsa_id"]: row for row in csv.DictReader(fh)}
                for tsa_id, data in tt_data.items():
                    tt = TeamType.objects.get(tsa_id=tsa_id)
                    tt.nickname = data["nickname"]
                    tt.mailing_slug = data["mailing_slug"]
                    tt.has_team_lead = data["has_team_lead"] == "T"
                    tt.has_all_list = data["has_all_list"] == "T"
                    tt.included_in_all_members = data["included_in_all_members"] == "T"
                    tt.save()

        self.stdout.write(self.style.SUCCESS(str(sync_reports)))
