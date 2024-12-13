
from django.utils.translation import gettext_lazy as _

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class BaseRemoteAuthScheme(OpenApiAuthenticationExtension):  # pragma: no cover
    target_class = 'musa_django_utils.drf.authentication.oauth.BaseOauthAuthentication'
    name = 'Bearer Token Authentication'
    priority = 0
    match_subclasses = True

    def __init__(self, target):
        super().__init__(target)
        self.name = getattr(self.target, 'name', self.name)

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'Authorization',
            'bearerFormat': 'JWT',
            # 'description': _('Token-based authentication')
        }
