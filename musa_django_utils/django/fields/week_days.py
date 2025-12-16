from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models


class WeekDaysField(ArrayField):
    WEEKDAY_INDEX = {
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6,
    }

    def __init__(self, *args, **kwargs):
        kwargs["size"] = 7
        super().__init__(models.BooleanField(), *args, **kwargs)

    def to_python(self, value):
        if value is None:
            return value

        if isinstance(value, list):
            if len(value) == 7 and all(isinstance(v, (bool, int)) for v in value):
                return [bool(v) for v in value]

            if set(value).issubset(set(self.WEEKDAY_INDEX.keys())):
                return [day in value for day in self.WEEKDAY_INDEX]

        raise ValidationError("Invalid format for week_days")
