from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class BooleanWeekDayField(serializers.Field):
    WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    def to_internal_value(self, data: list[str]):
        """
        convert a list of strings (weekdays) to a list of booleans (length 7).
        Ex: ["mon", "wed"] -> [True, False, True, False, False, False, False]
        """
        if not isinstance(data, list):
            raise serializers.ValidationError(_("Must be a list of strings."))

        bool_days = [False] * 7
        for day in data:
            if day[:3] not in self.WEEKDAYS:
                raise serializers.ValidationError(_("Invalid day: {day}"))

            bool_days[self.WEEKDAYS.index(day[:3])] = True
        return bool_days

    def to_representation(self, value: list[bool]):
        """
        Convert a list of booleans (length 7)
        to a list of strings with the corresponding days set to True.
        Example: [True, False, True, False, False, False, False] -> ["mon", "wed"]
        """
        if isinstance(value, (list, tuple)) and len(value) == 7:
            return [day for day, flag in zip(self.WEEKDAYS, value) if flag]
        return []
