import uuid
import logging
import threading
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.security')

class SessionContaminationDebugger(MiddlewareMixin):
    """
    Detects if the session/identity flips during the execution of a single request.
    This catches asynchronous Gunicorn/database bleed and global variable state leaks.
    """
    def process_request(self, request):
        request.trace_id = str(uuid.uuid4())[:8]
        request._thread_id = threading.get_native_id()
        
        request._incoming_session = request.COOKIES.get('sessionid', 'NO_SESSION')
        request._incoming_user = getattr(request.user, 'username', 'Anonymous') if hasattr(request, 'user') else "NoAuth"

        if request._incoming_user != "Anonymous" and request._incoming_user != "NoAuth":
            logger.info(f"[TRACE:{request.trace_id}] [THREAD:{request._thread_id}] INCOMING | "
                        f"Session: {request._incoming_session[-6:]} | User: {request._incoming_user} | Path: {request.path}")

    def process_response(self, request, response):
        if not hasattr(request, '_incoming_user'):
            return response

        outgoing_user = getattr(request.user, 'username', 'Anonymous') if hasattr(request, 'user') else "NoAuth"
        
        # Log when a brand new session cookie is sent to the client
        set_cookie_header = response.cookies.get('sessionid', None)
        if set_cookie_header:
            logger.warning(f"[TRACE:{request.trace_id}] SET-COOKIE DETECTED | "
                           f"New Session Assigned to User: {outgoing_user}")

        # CRITICAL: Detect if the user identity flipped during this exact request!
        if request._incoming_user not in ["Anonymous", "NoAuth"] and request._incoming_user != outgoing_user:
            logger.critical(f"🚨 IDENTITY FLIP DETECTED! [TRACE:{request.trace_id}] | "
                            f"Started as: {request._incoming_user} | Ended as: {outgoing_user}. "
                            f"THREAD POISONING OR GLOBAL VARIABLE LEAK CONFIRMED.")

        return response


class NoCacheAuthenticatedMiddleware(MiddlewareMixin):
    """
    Prevents Nginx, Cloudflare, or Render from caching authenticated HTML responses.
    This prevents User B from seeing User A's cached HTML and stealing their session cookie.
    """
    def process_response(self, request, response):
        # Only apply to authenticated users, allow caching for anonymous users
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Force downstream CDNs and proxies to NEVER cache this response
            response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            # Also tell proxies to Vary on Cookie so if they DO cache, they separate by session
            response['Vary'] = 'Cookie'
            
        return response
