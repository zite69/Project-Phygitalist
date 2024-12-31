from functools import wraps
from django.http import Http404

def check_perm_404(
        perm,
        fn = None,
    ):

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Normalize to a list of permissions
            if isinstance(perm, str):
                perms = (perm,)
            else:
                perms = perm

            # Get the object to check permissions against
            if callable(fn):
                obj = fn(request, *args, **kwargs)
            else:  # pragma: no cover
                obj = fn

            # Get the user
            user = request.user

            # Check for permissions and return a response
            if not user.has_perms(perms, obj):
                # User does not have a required permission
                raise Http404
            else:
                # User has all required permissions -- allow the view to execute
                return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator

