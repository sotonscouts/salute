import json
from collections.abc import Generator
from pathlib import Path
from typing import Any, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, TypeAdapter
from requests import Session

from salute.integrations.tsa.schemata.accreditations import (
    UnitAccreditationListingItem,
    UnitAccreditationListingResponse,
)
from salute.integrations.tsa.schemata.people import PersonDetail
from salute.integrations.tsa.schemata.roles import TeamMemberListingEntry, TeamMemberListingResponse
from salute.integrations.tsa.schemata.teams import TeamsAndRolesListingResponse, TeamsAndRolesListingTeamEntry
from salute.integrations.tsa.schemata.units import UnitDetail, UnitListingPageResult, UnitListingResult

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class MembershipAPIClient:
    def __init__(
        self,
        *,
        auth_token: str,
        base_url: str = "https://tsa-memportal-prod-fun01.azurewebsites.net/api/",
        request_cache_dir: Path | None = None,
    ) -> None:
        self.base_url = base_url
        self.cache_dir = request_cache_dir

        self.session = Session()
        self.session.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {auth_token}",
        }

    def _request(
        self, method: Literal["GET", "POST"], endpoint: str, model: type[BaseModelT], **kwargs: Any
    ) -> BaseModelT:
        resp = self.session.request(method, self.base_url + endpoint, **kwargs)
        resp.raise_for_status()
        data = resp.json()
        return model.model_validate(data)

    def _fetch_subunit_listing_page(
        self,
        *,
        parent_unit_id: UUID,
        next_token: str | None = None,
        page_size: int = 99,
    ) -> UnitListingPageResult:
        print(f"Fetching sub-units of {parent_unit_id}. Page {next_token}")
        payload = {
            "pagesize": page_size,
            "filter": {"global": "", "globaland": False, "fieldand": True},
            "unitId": str(parent_unit_id),
        }

        if next_token is not None:
            payload["nexttoken"] = next_token

        return self._request("POST", "UnitListingAsync", UnitListingPageResult, json=payload)

    def _fetch_sub_units(self, *, parent_unit_id: UUID) -> Generator[UnitListingResult, None, None]:
        next_token: str | None = "0"  # noqa: S105

        while next_token is not None:
            page = self._fetch_subunit_listing_page(
                parent_unit_id=parent_unit_id,
                next_token=next_token,
            )
            yield from page.data

            next_token = page.nexttoken

    def get_sub_units(self, *, parent_unit_id: UUID) -> list[UnitListingResult]:
        """Get the sub-units of a unit, flattened for the entire hierarchy."""
        ta = TypeAdapter(list[UnitListingResult])
        cache_key = f"get_sub_units__{parent_unit_id}"
        cached_data = self._get_cache_data(cache_key)
        if cached_data is not None:
            return ta.validate_python(cached_data)

        data = list(self._fetch_sub_units(parent_unit_id=parent_unit_id))

        self._set_cache_data(cache_key, ta.dump_python(data, by_alias=True, mode="json"))
        return data

    def fetch_unit_detail(self, *, unit_id: UUID) -> UnitDetail:
        print(f"Fetching unit details for  {unit_id}")
        payload = {"unitId": str(unit_id)}
        return self._request("POST", "GetUnitDetailAsync", UnitDetail, json=payload)

    def get_unit_detail(self, *, unit_id: UUID) -> UnitDetail:
        cache_key = f"get_unit_detail__{unit_id}"
        cached_data = self._get_cache_data(cache_key)
        if cached_data is not None:
            return UnitDetail.model_validate(cached_data)

        data = self.fetch_unit_detail(unit_id=unit_id)
        self._set_cache_data(cache_key, data.model_dump(by_alias=True, mode="json"))
        return data

    def fetch_teams_and_roles_for_unit(self, *, unit_id: UUID) -> list[TeamsAndRolesListingTeamEntry]:
        print(f"Fetching teams for for {unit_id}")
        payload = {"unitId": str(unit_id)}
        data = self._request("POST", "UnitTeamsAndRolesListingAsync", TeamsAndRolesListingResponse, json=payload)
        return data.teams

    def get_teams_and_roles_for_unit(self, *, unit_id: UUID) -> list[TeamsAndRolesListingTeamEntry]:
        cache_key = f"get_teams_and_roles_for_unit__{unit_id}"
        ta = TypeAdapter(list[TeamsAndRolesListingTeamEntry])
        cached_data = self._get_cache_data(cache_key)
        if cached_data is not None:
            return ta.validate_python(cached_data)

        data = self.fetch_teams_and_roles_for_unit(unit_id=unit_id)
        self._set_cache_data(cache_key, ta.dump_python(data, by_alias=True, mode="json"))
        return data

    def fetch_team_roles_listing_page(
        self,
        *,
        unit_id: UUID,
        team_id: UUID,
        page_no: int = 1,
        page_size: int = 99,
    ) -> TeamMemberListingResponse:
        print(f"Fetching roles of team {team_id} for unit {unit_id}. Page {page_no}")
        payload = {
            "query": f"teamid='{team_id}' AND unitid ='{unit_id}'",
            "table": "TeamMembersView",
            "selectFields": [
                "Id",
                "PreferredName",
                "FullName",
                "Firstname",
                "Lastname",
                "RoleStatusName",
                "Role",
                "unitid",
                "TeamId",
                "Unitname",
                "ContactMembershipId",
                "UnitTypeId",
            ],
            "distinct": True,
            "isDashboardQuery": False,
            "pageNo": str(page_no),
            "pageSize": page_size,
        }

        return self._request("POST", "DataExplorer/GetResultsAsync", TeamMemberListingResponse, json=payload)

    def fetch_team_roles(self, *, unit_id: UUID, team_id: UUID) -> Generator[TeamMemberListingEntry, None, None]:
        page_no: int | None = 1

        while page_no is not None:
            page = self.fetch_team_roles_listing_page(
                unit_id=unit_id,
                team_id=team_id,
                page_no=page_no,
            )
            yield from page.data

            page_no = page.next_page

    def get_team_roles(self, *, unit_id: UUID, team_id: UUID) -> list[TeamMemberListingEntry]:
        cache_key = f"get_team_roles__{unit_id}_{team_id}"
        ta = TypeAdapter(list[TeamMemberListingEntry])
        cached_data = self._get_cache_data(cache_key)
        if cached_data is not None:
            return ta.validate_python(cached_data)

        data = list(self.fetch_team_roles(unit_id=unit_id, team_id=team_id))

        self._set_cache_data(cache_key, ta.dump_python(data, mode="json", by_alias=True))
        return data

    def fetch_person_detail(self, *, person_id: UUID) -> PersonDetail:
        print(f"Fetching person details for  {person_id}")
        payload = {"type": "contact", "contactId": str(person_id)}
        return self._request("POST", "GetContactDetailAsync", PersonDetail, json=payload)

    def get_person_detail(self, *, person_id: UUID) -> PersonDetail:
        cache_key = f"get_person_detail__{person_id}"
        if cached_data := self._get_cache_data(cache_key):
            return PersonDetail.model_validate(cached_data)

        data = self.fetch_person_detail(person_id=person_id)
        self._set_cache_data(cache_key, data.model_dump(mode="json", by_alias=True))
        return data

    def fetch_unit_accreditation_listing_page(
        self,
        *,
        unit_id: UUID,
        page_no: int = 1,
        page_size: int = 99,
    ) -> UnitAccreditationListingResponse:
        print(f"Fetching accreditations for unit {unit_id}. Page {page_no}")
        payload = {
            "query": f"UnitId ='{unit_id}'",
            "table": "LeaderAccreditationView",
            "selectFields": [
                "AccreditationId",
                "AccreditationName",
                "HolderId",
                "MembershipId",
                "TeamId",
                "UnitId",
                "StatusId",
                "Status",
                "ExpiryDate",
                "GrantedDate",
            ],
            "orderBy": "AccreditationName",
            "order": "asc",
            "distinct": True,
            "isDashboardQuery": False,
            "pageNo": page_no,
            "pageSize": page_size,
        }
        return self._request("POST", "DataExplorer/GetResultsAsync", UnitAccreditationListingResponse, json=payload)

    def fetch_unit_accreditations(self, *, unit_id: UUID) -> Generator[UnitAccreditationListingItem, None, None]:
        page_no: int | None = 1

        while page_no is not None:
            page = self.fetch_unit_accreditation_listing_page(
                unit_id=unit_id,
                page_no=page_no,
            )
            yield from page.data

            page_no = page.next_page

    def get_unit_accreditations(self, *, unit_id: UUID) -> list[UnitAccreditationListingItem]:
        cache_key = f"get_unit_accreditations__{unit_id}"
        ta = TypeAdapter(list[UnitAccreditationListingItem])
        cached_data = self._get_cache_data(cache_key)
        if cached_data is not None:
            return ta.validate_python(cached_data)

        data = list(self.fetch_unit_accreditations(unit_id=unit_id))

        self._set_cache_data(cache_key, ta.dump_python(data, mode="json", by_alias=True))
        return data

    def _set_cache_data(self, key: str, data: Any) -> None:
        if self.cache_dir is None:
            return

        path = self.cache_dir / f"{key}.json"
        with path.open("w") as fh:
            return json.dump(data, fh)  #

    def _get_cache_data(self, key: str) -> Any:
        if self.cache_dir is None:
            return None

        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        with path.open("r") as fh:
            return json.load(fh)
