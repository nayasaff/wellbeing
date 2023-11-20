from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.



class Library(models.Model):
    library_name = models.CharField(max_length=100)
    description = models.TextField()
    categories = models.JSONField()
    image = models.CharField(max_length=255)
    approved = models.BooleanField(default=False)

class Assessment(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    categories = models.JSONField()
    coach = models.ForeignKey("users.Coach", on_delete=models.CASCADE)
    library = models.JSONField()
    general_description = models.TextField()
    external_link = models.CharField(max_length=355, null=True)
    scales = models.JSONField(null=True)

@receiver(post_save, sender=Assessment)
def assignLibraries(sender, instance, created, **kwargs):
    if created:
        libraries = Library.objects.all()
        matching_libraries = []
        for library in libraries:
            for category in library.categories:
                if category['name'] in instance.categories and category['approved'] == True:
                    matching_libraries.append(library.library_name)
            if library.library_name in instance.categories:
                matching_libraries.append(library.library_name)
        instance.library = matching_libraries
        instance.save()



class AssessmentUser(models.Model) :
    assessment = models.ForeignKey(Assessment, related_name="assessment", on_delete=models.CASCADE)
    user = models.ForeignKey("users.Users", on_delete=models.CASCADE)
    final_score = models.JSONField()
    scores = models.ManyToManyField("Score", related_name="scores")
    date = models.DateField(auto_now_add=True)

class Results(models.Model) :
    measurement = models.CharField(max_length=100)
    weight = models.IntegerField()
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)

class Score(models.Model) :
    score_name = models.CharField(max_length=100)
    description = models.TextField()
    guidance = models.TextField(null=True)
    minimum_score = models.IntegerField()
    maximum_score = models.IntegerField()
    key_words = models.JSONField(null=True)
    result = models.ForeignKey(Results, on_delete=models.CASCADE)


class Question(models.Model):

    QUESTIONS_TYPE = [
        ('short answer', 'short answer'),
        ('long answer', 'long answer'),
        ('scale', 'scale'),
        ('radio button', 'radio button'),
        ('checkbox', 'checkbox'),
        ('drop down', 'drop down'),
        ("matrix", "matrix")
    ]
    question_name = models.CharField(max_length=200)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    optional = models.BooleanField(default=False, null=True)
    type = models.CharField(max_length=100, choices=QUESTIONS_TYPE)
    category = models.CharField(max_length=100)
    result = models.ForeignKey(Results, on_delete=models.CASCADE, null=True)

class Scale(Question):
    reversed = models.BooleanField(default=False)
    options = models.JSONField()

class Matrix(Question):
    columns = models.JSONField()
    matrix_type = models.CharField(max_length=100)
    scores = models.JSONField(null=True)
    options = models.JSONField(null=True)

class Option(models.Model):
    option_name = models.CharField(max_length=100)
    score = models.CharField(max_length=100, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)



# {"assessments" : [
#     {
#         "title": "Personality Assessment",
#         "description": "Discover your unique personality traits.",
#         "categories": ["Extraversion/Introversion", "Thinking/Feeling", "Sensing/Intuition", "Judging/Perceiving"],
#         "coach": 123
#     },
#     {
#         "title": "Career Interest Test",
#         "description": "Identify potential career paths based on your preferences.",
#         "categories": ["Interests", "Skills", "Values", "Personality"],
#         "coach": 456
#     },
#     {
#         "title": "Stress Management Survey",
#         "description": "Learn effective stress management techniques.",
#         "categories": ["Physical Health", "Emotional Well-being", "Coping Strategies", "Work-Life Balance"],
#         "coach": 789
#     }
# ]}

# class Assessment(models.Model):
#     title = models.CharField(max_length=100)
#     description = models.TextField()
#     categories = models.JSONField()
#     coach = models.ForeignKey("users.Coach", on_delete=models.CASCADE)
#     library = models.JSONField()
#     aproved = models.BooleanField(default=False)

# class Scales(models.Model):
#     scale = models.CharField(max_length=100)
#     weight = models.IntegerField()
#     general_description = models.TextField()

# class Score(models.Model):
#     score_name = models.CharField(max_length=100)
#     maximum_score = models.IntegerField()
#     minimum_score = models.IntegerField()
#     description = models.TextField()
#     guidance = models.TextField()

# class Questions(models.Model):
#     question_name = models.CharField(max_length=200)
#     assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
#     optional = models.BooleanField(default=False)
#     type = models.CharField(max_length=100)
#     result = models.ForeignKey(Scales, on_delete=models.CASCADE)

# class Scale(Questions):
#     reversed = models.BooleanField(default=False)

# class Matrix(Questions):
#     columns = models.JSONField()
#     mattrix_type = models.CharField(max_length=100)

# class Options(models.Model):
#     option = models.CharField(max_length=100)
#     score = models.ForeignKey(Score, on_delete=models.CASCADE)
#     question = models.ForeignKey(Questions, on_delete=models.CASCADE)

# # class ExternalLink(models.Model):
# #     link = models.CharField(max_length=355)
# #     assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
# #     scales = models.JSONField()

# class AssessmentUser(models.Model):
#     assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
#     user = models.ForeignKey("users.Users", on_delete=models.CASCADE)
#     final_score = models.JSONField()
#     scores = models.ManyToManyField(Score)
#     date = models.DateField(auto_now_add=True)