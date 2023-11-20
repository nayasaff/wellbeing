from django.db import models
from users.models import Users
from django.contrib.auth.models import Permission, ContentType  


class Test(models.Model):
    text = models.CharField(max_length=264)



class Messages(models.Model):
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=64)
    type = models.CharField(max_length=30)
    reply = models.JSONField(null=True)
    url = models.CharField(max_length=300, null=True)
    size = models.CharField(max_length=30, null=True)

class Reactions(models.Model):
    emoji = models.CharField(max_length=3)
    message = models.ForeignKey(Messages, on_delete=models.CASCADE)
    users = models.JSONField(null=True)
    count = models.IntegerField(default=1)

class Groups(models.Model) :
    class Status(models.TextChoices):
        ACTIVE = 'active'
        DEACTIVATED = 'deactivated'

    class Type(models.TextChoices):
        PUBLIC = 'public'
        PRIVATE = 'private'
        HIDDEN = 'hidden'

    name = models.CharField(max_length=60)
    description = models.CharField(max_length=155) #JSONField
    categories = models.JSONField()
    created_time = models.DateField(auto_now_add=True)
    photo = models.CharField(max_length=355, default="https://firebasestorage.googleapis.com/v0/b/silent-snow-393013.appspot.com/o/groups%2FLogo.png?alt=media&token=db781c28-4187-4e46-937d-f54a40e45f69")
    status = models.CharField(max_length= 20,choices=Status.choices,default= Status.ACTIVE)
    messages = models.ManyToManyField(Messages ,related_name='messages')
    guideline = models.CharField(max_length=355, null=True)
    type = models.CharField(max_length=40, choices=Type.choices)
    forms = models.JSONField(null=True)
    members = models.ManyToManyField(Users, through='GroupsMembers', related_name='members')

    def update_roles(self) :
        permissions = {
            'admin': ['assign_mod', 'accept_reject_member', 'deactivate_group', 'remove_members', 'send_message', 'edit_group', 'invite_people'],
            'mod': ['remove_members', 'accept_reject_member', 'send_message', 'invite_people', 'assign_mod'],
            'member': ['send_message', "invite_people"],
        }
        admin_role = Role(role='admin', group = self, permissions = permissions['admin'])
        mod_role = Role(role='mod' , group = self, permissions = permissions['mod'])
        member_role = Role(role='member' , group = self, permissions = permissions['member'])
        admin_role.save()
        mod_role.save()
        member_role.save()
   



class Role(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        MOD = 'mod'
        MEMBER = 'member'

    role = models.CharField(max_length=30, choices=Role.choices)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE, null=True)
    permissions = models.JSONField(null=True)


class GroupsMembers(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        MOD = 'mod'
        MEMBER = 'member'
        PENDING = 'pending'
    
    group_id = models.ForeignKey(Groups, on_delete=models.CASCADE, null=True)
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE, null=True)
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.MEMBER)
    answers = models.JSONField(null=True)
    
    




#no need to add groups, find a way to add permissions automatically
