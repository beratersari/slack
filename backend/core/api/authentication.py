"""
Custom JWT authentication for DRF.
"""
import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from core.models import User


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication that validates tokens from the Authorization header.
    
    This authentication class does NOT require CSRF tokens, making it ideal
    for API-first applications.
    
    Usage: Include "Authorization: Bearer <token>" header in requests.
    """
    keyword = 'Bearer'
    
    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, token) if valid.
        Returns None if no authentication is attempted.
        """
        auth_header = authentication.get_authorization_header(request).split()
        
        if not auth_header:
            return None
        
        if auth_header[0].lower() != self.keyword.lower().encode():
            return None
        
        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        
        if len(auth_header) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')
        
        try:
            token = auth_header[1].decode()
        except UnicodeError:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain invalid characters.')
        
        return self.authenticate_credentials(token)
    
    def authenticate_credentials(self, token):
        """
        Validate the JWT token and return the corresponding user.
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired. Please login again.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token. Please login again.')
        
        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid token payload.')
        
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found or inactive.')
        
        return (user, token)
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate header.
        """
        return self.keyword


class JWTAuthenticationExtension(OpenApiAuthenticationExtension):
    """
    OpenAPI extension for JWTAuthentication.
    This enables the "Authorize" button in Swagger UI.
    """
    target_class = JWTAuthentication
    name = 'bearerAuth'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer <token>"',
        }
