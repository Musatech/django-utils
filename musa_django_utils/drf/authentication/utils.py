from json import loads
from urllib.request import urlopen


def get_well_know_keys(jwk_url):
    try:
        data = urlopen(jwk_url).read()
        return loads(data)['keys']
    except Exception as err:
        raise Exception('Cannot get well-know, check config and `JWK_URL` url') from err
