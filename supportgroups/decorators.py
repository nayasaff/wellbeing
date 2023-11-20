from django.shortcuts import get_object_or_404
from supportgroups.models import Groups, GroupsMembers, Role
from django.http import JsonResponse
import json
from functools import wraps
from asgiref.sync import sync_to_async

#requests
def group_member_permission_required(permission):
    def decorator(view_func):
        def check_permission(request, id, *args, **kwargs):
            group = get_object_or_404(Groups, id=id)
            group_member = get_object_or_404(GroupsMembers, group_id=group, user_id=request.user)
            role = get_object_or_404(Role, group=group, role=group_member.role)

            if permission in role.permissions:
                return view_func(request, id, *args, **kwargs)
            else:
                return JsonResponse({"message": "permission denied"}, status=403)
        return check_permission
    return decorator

#websocket
def has_permission(permission):
    def decorator(func):
        async def wrapper(self, text_data):
            data = json.loads(text_data)
            # Assuming the 'permission' attribute is in the data received from the WebSocket
            group_member = await sync_to_async(get_object_or_404)(GroupsMembers, group_id_id=self.id, user_id_id = self.user_id)
            role = await sync_to_async(get_object_or_404)(Role, group_id=self.id, role=group_member.role)

            if permission in role.permissions:
                return await func(self, text_data)
            else:
                # Handle the case where the user doesn't have the required permission
                # For example, you can send an error message back to the user
                await self.send(text_data=json.dumps({
                    'error': 'You do not have the required permission to perform this action.'
                }))
        return wrapper
    return decorator