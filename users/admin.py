from django.contrib import admin
from users.models import Users, User, Coach , PromotionRequest
# Register your models here.
admin.site.register(Users)
admin.site.register(User)
admin.site.register(Coach)
admin.site.register(PromotionRequest)