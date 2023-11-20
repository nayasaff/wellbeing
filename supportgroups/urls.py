from django.urls import path
from supportgroups import views
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from supportgroups import consumers

urlpatterns = [
    path('getGroups/', views.getGroups, name='getGroups'),
    path('groupById/', views.groupById, name='groupById'),
    path('leaveGroup/<int:groupId>', views.leaveGroup, name='leaveGroup'),
    path('getSettingsOfGroup/<int:groupId>', views.getSettingsOfGroup, name='getSettingsOfGroup'),
    path('getGroupsByUserId/', views.getGroupsByUserId, name='getGroupsByUserId'),
    path('joinGroup/<int:groupId>', views.joinGroup, name='joinGroup'),
    path('editRoles/<int:id>', views.editRoles, name='editRoles'),
    path('editGroup/<int:id>', views.editGroup, name='editGroup'),
    path('verifyMember/<int:group_id>/<int:member_id>', views.verifyMember, name='verifyMember'),
    path('createForm/<int:groupId>', views.createForm, name='createForm'),
    path('deleteGroup/<int:id>', views.deleteGroup, name='deleteGroup'),
    path('submitAnswer/<int:group_id>', views.submitAnswer, name='submitAnswer'),
    path("getGroupById/<int:id>" , views.getGroupById , name="getGroupById"),
    path("getCategories/", views.getCategories, name="getCategories"),
]

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': URLRouter(
            [
                path('ws/send-message/<int:id>/<int:user_id>/', consumers.MessageStream.as_asgi()),
                path("ws/send-reaction/", consumers.ReactionsStream.as_asgi())
            ]
        ),
    }
)