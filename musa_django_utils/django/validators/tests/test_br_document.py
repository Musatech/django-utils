import pytest
from django.core.exceptions import ValidationError

from musa_django_utils.django.validators.br_document import (
    CNPJValidator,
    CPFCNPJValidator,
    CPFValidator,
    _strip_document,
)


class TestStripDocument:
    def test_removes_formatting(self):
        assert _strip_document("12.345.678/0001-99") == "12345678000199"

    def test_uppercases_letters(self):
        assert _strip_document("ab.cde.fgh/ijkl-12") == "ABCDEFGHIJKL12"

    def test_preserves_letters_and_digits(self):
        assert _strip_document("1B.2C3.D4E/F5G6-78") == "1B2C3D4EF5G678"

    def test_removes_spaces(self):
        assert _strip_document("12 345 678 0001 99") == "123456780001" + "99"


class TestCPFCNPJValidator:
    def test_valid_cpf(self):
        CPFCNPJValidator()("529.982.247-25")

    def test_valid_numeric_cnpj(self):
        CPFCNPJValidator()("11.222.333/0001-81")

    def test_valid_alphanumeric_cnpj(self):
        # 12 alphanumeric base chars + 2 numeric check digits
        # Using a known-valid alphanumeric CNPJ for testing
        validator = CPFCNPJValidator()
        # Build a valid one programmatically
        base = "1B2C3D4EF5G6"
        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_2 = [6] + pesos_1

        def char_value(c):
            return ord(c) - 48

        def calc_digit(cnpj, pesos):
            soma = sum(char_value(cnpj[i]) * pesos[i] for i in range(len(pesos)))
            d = 11 - (soma % 11)
            return 0 if d >= 10 else d

        d1 = calc_digit(base, pesos_1)
        d2 = calc_digit(base + str(d1), pesos_2)
        valid_cnpj = f"{base}{d1}{d2}"
        validator(valid_cnpj)

    def test_invalid_cpf_raises(self):
        with pytest.raises(ValidationError):
            CPFCNPJValidator()("111.111.111-11")

    def test_invalid_cnpj_raises(self):
        with pytest.raises(ValidationError):
            CPFCNPJValidator()("11.222.333/0001-00")

    def test_all_same_cnpj_raises(self):
        with pytest.raises(ValidationError):
            CPFCNPJValidator()("11111111111111")

    def test_lowercase_input_accepted(self):
        # lowercase letters should be normalized before validation
        validator = CPFCNPJValidator()
        base = "1b2c3d4ef5g6"
        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_2 = [6] + pesos_1

        base_upper = base.upper()

        def calc_digit(cnpj, pesos):
            soma = sum((ord(cnpj[i]) - 48) * pesos[i] for i in range(len(pesos)))
            d = 11 - (soma % 11)
            return 0 if d >= 10 else d

        d1 = calc_digit(base_upper, pesos_1)
        d2 = calc_digit(base_upper + str(d1), pesos_2)
        validator(f"{base}{d1}{d2}")

    def test_invalid_length_raises(self):
        with pytest.raises(ValidationError):
            CPFCNPJValidator()("123")


class TestCPFValidator:
    def test_valid_cpf(self):
        CPFValidator()("529.982.247-25")

    def test_cnpj_raises(self):
        with pytest.raises(ValidationError):
            CPFValidator()("11.222.333/0001-81")


class TestCNPJValidator:
    def test_valid_numeric_cnpj(self):
        CNPJValidator()("11.222.333/0001-81")

    def test_cpf_raises(self):
        with pytest.raises(ValidationError):
            CNPJValidator()("529.982.247-25")


class TestCNPJValidatorRealCases:
    @pytest.mark.parametrize(
        "cnpj",
        [
            "36.568.736/0001-08",
            "24.854.328/0001-33",
            "08.471.615/0001-08",
            "28.950.187/0001-03",
            "79.993.202/0001-31",
            "36.568.736/8115-05",
            "36.568.736/0352-46",
        ],
    )
    def test_valid_numeric_cnpjs(self, cnpj):
        CNPJValidator()(cnpj)

    @pytest.mark.parametrize(
        "cnpj",
        [
            "NH.XSM.ZJ6/0001-19",
            "P3.L4Z.858/0001-16",
            "YT.9C8.CPE/0001-00",
            "G0.7DN.HZS/0001-03",
            "SN.CH5.JGR/0001-35",
        ],
    )
    def test_valid_alphanumeric_cnpjs(self, cnpj):
        CNPJValidator()(cnpj)
