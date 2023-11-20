from rest_framework import serializers
from supportgroups.models import *

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reactions
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    reactions = serializers.SerializerMethodField()
    class Meta:
        model = Messages
        fields = '__all__'
    def get_reactions(self, obj):
        reactions = Reactions.objects.filter(message_id=obj)
        serializer = ReactionSerializer(reactions, many=True)
        return serializer.data

class GroupsMembersSerializer(serializers.ModelSerializer):
    user_role = serializers.SerializerMethodField()
    class Meta:
        model = GroupsMembers
        fields = "__all__"
    def get_user_role(self, obj):
        user_role = Users.objects.get(id=obj.user_id.id)
        return user_role.role.lower()



class GroupSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True)
    members = serializers.SerializerMethodField() 
    class Meta:
        model = Groups
        fields = '__all__'
    def get_members(self, obj):
        group_members = GroupsMembers.objects.filter(group_id=obj)
        serializer = GroupsMembersSerializer(group_members, many=True)
        return serializer.data


