from datetime import time
from typing import Any

from django import forms
from django.contrib.postgres.fields.ranges import Range, RangeField  # type: ignore[attr-defined]
from django.contrib.postgres.forms import BaseRangeField, RangeWidget
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.fields import TimeField


class TimeRange(Range):
    base_type = time


class TimeRangeFormField(BaseRangeField):
    """
    A form field to handle TimeRange input.
    """

    base_field = forms.TimeField
    range_type = TimeRange
    widget = RangeWidget(forms.TimeInput)

    def __init__(self, *, required: bool = False, **kwargs: Any) -> None:
        super().__init__(required=required, **kwargs)

    def clean(self, value: TimeRange) -> TimeRange:
        value = super().clean(value)

        if value is None:
            if self.required:
                raise forms.ValidationError("This field is required.")
            return value

        if (value.lower is None) ^ (value.upper is None):
            raise forms.ValidationError(
                "Both the start and end times must be provided to create a valid time range.",
            )

        start_time = value.lower
        end_time = value.upper

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("The start time must be before the end time.")
        return value


class TimeRangeField(RangeField):
    """
    A custom RangeField for our custom PostgreSQL 'timerange' type.
    """

    base_field = TimeField
    form_field = TimeRangeFormField
    range_type = TimeRange

    def db_type(self, connection: BaseDatabaseWrapper) -> str:
        return "timerange"
