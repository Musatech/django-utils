from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class MonthDaysField(ArrayField):
    def __init__(self, *args, **kwargs):
        kwargs.pop("base_field", None)
        kwargs["size"] = 31
        super().__init__(models.BooleanField(), *args, **kwargs)

    def _normalize(self, value):
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

        raise ValidationError(_("Invalid format for month_days"))

    def get_db_prep_value(self, value, connection, prepared=False):
        value = self._normalize(value)
        return super().get_db_prep_value(value, connection, prepared=prepared)
