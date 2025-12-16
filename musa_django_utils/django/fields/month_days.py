from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models


class MonthDaysField(ArrayField):
    def __init__(self, *args, **kwargs):
        kwargs["size"] = 31
        super().__init__(models.BooleanField(), *args, **kwargs)

    def to_python(self, value):
        if value is None:
            return value

        if isinstance(value, list):
            if len(value) == 31 and all(isinstance(v, (bool, int)) for v in value):
                return [bool(v) for v in value]

            if set(value).issubset(set(range(1, 32))):
                days = [False] * 31
                for day in value:
                    days[day - 1] = True
                return days

        raise ValidationError("Invalid format for month_days")
