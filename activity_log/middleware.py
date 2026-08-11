from .context import clear_current_actor, set_current_actor
from .services import get_actor


class ActivityLogMiddleware:
    """Stores the current logged-in actor so model signals can log DB changes.

    Database writes are captured by the activity_log.signals post_save /
    post_delete receivers; this middleware only keeps track of who did them.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_actor(get_actor(request))
        try:
            response = self.get_response(request)
        finally:
            clear_current_actor()
        return response
