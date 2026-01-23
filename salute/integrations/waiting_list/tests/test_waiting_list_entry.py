import datetime
from zoneinfo import ZoneInfo

import pytest
import time_machine

from salute.integrations.waiting_list.factories import WaitingListEntryFactory
from salute.integrations.waiting_list.models import WaitingListEntry


@pytest.mark.django_db
class TestWaitingListEntry:
    @time_machine.travel("2022-01-01")
    def test_with_age(self) -> None:
        WaitingListEntryFactory(date_of_birth=datetime.date(2020, 1, 1))
        entry = WaitingListEntry.objects.with_age(
            datetime.datetime(2022, 1, 1, tzinfo=ZoneInfo("Europe/London"))
        ).first()
        assert entry is not None
        assert entry.age == datetime.timedelta(days=731)

    @pytest.mark.parametrize(
        "date_of_birth, expected_target_section",
        [
            (datetime.date(2020, 1, 1), "TOO_YOUNG"),  # Age 2
            (datetime.date(2016, 1, 1), "BEAVERS"),  # Age 6
            (datetime.date(2013, 1, 1), "CUBS"),  # Age 9
            (datetime.date(2010, 4, 1), "SCOUTS"),  # Age 12ish
            (datetime.date(2007, 1, 1), "EXPLORERS"),  # Age 15
            (datetime.date(2003, 1, 1), "NETWORK"),  # Age 19
            (datetime.date(1996, 1, 1), "TOO_OLD"),  # Age 26
        ],
    )
    def test_with_target_section(self, date_of_birth: datetime.date, expected_target_section: str) -> None:
        WaitingListEntryFactory(date_of_birth=date_of_birth)
        entry = WaitingListEntry.objects.with_target_section(
            datetime.datetime(2022, 1, 1, tzinfo=ZoneInfo("Europe/London"))
        ).first()
        assert entry is not None
        assert entry.target_section == expected_target_section
