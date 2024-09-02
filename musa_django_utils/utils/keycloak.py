from datetime import datetime, timedelta

from requests import post


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class KeyCloakAppAuth(metaclass=Singleton):
    _token = None
    _expires = datetime.min

    def __init__(self, **kwargs) -> None:
        self.keycloak_url = kwargs.get('keycloak_base_url') or kwargs.get('KEYCLOAK_BASE_URL')
        self.realm = kwargs.get('realm') or kwargs.get('REALM')
        self.client_id = kwargs.get('client_id') or kwargs.get('CLIENT_ID')
        self.client_secret = kwargs.get('client_secret') or kwargs.get('CLIENT_SECRET')

    def renew_token(self):
        url = f'{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token'
        data = {"grant_type":  "client_credentials", "client_id": self.client_id, "client_secret": self.client_secret}
        res = post(url, data=data, timeout=5).json()
        self._token = res['access_token']
        self._expires = datetime.now() + timedelta(seconds=res['expires_in'] - 20)

    @property
    def token(self):
        if self._expires < datetime.now():
            self.renew_token()
        return self._token
