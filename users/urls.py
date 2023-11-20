from django.urls import path
from users import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('userProfile/', views.get_user_profile, name='userProfile'),
    path('coachProfile/', views.get_coach_profile, name='coachProfile'),
    path('login/', views.login, name='login'),
    path('forgetPassword/', views.passwordReset, name='forgetPassword'),
    path('<str:username>/add-diamonds/<int:diamonds>/', views.add_user_diamonds, name='add-diamonds'),
    path('promote/', views.upgrade, name='add-promote'),
    path('coaches/', views.get_all_coaches, name='get_all_coaches'),
    path('logout/', views.logout_view, name='logout'),
    path('addFavouriteCoach/<str:id>', views.add_Coach_to_Favourite, name='add_Coach_to_Favourite'),
    path('GetFavouriteCoaches/', views.get_user_favourite_coaches, name='get_user_favourite_coaches'),

    ## Diamond Conversion
    path('diamond-conversions/', views.get_diamond_conversions, name='get_diamond_conversions'),
    path('diamond-conversions/<int:pk>/', views.get_diamond_conversions, name='get_diamond_conversion_detail'),
    path('create-diamond-conversion/', views.create_diamond_conversion, name='create_diamond_conversion'),
    path('update-diamond-conversion/', views.update_diamond_conversion, name='update_diamond_conversion'),

    path('buy_diamonds/', views.buyDiamonds, name='buy_diamonds'),
    ## 
    path("reset-password/", views.reset_password, name="reset_password"),
    path('annonymousName/', views.annonymousName, name='annonymousName'),
    path('getUserByUsername/<str:name>', views.getUserByUsername, name='getUserByUsername'),
    path('createPromotionRequest/', views.createPromotionRequest, name='createPromotionRequest'),
    path('getPromotionRequests/', views.get_promotion_requests, name='getPromotionRequests'),
    path('getPromotionRequestByUsername/<str:username>/', views.get_promotion_request_by_username, name='getPromotionRequest'),
    path('approvePromotionRequest/', views.accept_request, name='approvePromotionRequest'),
    path('rejectPromotionRequest/', views.reject_request, name='rejectPromotionRequest'),
    path('edit_profile_user/', views.edit_profile_user, name='edit_profile_user'),
    path('edit_profile_coach/', views.edit_profile_coach, name='edit_profile_coach'),
    path('add_voices/', views.add_voices, name='add_voices'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)