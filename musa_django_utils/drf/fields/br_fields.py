import re

from rest_framework import serializers

from musa_django_utils.django.validators import CPFCNPJValidator


class CPFCNPJSerializerField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(CPFCNPJValidator())

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return re.sub(r'\D', '', value)
