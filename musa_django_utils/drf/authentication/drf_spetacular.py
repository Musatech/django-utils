
from django.utils.translation import gettext_lazy as _

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class BaseRemoteAuthScheme(OpenApiAuthenticationExtension):  # pragma: no cover
    target_class = 'musa_django_utils.drf.authentication.jwt.JwtAuthentication'
    name = 'Bearer Token Authentication'
    priority = 0
    match_subclasses = True

    def __init__(self, target):
        super().__init__(target)
        self.name = getattr(self.target, 'name', self.name)

    def get_security_definition(self, auto_schema):
        data = {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'Authorization',
            'bearerFormat': 'JWT',
            # 'description': _('Token-based authentication')
        }
        if provider := self.target.get_provider_header_value():
            field_name = self.target.get_provider_header()
            data['description'] = _(f'You need to set a `{field_name}` with a value `{provider}` in header')

        return data


class WmsCookieAuthScheme(OpenApiAuthenticationExtension):  # pragma: no cover
    target_class = 'musa_django_utils.drf.authentication.old_django.OldDjangoCookieSessionAuthentication'
    name = 'Django Session Cookie Authentication'
    priority = 0

    def __init__(self, target):
        super().__init__(target)
        self.name = getattr(self.target, 'name', self.name)

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': self.target.cookie_name,
            'description': _('Use WMS Cookie-based session authentication')
        }
