import time
from datetime import date, datetime

import requests
from pydantic import BaseModel, Field


class WaitingListEntry(BaseModel):
    external_id: str
    date_of_birth: date  # Note: rounded to the first of the month.
    groups_of_interest: list[str]
    postcode: str | None
    joined_waiting_list_at: datetime
    successfully_transferred: bool


class AirTableWaitingListEntryFields(BaseModel):
    date_of_birth: date = Field(alias="D.O.B.")
    which_group_would_you_like_to_join: list[str] = Field(alias="Which group would you like to join", default=[])
    postcode: str | None = Field(alias="Postcode", default=None)
    created: datetime = Field(alias="Created")
    fourteen_wl_start_date: date | None = Field(alias="14th WL: Joined List", default=None)
    transfered_to: str | None = Field(alias="Transfered to", default=None)


class AirTableWaitingListRecord(BaseModel):
    id: str
    fields: AirTableWaitingListEntryFields
    created_time: datetime = Field(alias="createdTime")

    def to_waiting_list_entry(self) -> WaitingListEntry:
        # Convert date to datetime if fourteen_wl_start_date is used
        if self.fields.fourteen_wl_start_date is not None:
            joined_at = datetime.combine(self.fields.fourteen_wl_start_date, datetime.min.time())
        else:
            joined_at = self.created_time

        return WaitingListEntry(
            external_id=self.id,
            date_of_birth=self.fields.date_of_birth.replace(day=1),
            groups_of_interest=self.fields.which_group_would_you_like_to_join,
            postcode=self.fields.postcode,
            joined_waiting_list_at=joined_at,
            successfully_transferred=bool(self.fields.transfered_to),
        )


class AirTableWaitingListResponse(BaseModel):
    records: list[AirTableWaitingListRecord]
    offset: str | None = Field(alias="offset", default=None)


class AirTableClient:
    # Airtable API rate limit: 4 requests per second
    _MIN_REQUEST_INTERVAL = 0.25  # 250ms = 1/4 second

    def __init__(self, api_key: str, base_id: str, table_id: str) -> None:
        self.api_key = api_key
        self.base_id = base_id
        self.table_id = table_id
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
            }
        )
        self._last_request_time: float | None = None

    def _get_page(self, offset: str | None = None) -> AirTableWaitingListResponse:
        # Rate limiting: ensure at least 250ms between requests
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._MIN_REQUEST_INTERVAL:
                time.sleep(self._MIN_REQUEST_INTERVAL - elapsed)

        url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_id}"
        if offset is not None:
            url += f"?offset={offset}"
        response = self.session.get(url)
        response.raise_for_status()
        self._last_request_time = time.time()
        return AirTableWaitingListResponse.model_validate(response.json())

    def get_waiting_list(self) -> list[WaitingListEntry]:
        all_records = []
        offset = None
        while True:
            response = self._get_page(offset)
            all_records.extend(response.records)
            offset = response.offset
            if offset is None:
                break
        return [record.to_waiting_list_entry() for record in all_records]
