import pytest
from phonenumber_field.phonenumber import PhoneNumber

from salute.people.utils import format_phone_number


class TestFormatPhoneNumber:
    @pytest.mark.parametrize(
        "phone_number, expected",
        [
            ("+441234567890", "01234 567890"),  # UK number
            ("+442380123456", "023 8012 3456"),  # Another UK number format
            ("+12121231234", "+1 212-123-1234"),  # Non-UK number
        ],
    )
    def test_format_phone_number(self, phone_number: str, expected: str) -> None:
        formatted = format_phone_number(PhoneNumber.from_string(phone_number, region="GB"))
        assert formatted == expected

    def test_none_phone_number(self) -> None:
        formatted = format_phone_number(None)
        assert formatted is None
