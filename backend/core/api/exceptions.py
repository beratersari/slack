"""
Custom exception handling for meaningful API error responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import (
    AuthenticationFailed, NotAuthenticated, PermissionDenied,
    NotFound, ValidationError, MethodNotAllowed, ParseError,
    Throttled, APIException
)


def get_error_code(exc):
    """Get a standardized error code for the exception."""
    error_codes = {
        AuthenticationFailed: 'authentication_failed',
        NotAuthenticated: 'not_authenticated',
        PermissionDenied: 'permission_denied',
        NotFound: 'not_found',
        Http404: 'not_found',
        ValidationError: 'validation_error',
        MethodNotAllowed: 'method_not_allowed',
        ParseError: 'parse_error',
        Throttled: 'throttled',
    }
    
    # Check for CSRF errors (they come as PermissionDenied or custom)
    error_message = str(exc).lower()
    if 'csrf' in error_message:
        return 'csrf_error'
    
    for exc_type, code in error_codes.items():
        if isinstance(exc, exc_type):
            return code
    
    return 'error'


def get_error_message(exc):
    """Get a user-friendly error message."""
    # CSRF errors
    error_message = str(exc)
    if 'csrf' in error_message.lower():
        return {
            'error': 'CSRF token missing or invalid',
            'detail': 'Your request requires a valid CSRF token. Please include the X-Csrftoken header.',
            'solution': 'Use JWT token authentication via the Authorization header instead: "Authorization: Bearer <token>"',
        }
    
    # Standard error messages
    if isinstance(exc, NotAuthenticated):
        return {
            'error': 'Authentication required',
            'detail': 'You must be logged in to access this resource.',
            'solution': 'Login at /api/auth/login/ to get a JWT token, then include it in the Authorization header.',
        }
    
    if isinstance(exc, AuthenticationFailed):
        return {
            'error': 'Authentication failed',
            'detail': 'The provided credentials are invalid or expired.',
        }
    
    if isinstance(exc, PermissionDenied):
        return {
            'error': 'Permission denied',
            'detail': str(exc) if str(exc) else 'You do not have permission to perform this action.',
        }
    
    if isinstance(exc, NotFound) or isinstance(exc, Http404):
        return {
            'error': 'Resource not found',
            'detail': str(exc) if str(exc) else 'The requested resource does not exist.',
        }
    
    if isinstance(exc, ValidationError):
        return {
            'error': 'Validation error',
            'detail': exc.detail if hasattr(exc, 'detail') else str(exc),
        }
    
    if isinstance(exc, MethodNotAllowed):
        return {
            'error': 'Method not allowed',
            'detail': str(exc) if str(exc) else 'This HTTP method is not allowed for this endpoint.',
        }
    
    if isinstance(exc, Throttled):
        return {
            'error': 'Too many requests',
            'detail': str(exc) if str(exc) else 'You have exceeded the rate limit.',
            'retry_after': exc.wait if hasattr(exc, 'wait') else None,
        }
    
    if isinstance(exc, ParseError):
        return {
            'error': 'Parse error',
            'detail': str(exc) if str(exc) else 'Invalid request format.',
        }
    
    # Generic error
    return {
        'error': 'An error occurred',
        'detail': str(exc) if str(exc) else 'Please try again later.',
    }


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns meaningful JSON error responses.
    
    Handles all DRF and Django exceptions with consistent, user-friendly format.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get error details
        error_code = get_error_code(exc)
        message_data = get_error_message(exc)
        
        # Build consistent error response
        error_response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message_data.get('error', 'An error occurred'),
            }
        }
        
        # Add detail if available
        if 'detail' in message_data:
            error_response['error']['detail'] = message_data['detail']
        
        # Add solution hint if available
        if 'solution' in message_data:
            error_response['error']['solution'] = message_data['solution']
        
        # Add field errors for validation errors
        if isinstance(exc, ValidationError) and hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                error_response['error']['fields'] = exc.detail
            elif isinstance(exc.detail, list):
                error_response['error']['errors'] = exc.detail
        
        # Add retry info for throttled requests
        if isinstance(exc, Throttled) and hasattr(exc, 'wait'):
            error_response['error']['retry_after_seconds'] = exc.wait
        
        # Preserve status code
        response.data = error_response
        return response
    
    # Handle unhandled exceptions (500 errors)
    if isinstance(exc, Exception):
        return Response(
            {
                'success': False,
                'error': {
                    'code': 'server_error',
                    'message': 'Internal server error',
                    'detail': 'An unexpected error occurred. Please try again later.',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response
