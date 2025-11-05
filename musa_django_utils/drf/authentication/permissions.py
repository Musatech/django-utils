from functools import wraps
from rest_framework import status
from rest_framework.response import Response
import logging
logger = logging.getLogger('apps')

def require_permissions(client_roles_map):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Get token data from the request
            token_data = getattr(request, 'auth', None)
            
            # If token_data is None, try to get it from the user object
            if not token_data and hasattr(request, 'user') and request.user and hasattr(request.user, 'token_data'):
                token_data = request.user.token_data

            logger.debug(f"USER data : {request.user.__dict__}")
            logger.debug(f"Token data : {token_data}")
            if not token_data:
                logger.warning("Permission validation failed: No token data found")
                return Response(
                    {"detail": "Authentication credentials were not provided."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Extract client_id from token
            client_id = token_data.get('azp', None)
            
            if not client_id:
                logger.warning(f"Permission validation failed: No client_id found in token: {token_data}")
                return Response(
                    {"detail": "Invalid token: missing client_id."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if client_id is in the allowed clients
            if client_id not in client_roles_map:
                logger.warning(f"Permission validation failed: Client {client_id} not in allowed clients: {list(client_roles_map.keys())}")
                return Response(
                    {"detail": "Access denied for this client."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Extract user roles from token
            user_roles = []
            if 'realm_access' in token_data and 'roles' in token_data['realm_access']:
                user_roles = token_data['realm_access']['roles']
            
            # Check if user has any of the required roles for this client
            required_roles = client_roles_map[client_id]
            has_required_role = any(role in user_roles for role in required_roles)
            
            if not has_required_role:
                logger.warning(f"Permission validation failed: User roles {user_roles} don't match required roles {required_roles} for client {client_id}")
                return Response(
                    {"detail": "You don't have the required permissions to perform this action."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # If all checks pass, execute the view function
            return view_func(self, request, *args, **kwargs)
        
        return wrapper
    
    return decorator