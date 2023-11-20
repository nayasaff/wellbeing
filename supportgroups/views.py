from .models import *
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from users.models import Users, User
from django.forms.models import model_to_dict
from rest_framework.decorators import api_view
from dotenv import load_dotenv
from supportgroups.decorators import group_member_permission_required
from supportgroups.serializers import *
from supportgroups.helpers import update_all_roles
from lists.libraries import groupCategory

load_dotenv('config.env')
# Create your views here.


def getGroups(request) : #serializer
    try :
        groups = Groups.objects.exclude(type = 'hidden')
        result = GroupSerializer(groups, many=True)
        return JsonResponse(result.data, safe=False)
    except Exception as e:
        return JsonResponse({"message" : str(e)}, status=400)

@api_view(['GET'])
def getGroupsByUserId(request):
    try:
        user = Users.objects.get(username = request.user)
        annonymous_username_exists =True
        groups = Groups.objects.filter(members__id = user.id)
        group_list = GroupSerializer(groups, many=True)
        if(user.role.lower() == 'user'):
            username = User.objects.get(pk = user.id).annonymous_username
            if username is None:
                annonymous_username_exists = False
        filtered_data = []
        for group in group_list.data:
            is_pending = False
            is_deactivated = False
            for current_user in group['members']:
                if(current_user['role'] != 'pending'):
                    role = Role.objects.get(group_id = group['id'], role = current_user['role'])
                current_user['permissions'] = role.permissions
                if current_user['user_id'] == user.id and current_user['role'] == 'pending':
                    is_pending = True
                if current_user['user_id'] == user.id and group['status'] == 'deactivated' and current_user['role'] != 'admin':
                    is_deactivated = True
            if(is_pending == False and is_deactivated == False):
                filtered_data.append(group)
        return JsonResponse({"data" : filtered_data, "username" : annonymous_username_exists}, safe=False)
    except Exception as e:
        return JsonResponse({"message" : str(e)}, status=400)
    
def automaticReject(forms, answers):
    if forms is None:
        return False
    
    if answers is None:
        return False

    for index,form in enumerate(forms):
        if form['type'] != 'Paragraph' :
            print(index)
            optionIndex = form['options'].index(answers[index])
            print(optionIndex)
            if form['checked'][optionIndex]:
                return True
    return False


@api_view(['GET'])
def getGroupById(request, id):
    group = Groups.objects.get(pk=id)
    if group.type != 'public' :
        groupMember = GroupsMembers.objects.filter(group_id = group)
        for groupmember in groupMember:
            remove = automaticReject(group.forms, groupmember.answers)
            if remove:
                groupmember.delete()

    current_user = Users.objects.get(username = request.user)
    if not GroupsMembers.objects.filter(group_id = group, user_id = current_user).exists(): 
        return JsonResponse({"message" : "You are not a member of this group"}, status=400)
    result = GroupSerializer(group)
    for member in result.data['members']:
        users = Users.objects.get(pk = member['user_id'])
        if users.role.lower() == 'user' :
            the_user = User.objects.get(pk = member['user_id'])
            member['annonymous_username'] = the_user.annonymous_username if the_user.annonymous_username != '' else the_user.username
        else:
            member['annonymous_username'] = users.username
        if(member['role'] != 'pending'):
            role = Role.objects.get(group_id = id, role = member['role'])
        member['permissions'] = role.permissions
    return JsonResponse(result.data, safe=False)


@api_view(['POST'])
def groupById(request):  # i can get messages and members
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            categories = data.get('categories')
            newGroup = Groups(name= data.get("name"), description= data.get("description"), 
                categories=categories , type=data.get('type'), guideline=data.get('guideline'))
            photo = data.get('photo')
            if (photo is not None):
                newGroup.photo = photo
            newGroup.save() 
            user = Users.objects.get(username = request.user)


            groupMember = GroupsMembers(user_id = user ,group_id = newGroup ,role='admin')
            groupMember.save()

            result = GroupSerializer(newGroup)
            return JsonResponse(result.data, safe=False, status=200)  
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)
        

@api_view(['GET','POST'])
def joinGroup(request, groupId):
    if request.method == 'POST':
        try:
            group = Groups.objects.get(pk = groupId)
            user = Users.objects.get(username = request.user)

            if(GroupsMembers.objects.filter(user_id = user, group_id = group).exists()):
                return JsonResponse({'message' : 'user already in group'}, status =400)
            if group.type == 'private' and group.forms is not None:
                return JsonResponse({'message' : 'form'}, status =200)
            if group.type == 'private':
                group_member = GroupsMembers(group_id = group, user_id = user, role='pending')
                group_member.save()
            if group.type == 'public':
                group_member = GroupsMembers(group_id = group, user_id = user, role='member')
                group_member.save()
            return JsonResponse(model_to_dict(group_member), safe=False, status =200)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)
    else:
        return JsonResponse({'message' : 'bad response'})

@api_view(['PATCH'])
@group_member_permission_required('edit_group')
def editGroup(request, id):
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            print(data)
            data = data.get('data')
            categories = data.get('categories')
            permissions = data.get('permissions')
            updated_group = Groups.objects.get(pk=id)
            updated_group.name = data.get("name")
            updated_group.description = data.get("description")
            updated_group.categories = categories
            updated_group.type = data.get('type')
            if 'photo' in data:
                updated_group.photo = data.get('photo')
            if(data.get('guideline') != 'null'):
                updated_group.guideline = data.get('guideline')
            if permissions is not None:
                update_all_roles(permissions, updated_group.id)
            updated_group.save()
            return JsonResponse({"message": "updated groups "}, status=200)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)



