from django.shortcuts import redirect
from functools import wraps


def login_required_mongo(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("username"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.session.get("role") not in roles:
                return redirect("login")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
