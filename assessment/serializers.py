from rest_framework import serializers
from assessment.models import *
from django.forms.models import model_to_dict

class ResultsSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    class Meta:
        model = Results
        fields = '__all__'

    def get_score(self, result):
        score = Score.objects.filter(result=result)
        return ScoreSerializer(score, many=True).data

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'
    
class MatrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matrix
        fields = '__all__'

class ScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scale
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    class Meta:
        model = Question
        fields = '__all__'
    
    def get_options(self, question):
        if not (question.type == 'matrix'  or question.type == 'scale' ):
            options = Option.objects.filter(question=question)
            return OptionSerializer(options, many=True).data
     

class AssessmentSerializer(serializers.ModelSerializer):
    coach = serializers.SerializerMethodField()
    results = serializers.SerializerMethodField()
    class Meta:
        model = Assessment
        fields = '__all__'

    def get_coach(self, assessment):
        return assessment.coach.username
    def get_results(self, assessment):
        results = Results.objects.filter(assessment=assessment)
        return ResultsSerializer(results, many=True).data


    
class AssessmentNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'title', "description" ,"general_description", "categories",]
class ScoreResultSerializer(serializers.ModelSerializer):
    result = ResultsSerializer()
    class Meta:
        model = Score
        fields = '__all__'

class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = '__all__'

class AssessmentUserSerializer(serializers.ModelSerializer):
    assessment = AssessmentNameSerializer()
    scores = ScoreResultSerializer(many=True)
    
    class Meta:
        model = AssessmentUser
        fields = '__all__'

class AssessmentCoachSerializer(serializers.ModelSerializer):
    coach = serializers.SerializerMethodField()
    class Meta:
        model = Assessment
        fields = '__all__'
    def get_coach(self, assessment):
        return assessment.coach.username

