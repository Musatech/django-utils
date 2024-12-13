import re
from json import dumps

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from jwt import decode, get_unverified_header
from jwt.algorithms import ECAlgorithm, RSAAlgorithm
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .utils import get_well_know_keys


class BaseOauthAuthentication(BaseAuthentication):
    keyword = 'Bearer'
    issuers = [
        'https://cognito-idp.*.amazonaws.com/.*'
    ]
    jwk_urls = [
        ('https://cognito-idp.*.amazonaws.com.*', '/.well-known/jwks.json'),
    ]

    def get_well_know_key(self, iss, kid):
        if 'JWK' not in settings.REST_FRAMEWORK:
            settings.REST_FRAMEWORK['JWK'] = []

        elif iss not in settings.REST_FRAMEWORK['JWK']:
            for pattern, url in self.jwk_urls:
                if re.match(pattern, iss):
                    settings.REST_FRAMEWORK['JWK'] = {iss: get_well_know_keys(f'{iss}{url}')}
                    break

        return [key for key in settings.REST_FRAMEWORK['JWK'][iss] if key['kid'] == kid][0]

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        try:
            data = decode(auth[1], algorithms=['RS256', 'ES256'], options={"verify_signature": False})
            if not re.match('(%s)' % '|'.join(self.issuers), data['iss']):
                raise Exception()

            header = get_unverified_header(auth[1])

            key = self.get_well_know_key(data['iss'], header['kid'])
            if key['alg'].startswith('RS'):
                public_key = RSAAlgorithm.from_jwk(dumps(key))
            elif key['alg'].startswith('ES'):
                public_key = ECAlgorithm.from_jwk(dumps(key))
            else:
                raise Exception()

            decode(auth[1], public_key, algorithms=['RS256', 'ES256'], options={'verify_aud': False})
            user = self.get_user(request, data)
        except NotImplementedError as err:
            raise err
        except Exception:
            raise AuthenticationFailed(_('invalid or expired token'))

        return (user, None)

    def get_user(self, request, token_data):
        raise NotImplementedError('You need to create `get_user`')
