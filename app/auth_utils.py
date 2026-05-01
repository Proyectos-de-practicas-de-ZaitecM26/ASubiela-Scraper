from functools import wraps
from flask import abort, redirect, url_for, request
from flask_login import current_user


def require_role(*allowed_roles):
    """Decorator to require one of the allowed roles for a route.

    Usage: @require_role('admin') or @require_role('admin','manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.path))
            role = getattr(current_user, 'role', None)
            if role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def is_role(user, role_name):
    return getattr(user, 'role', None) == role_name
