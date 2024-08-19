from django.conf import settings
from django.utils.translation import gettext_lazy as _

from django_restql.mixins import DynamicFieldsMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 999
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'pagination': {
                'page': self.page.number,
                'last_page': self.page.paginator.num_pages,
                'page_size': self.page.paginator.per_page,
                'count': self.page.paginator.count,
            },
            'results': data
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'pagination': {
                    'type': 'object',
                    'properties': {
                        'page': {'type': 'integer', 'example': 1},
                        'last_page': {'type': 'integer', 'example': 5},
                        'page_size': {'type': 'integer', 'example': 25},
                        'count': {'type': 'integer', 'example': 123},
                    }
                },
                'results': schema,
            },
        }

    @staticmethod
    def get_filter_desc():
        return _("""Use to filter fields in response (for fast response and low data consumption).

You can specify fields to show using his name ex: `?fields={fieldName}` and `?fields={fieldName, field2Name}`, to
exclude some fields, you can put `-` before a name, ex: `?fields={-fieldName}` and `?fields={-fieldName, -field2Name}`,
works in nested data: `?fields={fieldNested{id}}`
""")

    def get_schema_operation_parameters(self, view):
        parameters = super().get_schema_operation_parameters(view)

        # add default page_size to documentation
        result = list(filter(lambda x: (x['name'] == self.page_size_query_param), parameters))
        if len(result) > 0:
            result[0]['schema']['default'] = self.page_size

        if view.serializer_class and issubclass(view.serializer_class, DynamicFieldsMixin):
            # add fields filter to documentation
            parameters.append(
                {
                    'name': settings.RESTQL['QUERY_PARAM_NAME'],
                    'required': False,
                    'in': 'query',
                    'description': self.get_filter_desc(),
                    'schema': {
                        'type': 'string',
                    },
                },
            )

        return parameters
