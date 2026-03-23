"""
Custom middleware for Slack-like presence tracking.
"""
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class UpdateLastSeenMiddleware(MiddlewareMixin):
    """
    Middleware that updates the authenticated user's last_seen timestamp.
    
    This is similar to Slack's presence tracking - any authenticated
    request updates the user's last_seen, allowing others to see
    if they're currently active or when they were last seen.
    
    The update is throttled to once per minute to avoid excessive DB writes.
    """
    
    def process_response(self, request, response):
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            # Only update if last_seen is None or older than 1 minute
            # to reduce DB writes
            if not user.last_seen or (timezone.now() - user.last_seen).total_seconds() > 60:
                # Use update() to avoid triggering full save signals
                from core.models import User
                User.objects.filter(pk=user.pk).update(last_seen=timezone.now())
        
        return response
