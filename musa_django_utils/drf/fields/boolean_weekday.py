from rest_framework import serializers


class BooleanWeekdayField(serializers.Field):
    WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    def to_internal_value(self, data):
        # Normalize input (e.g. "monday" → "mon")
        data = data.strip().lower()[:3]
        if data not in self.WEEKDAYS:
            raise serializers.ValidationError(f"Invalid weekday '{data}'.")

        # Create boolean list
        return [day == data for day in self.WEEKDAYS]

    def to_representation(self, value):
        # Optional: reverse transform list → name
        try:
            index = value.index(True)
            return self.WEEKDAYS[index]
        except ValueError:
            return None