@api_view(['DELETE'])
@group_member_permission_required('deactivate_group')
def deleteGroup(request, id):
    if request.method == 'DELETE':
        try:
            deleted = request.data.get('deleted')
            role = request.data.get('role')
            group = Groups.objects.get(pk=id)
            if deleted and role != 'admin':
                return JsonResponse({"message": "you are not allowed to delete this group"}, status=403)
            if deleted:
                group.delete()
                return JsonResponse({"message": "group has been deleted successfulyy"}, status=200)
            else:
                group.status = request.data.get('status')
                group.save()
                return JsonResponse({"message": "group has been deactivated successfulyy"}, status=200)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)



@csrf_exempt
def verifyMember(request, group_id, member_id):
    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
            is_accepted = body.get('is_accepted')
            user = Users.objects.get(pk=member_id)
            print(user.id)
            groupMember = GroupsMembers.objects.get(user_id_id=member_id, group_id_id=group_id)
            if is_accepted :
                groupMember.role = 'member'
                groupMember.save()
            else :
                groupMember.delete()
            return JsonResponse({"message": "success"}, status=200)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)
    if request.method == 'DELETE':
        try:
            groupMember = GroupsMembers.objects.get(user_id_id=member_id, group_id_id=group_id)
            groupMember.delete()
            return JsonResponse({"message": "success"}, status=200)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)




@api_view(['DELETE'])
def leaveGroup(request, groupId):
    try:
        if request.method == 'DELETE':
            user = Users.objects.get(username=request.user)
            group = Groups.objects.get(pk=groupId)
            if GroupsMembers.objects.get(user_id=user, group_id=group).role == 'admin':
                #if the only member left
                if GroupsMembers.objects.filter(group_id=group).count() == 1:
                    GroupsMembers.objects.get(user_id=user, group_id=group).delete()
                    group.delete()
                    return JsonResponse({"message": "success"}, status=200)
                #assign mod if exists or other member admin
                else:
                    if GroupsMembers.objects.filter(group_id=group, role='mod').exists():
                        #choose one first mod to be admin
                        group_member =GroupsMembers.objects.filter(group_id=group, role='mod').first()
                        group_member.role = 'admin'
                    else:
                        group_member = GroupsMembers.objects.filter(group_id=group, role='member').first()
                        group_member.role = 'admin'
            GroupsMembers.objects.get(user_id=user, group_id=group).delete()
            return JsonResponse({"message": "success"}, status=200)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=400)



@csrf_exempt
def getSettingsOfGroup(request, groupId):
    try:
        group = Groups.objects.get(pk=groupId)
        admin = Role.objects.get(group = group, role = 'admin')
        mod = Role.objects.get(group = group, role = 'mod')
        member = Role.objects.get(group = group, role = 'member')
        groupMember = GroupsMembers.objects.filter( group_id = group, role ='pending')

        result = {
            'role' : {'admin' :admin.permissions,
            'mod' : mod.permissions,
            'member' : member.permissions,
            },
            'pending' : GroupsMembersSerializer(groupMember, many=True).data,
            'forms' : group.forms
        }

        for res in result['pending']:
            cuurent_user = Users.objects.get(pk = res['user_id'])
            if(cuurent_user.role.lower() == 'user' ):
                user = User.objects.get(pk = res['user_id'])
                res['annonymous_username'] =  user.annonymous_username if not (user.annonymous_username == '' or user.annonymous_username == None ) else user.username
            else :
                res['annonymous_username'] = cuurent_user.username
    
        return JsonResponse(result , safe=False, status=200)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=403)



@api_view(['PATCH'])
@group_member_permission_required('assign_mod')
def editRoles(request, id):
    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
            role = body.get('role')
            groupMember = GroupsMembers.objects.get(user_id = body.get('memberId'), group_id = id)
            groupMember.role = role
            groupMember.save()
            return JsonResponse({"message": "success"}, status=200)
        except  Exception as e:
            return JsonResponse({"message": str(e)}, status=400)

@csrf_exempt       
def createForm(request, groupId):
    if request.method == 'PATCH':
        group = Groups.objects.get(pk=groupId)
        body = json.loads(request.body)
        group.forms = body
        group.save()
        return JsonResponse({"message": "success"}, status=200)

@api_view(['PATCH'])
def submitAnswer(request, group_id):
    if request.method == 'PATCH':
        body = json.loads(request.body)
        user = Users.objects.get(username = request.user)
        group = Groups.objects.get(pk = group_id)
        if(GroupsMembers.objects.filter(group_id = group, user_id = user).exists()) :
            return JsonResponse({"message": "user already in group"}, status=200)
        group_member = GroupsMembers(group_id = group, user_id = user, role='pending', answers = body)
        group_member.save()
        return JsonResponse(model_to_dict(group_member), safe=False, status=200)


    
@csrf_exempt
def getCategories(request):
    if request.method == 'GET':
        return JsonResponse(groupCategory, safe=False, status=200)
