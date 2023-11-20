from django.contrib import admin
from supportgroups.models import Groups, Messages ,GroupsMembers
from supportgroups.models import *
from django.contrib.auth.models import Permission, ContentType

admin.site.register(Groups)
admin.site.register(GroupsMembers)
admin.site.register(Messages)
admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(Reactions)

# Register your models here.
