from rest_framework import serializers
from users.models import Coach , User , PromotionRequest, Users , DiamondConversion

from rest_framework import serializers
from .models import Coach

class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class DiamondConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiamondConversion
        fields = '__all__'



from rest_framework import serializers

class PromotionRequestSerializer(serializers.Serializer):
    bio = serializers.CharField(max_length=200)
    documents = serializers.FileField()

    def create(self, validated_data):
        return PromotionRequest.objects.create(**validated_data)
