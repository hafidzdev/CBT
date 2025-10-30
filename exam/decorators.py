from django.core.exceptions import PermissionDenied


def teacher_required(function):
    """Hanya izinkan user dengan role 'teacher'"""
    def wrap(request, *args, **kwargs):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'teacher':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def student_required(function):
    """Hanya izinkan user dengan role 'student'"""
    def wrap(request, *args, **kwargs):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'student':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def admin_required(function):
    """Hanya izinkan user dengan role 'admin'"""
    def wrap(request, *args, **kwargs):
        if hasattr(request.user, 'user_type') and request.user.user_type == 'admin':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap

def student_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'student':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap
