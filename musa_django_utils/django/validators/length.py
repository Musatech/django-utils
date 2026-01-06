from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class LengthValidator:
    def __init__(self, allowed_lengths):
        if not isinstance(allowed_lengths, (list, tuple, set)):
            raise ValueError("allowed_lengths must be a list, tuple, or set of integers.")
        self.allowed_lengths = allowed_lengths

    def __call__(self, value):
        if len(value) not in self.allowed_lengths:
            raise ValidationError(
                _(f"Length must be one of {self.allowed_lengths} characters.")
            )
