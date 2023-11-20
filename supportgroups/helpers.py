from django.db.models.signals import post_save
from django.dispatch import receiver
from supportgroups.models import Groups, Role
from django.db.models.signals import post_save
from django.dispatch import receiver
# import pyrebase
import os
import uuid



# def uploadtoFirebase(file, path):
#     config = {
#         "apiKey": os.getenv('FIREBASE_API_KEY'),
#         "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
#         "databaseURL": os.getenv('FIREBASE_DATABASE_URL'),
#         "projectId": os.getenv('FIREBASE_PROJECT_ID'),
#         "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
#         "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
#         "appId": os.getenv('FIREBASE_APP_ID'),
#     }

#     firebase = pyrebase.initialize_app(config)
#     storage = firebase.storage()
#     imageId = uuid.uuid4()
#     file_type = str(file).split('.')[-1]
#     image = storage.child(path + str(imageId) + '.' + file_type).put(file)
#     download_url = storage.child(path + str(imageId) + '.' + file_type).get_url(image['downloadTokens'])
#     print(download_url)
#     return download_url
    
@receiver(post_save, sender=Groups)
def create_group_roles(sender, instance, created, **kwargs):
    if created:
        instance.update_roles()

def update_all_roles(permissions, id):
    group = Groups.objects.get(pk=id)
    role = Role.objects.get(group=group, role='admin')
    role.permissions = permissions['admin']
    role.save()
    group = Groups.objects.get(pk=id)
    role = Role.objects.get(group=group, role='mod')
    role.permissions = permissions['mod']
    role.save()
    group = Groups.objects.get(pk=id)
    role = Role.objects.get(group=group, role='member')
    role.permissions = permissions['member']
    role.save()