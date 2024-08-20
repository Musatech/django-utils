from django.conf import settings


class MultiProviderMixin:
    config_name = None
    provider_header = 'Authorization-Provider'
    authentication_in = 'headers'
    authentication_field = 'Authorization'

    def __init__(self) -> None:
        super().__init__()
        self.config = self.mount_config()

    def mount_config(self):
        try:
            config = settings.AUTH_CONFIG[self.config_name]
        except AttributeError:
            raise Exception('You need to declare `AUTH_CONFIG` in settings')
        except KeyError:
            raise Exception(f'`{self.config_name}` is not present in `AUTH_CONFIG`')

        return config

    def get_config(self, key, default=None):
        return self.config.get(key, default)

    def validate_provider(self, request):
        provider_value = self.config.get('PROVIDER_HEADER_VALUE')
        if provider_value:
            provider = self.config.get('PROVIDER_HEADER', self.provider_header)
            return request.headers[provider] == provider

        return True

    def get_token(self, request):
        find_in = self.config.get('AUTHENTICATION_IN', self.authentication_in)
        field_name = self.config.get('AUTHENTICATION_FIELD', self.authentication_field)
        return getattr(request, find_in, {}).get(field_name, '')
