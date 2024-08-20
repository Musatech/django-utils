from base64 import urlsafe_b64decode, urlsafe_b64encode
from time import time
from zlib import decompress

from django.conf import settings
from django.core.signing import JSONSerializer
from django.utils.baseconv import base64
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.translation import gettext_lazy as _

from rest_framework import authentication, exceptions

from .base import MultiProviderMixin

try:
    from .drf_spetacular import *  # noqa this don`t broke app`s without drf-spectacular
except ModuleNotFoundError:
    pass


class BaseDecodeToken:
    """"
        methods copied from django 2.2 => django.core.signing
    """

    def b64_decode(self, value):
        pad = b'=' * (-len(value) % 4)
        return urlsafe_b64decode(value + pad)

    def b64_encode(self, value):
        return urlsafe_b64encode(value).strip(b'=')

    def base64_hmac(self, salt, value, key):
        return self.b64_encode(salted_hmac(salt, value, key).digest()).decode()

    def signature(self, value, secret):
        salt = 'django.contrib.sessions.backends.signed_cookies'
        return self.base64_hmac(salt + 'signer', value, secret)

    def decode_key(self, key):
        if key[0] == '.':
            key = key[1:].encode()
            return decompress(self.b64_decode(key))

        return self.b64_decode(key.encode())


class OldDjangoCookieSessionAuthentication(MultiProviderMixin, authentication.BaseAuthentication, BaseDecodeToken):
    authentication_in = 'cookies'
    authentication_field = settings.SESSION_COOKIE_NAME

    def get_user(self, request, session_data):
        raise NotImplementedError('You need to create your `get_user`')

    def authenticate(self, request):
        token = self.get_token(request)
        if not token or not self.validate_provider(request):
            return None

        try:
            value, timestamp = token.rsplit(':', 1)
            assert time() - base64.decode(timestamp) <= self.get_config('COOKIE_AGE', settings.SESSION_COOKIE_AGE)

            secret = self.get_config('SECRET_KEY', settings.SECRET_KEY)
            assert constant_time_compare(timestamp, self.signature(value, secret))

            session_data = JSONSerializer().loads(self.decode_key(value))
            user = self.get_user(request, session_data)
        except Exception:
            raise exceptions.AuthenticationFailed(_('invalid or expired session'))

        return (user, None)
