from django.db import models
from django.contrib.auth.models import AbstractUser

class Voice(models.Model):
    name = models.CharField(max_length=255, unique=True)



default_Voices = {
    "Angriness",
    "Anxiety",
    "Boredom",
    "Calmness",
    "Confusion",
    "Depression",
    "Disgust",
    "Fear",
    "Happiness",
    "Hate",
    "Love",
    "Sadness",
    "Surprise"
}

class Users(AbstractUser):
    username = models.CharField(max_length=64,unique=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    age = models.PositiveIntegerField(null=True)
    birthday_day = models.PositiveIntegerField(null=True)
    birthday_month = models.PositiveIntegerField(null=True)
    birthday_year = models.PositiveIntegerField(null=True)
    country = models.CharField(max_length=64, null=True)
    current_country = models.CharField(max_length=64, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)


    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"
        COACH = "COACH", "Coach"
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

class Coach(Users):
    role = Users.Role.COACH
    bio = models.TextField(default="")
    profession = models.TextField(default="")
    created_assessments = models.IntegerField(default=0)
    approved_assessments = models.JSONField(default=dict)
    requested_sessions = models.JSONField(default=dict)
    support_groups_created = models.JSONField(default=dict)
    avg_session_rating = models.FloatField(default=0)

class User(Users):

    role = Users.Role.USER
    diamonds = models.PositiveIntegerField(default= 1000)
    XP = models.PositiveIntegerField(default= 0)
    level = models.PositiveIntegerField(default= 0)
    Overall_Score = models.PositiveIntegerField(default= 0)
    Total_Assessments = models.PositiveIntegerField(default= 0)
    Total_Live_Sessions = models.PositiveIntegerField(default= 0)
    Total_Joined_Meditations = models.PositiveIntegerField(default= 0)
    Total_Journal_Entries = models.PositiveIntegerField(default= 0)
    Total_Goals_Set = models.PositiveIntegerField(default= 0)
    FavouriteCoachesIds = models.JSONField(default=list)
    annonymous_username = models.CharField(max_length=64, null=True)
    diary_streak = models.PositiveIntegerField(default= 0)
    voices = models.ManyToManyField(Voice)



from django.db import models

# class PromotionAssessment(models.Model):

#     Questions = models.JSONField(default=list)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     category = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Promotion Assessment - {self.created_at}"

class PromotionRequest(models.Model):
    Questions = models.JSONField(default=list)
    working_days_hours = models.JSONField(default=list)
    username = models.CharField(unique=True, max_length=255)
    documents = models.FileField(upload_to='promotion_requests/documents/' + str(username) + '/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Promotion Request - {self.created_at}"

class DiamondConversion(models.Model):
    dollarToDiamond = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"Diamond Conversion - {self.diamonds} diamonds for {self.price} EGP"