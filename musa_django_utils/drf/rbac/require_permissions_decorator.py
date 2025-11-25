from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .rbac import PermissionSpec


def require_permissions(*required_specs: PermissionSpec):
    def decorator(view_method):
        @wraps(view_method)
        def _wrapped(self, request, *args, **kwargs):
            user = getattr(request, "user", None)

            if not user.has_permission(*required_specs):
                return Response(
                    {"detail": "You do not have permission to access this resource."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            return view_method(self, request, *args, **kwargs)

        return _wrapped

    return decorator
