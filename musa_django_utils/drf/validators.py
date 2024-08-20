from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.utils.representation import smart_repr


class NoAcceptSpace:

    def __call__(self, value):
        if ' ' in value:
            raise ValidationError(_('This field cannot contain spaces'))


class DependsAnotherField:
    """
        Validator to check multiple fields

        use if have not required fields, but if one present, required another(s) fields
        ex: edit password in account serializer, have specs bellow:
            - password and old_password is not required
            - but if password is present, old_password is required
            - and if old_password is present, password is required
    """
    message = _('This field is required.')

    def __init__(self, fields, message=None):
        self.fields = fields
        self.message = message or self.message

    def __call__(self, attrs):
        missing_items = {
            field_name: self.message
            for field_name in self.fields
            if field_name not in attrs.keys()
        }
        if missing_items and len(missing_items.keys()) != len(self.fields):
            raise ValidationError(missing_items, code='required')

    def __repr__(self):
        return f'<{self.__class__.__name__}(fields={smart_repr(self.fields)})>'
