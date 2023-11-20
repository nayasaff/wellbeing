from django.http import JsonResponse

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            response = {"error": "Admin access required."}
            return JsonResponse(response, status=403)

    return _wrapped_view

def role_required(*roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            # Check if the user has the required roles
            if all(role in user.get_roles() for role in roles):
                return view_func(request, *args, **kwargs)
            else:
                response = {"error": "Access denied. Insufficient role permissions."}
                return JsonResponse(response, status=403)  

        return _wrapped_view
    return decorator