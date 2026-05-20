from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class LengthValidator:
    def __init__(self, length, operation='min'):
        assert operation in ('min', 'max', 'exact', 'in_list'), "operation must be 'min', 'max', 'exact', or 'in_list'."
        if operation == 'in_list':
            if not isinstance(length, (list, tuple)):
                raise ValueError("length must be a list or tuple of positive integers when operation is 'in_list'.")
        elif not isinstance(length, int) or length < 1:
            raise ValueError("length must be a positive integer.")
        self.length = length
        self.operation = operation

    def __call__(self, value):
        if self.operation == 'in_list':
            if len(value) not in self.length:
                raise ValidationError(
                    _("Length must be one of %(length)s characters.") % {'length': self.length}
                )
        elif self.operation == 'min' and len(value) < self.length:
            raise ValidationError(
                _("Length must be at least %(length)s characters.") % {'length': self.length}
            )
        elif self.operation == 'max' and len(value) > self.length:
            raise ValidationError(
                _("Length must be no more than %(length)s characters.") % {'length': self.length}
            )
        elif self.operation == 'exact' and len(value) != self.length:
            raise ValidationError(
                _("Length must be exactly %(length)s characters.") % {'length': self.length}
            )
