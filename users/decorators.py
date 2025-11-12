from functools import wraps
from django.shortcuts import redirect
from urllib.parse import quote
from django.conf import settings

def login_required_modal(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            next_url = quote(request.get_full_path())
            return redirect(f"/?login=required&next={next_url}")
        return view_func(request, *args, **kwargs)
    return wrapper

def debug_pass(view_func):
    """
    Si esta el modo DEBUG activo, no se ejecuta la vista.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print("DEBUG PASS decorator activated.")
        if settings.DEBUG:
            return None
        return view_func(request, *args, **kwargs)
    return wrapper