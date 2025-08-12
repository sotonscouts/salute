import json
from decimal import Decimal

import pytest
from django.db import connection


@pytest.mark.django_db
class TestPostgresFunctionJSumByRegexKey:
    def _call(self, data: dict, regex: str) -> int:
        if connection.vendor != "postgresql":
            pytest.skip("Tests require PostgreSQL for custom SQL functions")
        with connection.cursor() as cursor:
            cursor.execute("SELECT j_sum_by_regex_key(%s::jsonb, %s)", [json.dumps(data), regex])
            row = cursor.fetchone()
            assert row is not None
            return int(row[0])

    def test_basic_sum_of_matching_keys(self) -> None:
        data = {"a_1": "1", "a_2": "2", "b_1": "10"}
        assert self._call(data, r"^a_[0-9]$") == 3

    def test_returns_zero_when_no_keys_match(self) -> None:
        data = {"x": "5", "y": "7"}
        assert self._call(data, r"^nope$") == 0

    def test_empty_object_returns_zero(self) -> None:
        assert self._call({}, r".*") == 0

    def test_nested_objects_are_ignored_top_level_only(self) -> None:
        data = {"a_1": "3", "nested": {"a_2": "4"}}
        # Only top-level keys are considered, so nested.a_2 should be ignored
        assert self._call(data, r"^a_[0-9]$") == 3

    def test_non_integer_values_in_non_matching_keys_do_not_error(self) -> None:
        data = {"foo": "bar", "y_1_m": "2", "y_2_f": "3"}
        # Only y_* keys match; "foo": "bar" should not be cast and thus not error
        assert self._call(data, r"^y_[0-9]+_(m|f)$") == 5

    def test_ignores_non_numeric_values_for_matching_keys(self) -> None:
        data = {"y_1_m": "2", "y_2_f": "NaN", "y_3_m": "", "y_4_m": "7"}
        # Only numeric values should be summed -> 2 + 7 = 9
        assert self._call(data, r"^y_[0-9]+_(m|f)$") == 9

    def test_regex_used_in_app_for_young_people(self) -> None:
        # Mirrors the regex used in TOTAL_YOUNG_PEOPLE_EXPR: ^y_[0-9]+_(m|f|p|s)$
        data = {
            "y_4_m": "7",
            "y_4_f": "6",
            "y_4_p": "1",
            "y_4_s": "0",
            # Should not match different suffix
            "y_4_x": "9",
            # Should not match volunteers pattern
            "l_leaders_m": "5",
        }
        assert self._call(data, r"^y_[0-9]+_(m|f|p|s)$") == 14

    def test_regex_used_in_app_for_volunteers(self) -> None:
        # Mirrors the regex used in TOTAL_VOLUNTEERS_EXPR: ^l_[a-z]+_(m|f|p|s|xm|xf|xp|xs)$
        data = {
            "l_leaders_m": "5",
            "l_leaders_f": "4",
            "l_helpers_p": "2",
            "l_helpers_s": "1",
            "l_youngleaders_xm": "3",
            "l_youngleaders_xf": "2",
            "l_youngleaders_xp": "1",
            "l_youngleaders_xs": "0",
            # Should not match
            "y_4_m": "7",
            "l_99": "100",  # wrong pattern
        }
        assert self._call(data, r"^l_[a-z]+_(m|f|p|s|xm|xf|xp|xs)$") == 18


@pytest.mark.django_db
class TestPostgresFunctionRatio:
    def _call(self, n: int, d: int) -> Decimal:
        if connection.vendor != "postgresql":
            pytest.skip("Tests require PostgreSQL for custom SQL functions")
        with connection.cursor() as cursor:
            cursor.execute("SELECT ratio(%s, %s)", [n, d])
            row = cursor.fetchone()
            assert row is not None
            # psycopg returns Decimal for numeric
            return row[0]

    def test_regular_division_rounded_to_2dp(self) -> None:
        # 1 / 3 = 0.333.. -> 0.33
        assert self._call(1, 3) == Decimal("0.33")
        # 2 / 3 = 0.666.. -> 0.67
        assert self._call(2, 3) == Decimal("0.67")

    def test_zero_denominator_returns_zero(self) -> None:
        assert self._call(5, 0) == Decimal("0")

    def test_zero_numerator_returns_zero(self) -> None:
        assert self._call(0, 10) == Decimal("0")

    def test_negative_values(self) -> None:
        assert self._call(-1, 2) == Decimal("-0.5")
        assert self._call(1, -2) == Decimal("-0.5")
        assert self._call(-1, -2) == Decimal("0.5")
