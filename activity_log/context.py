"""Thread-local holder for the current request actor.

The middleware stores the logged-in user here so that model signals
(post_save / post_delete) can attribute database changes to the right person.
"""

import threading

_thread_locals = threading.local()


def set_current_actor(actor):
    _thread_locals.actor = actor


def get_current_actor():
    return getattr(_thread_locals, "actor", None)


def clear_current_actor():
    _thread_locals.actor = None
