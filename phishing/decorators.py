from functools import wraps

from django.http import HttpRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from phishing.models import Status, Target, TargetPool


def phish(status: Status):
    """Transform a view to a phishing view.

    A phishing view is a GET route that takes two arguments in its query
    string: "t" (for target) and "p" (for pool). These parameters are,
    respectively, a Target's ID and its corresponding TargetPool's ID.

    The view will upgrade the status of the target and update the pool's
    counters accordingly. It will also add "target_id", "pool_id", "group", and
    "template" fields to the request.

    If the request is not a GET request, if a parameter is missing, or
    if any ID is invalid, the view will abort and respond with 404 Not Found.
    """
    def decorator(view):

        @wraps(view)
        def wrapper(request: HttpRequest):
            # Pre-conditions
            if request.method != 'GET':
                return HttpResponseNotFound()

            try:
                target_id = request.GET['t']
                pool_id = request.GET['p']
            except KeyError:
                return HttpResponseNotFound()

            target: Target = get_object_or_404(Target, pk=target_id)
            pool: TargetPool = get_object_or_404(TargetPool, pk=pool_id)

            # Actual logic
            new_statuses = target.upgrade_status(status)
            pool.increment_statuses(new_statuses)

            request.target_id = target_id
            request.pool_id = pool_id
            request.group = pool.group
            request.template = pool.template
            return view(request)

        return wrapper
    
    return decorator
