import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


def _strip_document(value: str) -> str:
    """Remove formatting characters, preserve alphanumeric, uppercase."""
    return re.sub(r"[^A-Z0-9]", "", value.upper())


@deconstructible
class CPFCNPJValidator:
    code = "invalid_document"
    message = _("Invalid document number. Must be a valid CPF or CNPJ.")
    accept_cnpj = True
    accept_cpf = True

    def __call__(self, value):
        value = _strip_document(value)

        if len(value) == 11 and value.isdigit() and self.accept_cpf:
            if not self._is_valid_cpf(value):
                raise ValidationError(self.message, code=self.code)

        elif len(value) == 14 and self.accept_cnpj:
            if not self._is_valid_cnpj(value):
                raise ValidationError(self.message, code=self.code)

        else:
            raise ValidationError(self.message, code=self.code)

    def _is_valid_cpf(self, cpf):
        if cpf == cpf[0] * 11:
            return False

        for i in range(9, 11):
            soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
            digito = ((soma * 10) % 11) % 10
            if digito != int(cpf[i]):
                return False
        return True

    @staticmethod
    def _char_value(c: str) -> int:
        """0-9 → 0-9; A-Z → 17-42 (IN RFB 2229/2024: ord(c) - 48)."""
        return ord(c) - 48

    def _is_valid_cnpj(self, cnpj):
        if len(set(cnpj)) == 1:
            return False

        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_2 = [6] + pesos_1

        for pesos in (pesos_1, pesos_2):
            soma = sum(self._char_value(cnpj[i]) * pesos[i] for i in range(len(pesos)))
            digito = 11 - (soma % 11)
            digito = 0 if digito >= 10 else digito
            if digito != int(cnpj[len(pesos)]):
                return False
        return True


@deconstructible
class CPFValidator(CPFCNPJValidator):
    message = _("Invalid document number. Must be a valid CPF.")
    accept_cnpj = False


@deconstructible
class CNPJValidator(CPFCNPJValidator):
    message = _("Invalid document number. Must be a valid CNPJ.")
    accept_cpf = False
