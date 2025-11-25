from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .rbac import PermissionSpec


def require_permissions(*required_specs: PermissionSpec):
    """
    Decorator para ser usado em métodos de View (APIView/ViewSet).
    Sempre considera OR entre as specs:
    - require_permissions(spec1)               -> precisa atender spec1
    - require_permissions(spec1, spec2, ...)  -> precisa atender QUALQUER uma

    O token deve ter no payload:
    payload = {
      "permissions": {
        1: [2, 3],
        2: [1],
      }
    }
    """

    def decorator(view_method):
        @wraps(view_method)
        def _wrapped(self, request, *args, **kwargs):
            user = getattr(request, "user", None)

            if not user or not getattr(user, "is_authenticated", False):
                return Response(
                    {"detail": "Authentication credentials were not provided."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # token_data vindo do OauthAuthentication (payload JWT)
            # token_data = getattr(request, "user", None)

            if not user.has_permission(*required_specs):
                return Response(
                    {"detail": "You do not have permission to access this resource."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            return view_method(self, request, *args, **kwargs)

        return _wrapped

    return decorator
