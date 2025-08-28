from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.response import Response


class HybridPagination(PageNumberPagination):
    """
    Accepts:
      - Page-number: ?page=2 [&page_size=20]
      - Limit/offset: ?limit=20&offset=40
      - Optional override: ?pagination=page | offset
    """
    # page-number defaults
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 999

    # limit/offset defaults
    default_limit = 25
    max_limit = 999
    limit_query_param = 'limit'
    offset_query_param = 'offset'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # a real instance for offset/limit when needed
        self._offset_paginator = LimitOffsetPagination()
        self._offset_paginator.default_limit = self.default_limit
        self._offset_paginator.max_limit = self.max_limit
        self._offset_paginator.limit_query_param = self.limit_query_param
        self._offset_paginator.offset_query_param = self.offset_query_param

        self._mode = 'page'  # set per-request in paginate_queryset
        self._active_paginator = None
        self._count = None  # unify count access

    def _select_mode(self, request):
        forced = request.query_params.get('pagination')
        if forced in ('page', 'offset'):
            return forced
        # auto-detect by params
        qp = request.query_params
        if self.limit_query_param in qp or self.offset_query_param in qp:
            return 'offset'
        return 'page' if 'page' in qp or 'page_size' in qp else 'page'

    # ---- main DRF hooks ----
    def paginate_queryset(self, queryset, request, view=None):
        self._mode = self._select_mode(request)
        if self._mode == 'offset':
            self._active_paginator = self._offset_paginator
        else:
            self._active_paginator = self  # use PageNumberPagination methods

        if self._mode == 'offset':
            page = self._offset_paginator.paginate_queryset(queryset, request, view=view)
            # capture unified count
            self._count = getattr(self._offset_paginator, 'count', None)
            return page
        else:
            page = super().paginate_queryset(queryset, request, view=view)
            self._count = getattr(self, 'page', None).paginator.count if getattr(self, 'page', None) else None
            return page

    def get_paginated_response(self, data):
        # Delegate to active paginator to keep response shapes familiar
        resp = self._active_paginator.get_paginated_response(data)
        # Optionally annotate which mode was used
        resp.data['pagination_mode'] = self._mode
        return resp

    # ---- OpenAPI / schema (adds both sets of params) ----
    def get_schema_operation_parameters(self, view):
        # Parameters from both paginators
        page_params = [
            {
                "name": "page",
                "required": False,
                "in": "query",
                "description": "Page number (page-number pagination).",
                "schema": {"type": "integer", "minimum": 1},
            },
            {
                "name": self.page_size_query_param,
                "required": False,
                "in": "query",
                "description": "Page size (page-number pagination).",
                "schema": {"type": "integer", "minimum": 1, "maximum": self.max_page_size},
            },
        ]
        offset_params = [
            {
                "name": self.limit_query_param,
                "required": False,
                "in": "query",
                "description": "Max results to return (limit/offset pagination).",
                "schema": {"type": "integer", "minimum": 1, "maximum": self.max_limit},
            },
            {
                "name": self.offset_query_param,
                "required": False,
                "in": "query",
                "description": "Number of items to skip (limit/offset pagination).",
                "schema": {"type": "integer", "minimum": 0},
            },
        ]
        selector = [{
            "name": "pagination",
            "required": False,
            "in": "query",
            "description": "Force pagination mode: 'page' or 'offset'. If omitted, auto-detects.",
            "schema": {"type": "string", "enum": ["page", "offset"]},
        }]
        return page_params + offset_params + selector
