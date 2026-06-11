from django.db.models import CharField

from ..validators import CPFCNPJValidator
from ..validators.br_document import _strip_document


class CPFCNPJField(CharField):
    description = "Field to store Brazilian CPF or CNPJ numbers"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 18  # Maximum length for formatted CNPJ
        super().__init__(*args, **kwargs)
        self.validators.append(CPFCNPJValidator())

    def to_python(self, value):
        if value is None:
            return value
        return _strip_document(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        return _strip_document(value)
