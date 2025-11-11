from rest_framework import serializers


class BooleanMonthDayField(serializers.Field):

    def to_internal_value(self, data: list[int]):
        """
        convert a list of int (month days) to a list of booleans (length 31).
        Ex: [1, 3] -> [True, False, True, False, False, .., False]
        """
        if not isinstance(data, list):
            raise serializers.ValidationError("The value must be a list of integers.")

        bool_days = [False] * 31
        for day in data:
            bool_days[day - 1] = True
        return bool_days

    def to_representation(self, value: list[bool]):
        """
        Convert a list of booleans (length 31)
        to a list of strings with the corresponding days set to True.
        Example: [True, False, True, False, False, False, False] -> [1, 3]
        """
        if isinstance(value, (list, tuple)) and len(value) == 31:
            return [i + 1 for i, flag in enumerate(value) if flag]
        return []
