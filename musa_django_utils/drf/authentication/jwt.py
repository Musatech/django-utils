from json import dumps

from django.utils.translation import gettext_lazy as _

from jwt import decode, get_unverified_header
from jwt.algorithms import ECAlgorithm, RSAAlgorithm
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .base import MultiProviderMixin
from .utils import get_well_know_keys

try:
    from .drf_spetacular import *  # noqa this don`t broke app`s without drf-spectacular
except ModuleNotFoundError:
    pass


class JwtAuthentication(MultiProviderMixin, BaseAuthentication):

    def get_well_know_key(self, kid):
        jwk_url = self.get_config('JWK_URL')
        if 'KEYS' not in self.config and not jwk_url:
            raise Exception(f'`JWK_URL` is not present in `{self.config_name}`')

        elif 'KEYS' not in self.config:
            self.config['KEYS'] = get_well_know_keys(self.get_config('JWK_URL'))

        return [key for key in self.config['KEYS'] if key['kid'] == kid][0]

    def get_user(self, request, token_data):
        raise NotImplementedError('You need to create `get_user`')

    def authenticate(self, request):
        token = self.get_token(request).split()
        if not token or not self.validate_provider(request):
            return None

        if len(token) != 2 or token[0] != self.get_config('KEYWORD', 'Bearer'):
            raise AuthenticationFailed(_('Invalid token header'))

        try:
            header = get_unverified_header(token[1])
            key = self.get_well_know_key(header['kid'])

            if key['alg'].startswith('RS'):
                public_key = RSAAlgorithm.from_jwk(dumps(key))
            elif key['alg'].startswith('ES'):
                public_key = ECAlgorithm.from_jwk(dumps(key))
            else:
                raise Exception()

            data = decode(token[1], public_key, algorithms=['RS256', 'ES256'], options={'verify_aud': False})
            user = self.get_user(request, data)
        except NotImplementedError as err:
            raise err
        except Exception:
            raise AuthenticationFailed(_('invalid or expired token'))

        return (user, None)
