from rest_framework import serializers

from musa_django_utils.django.validators import CPFCNPJValidator
from musa_django_utils.django.validators.br_document import _strip_document


class CPFCNPJSerializerField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(CPFCNPJValidator())

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return _strip_document(value)
