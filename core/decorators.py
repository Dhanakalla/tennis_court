from django.http import HttpResponseForbidden

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You must be logged in")
        if request.user.role != "admin":
            return HttpResponseForbidden("Not allowed")
        return view_func(request, *args, **kwargs)
    return wrapper
