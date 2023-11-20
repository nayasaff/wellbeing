from django.contrib.auth import authenticate
from .models import Coach
from rest_framework_simplejwt.tokens import RefreshToken
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import User , DiamondConversion
from django.shortcuts import render
from django.shortcuts import redirect
from datetime import datetime
from .models import *
from django.contrib.auth import authenticate, login as dj_login, logout  
import json
from users.serializers import CoachSerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import serializers
from .models import Users
from django.forms.models import model_to_dict
from django.core.mail import send_mail
import random
import string
from django.contrib.auth import update_session_auth_hash
from .decorators import admin_required , role_required
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings


def upload_default_profile_picture():
    default_picture_path = settings.MEDIA_ROOT + '/default_profile_picture.jpg'
    if not default_storage.exists(default_picture_path):
        with open(default_picture_path, 'rb') as default_picture_file:
            default_storage.save(default_picture_path, ContentFile(default_picture_file.read()))

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'email', 'password']

import stripe


from .serializers import DiamondConversionSerializer

@api_view(['POST'])
def create_diamond_conversion(request):
    if request.method == 'POST':
        serializer = DiamondConversionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_diamond_conversion(request):
    try:
        diamond_conversion = DiamondConversion.objects.first()
    except DiamondConversion.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = DiamondConversionSerializer(diamond_conversion, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_diamond_conversions(request, pk=None):
    if pk:
        try:
            diamond_conversion = DiamondConversion.objects.get(pk=pk)
            serializer = DiamondConversionSerializer(diamond_conversion)
            return Response(serializer.data)
        except DiamondConversion.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    diamond_conversions = DiamondConversion.objects.all()
    serializer = DiamondConversionSerializer(diamond_conversions, many=True)
    return Response(serializer.data)

@csrf_exempt
@api_view(['POST'])
def buyDiamonds(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            diamonds = float(data.get('diamonds'))  # Cast to float or int
            user = User.objects.get(username=request.user)
            paymentMethodId = data.get('paymentMethod')
            diamondConversion = DiamondConversion.objects.first()
            oneDollarInDiamonds = float(diamondConversion.dollarToDiamond)  

            price = int(diamonds / oneDollarInDiamonds * 100)
            
            stripe.api_key = settings.STRIPE_SECRET_KEY

            try:
                
               
                payment_intent = stripe.PaymentIntent.create(
                    amount=price,
                    currency='usd',
                    payment_method=data.get('paymentMethod'),
                    customer=user.stripe_customer_id, 
                    payment_method_types=['card'],
                )
                print(payment_intent.id)
                payment_success = stripe.PaymentIntent.confirm(
                    payment_intent.id,
                    payment_method=paymentMethodId,
                )
                

                if payment_success.status == 'succeeded':
                    user.diamonds += diamonds
                    user.save()
                    return JsonResponse({"message": "Payment succeeded"}, status=200)
                else:
                    return JsonResponse({"error": "Payment confirmation failed"}, status=400)
            except stripe.error.StripeError as e:
                return JsonResponse({"error": str(e.user_message)}, status=400)
        except Exception as e:
            return JsonResponse({"error": "An error occurred while processing the payment."}, status=400)

@api_view(['PUT'])
def upload_profile_picture(request):
    if request.method == 'PUT':
        try:
            
            user = User.objects.get(username=request.user)
            image_file = request.FILES.get('profile_picture')
            
            if image_file:
                user.profile_picture = image_file
                user.save()
                
                return JsonResponse({'message': 'Profile picture uploaded successfully'}, status=200)
            else:
                return JsonResponse({'error': 'No image file provided'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
        return JsonResponse({}, status=400)

def calculate_age(birthday_year, birthday_month, birthday_day):

    birthday_year = int(birthday_year)
    birthday_month = int(birthday_month)
    birthday_day = int(birthday_day)

    today = datetime.today()
    age = today.year - birthday_year - ((today.month, today.day) < (birthday_month, birthday_day))
    
    return age

default_Voices = ["Angriness", "Anxiety", "Boredom", "Calmness", "Confusion", "Depression", "Disgust", "Fear", "Happiness", "Hate", "Love", "Sadness", "Surprise"]
default_Voices = json.dumps(default_Voices)
@csrf_exempt
def signup(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        username = data.get('username')
        birthday_day = data.get('birthday_day')
        birthday_month = data.get('birthday_month')
        birthday_year = data.get('birthday_year')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        password = data.get('password')
        country = data.get('country')
        current_country = data.get('current_country')
        age = calculate_age(birthday_year, birthday_month, birthday_day)



        if Users.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User with this email already exists.'}, status=400)
        
        if Users.objects.filter(username=username).exists():
            return JsonResponse({'error': 'User with this username already exists.'}, status=400)

        user = User.objects.create_user(email=email, password=password, username=username,
                                        age=age, first_name=first_name, last_name=last_name , birthday_day=birthday_day, birthday_month=birthday_month, birthday_year=birthday_year , country=country , current_country=current_country)


        return JsonResponse({'message': 'Sign up successful',
                             "age" : user.age}, status=200)
    else:
        return JsonResponse({}, status=400)


@csrf_exempt
def login(request):
    try:
        if request.method == 'POST':
            body = json.loads(request.body)
            email = body.get('email')
            username = body.get('username')
            password = body.get('password')
            user = None

            user_model = None  

            if email:
           
                user = authenticate(email=email, password=password)
              
                if user.is_superuser:
                    print(user)
                    csrf_token = get_token(request)
                    dj_login(request, user)
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    response = {
             
                        'csrfToken': csrf_token,
                        'token': access_token,
          
                        "role": user.role,
        
                    }
                    return JsonResponse(response, status=200)
                try:
                    user_model = User.objects.get(email=email)

                except User.DoesNotExist:
                    try:
                        user_model = Coach.objects.get(email=email)
                    except Coach.DoesNotExist:
                        response = {"error": "User does not exist."}
                        return JsonResponse(response, status=400)
            elif username:
                user = authenticate(username=username, password=password)
                print(user)
                if user.is_superuser:
                    print(user)
                    
                    csrf_token = get_token(request)
                    dj_login(request, user)
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    response = {
                        
                        'csrfToken': csrf_token,
                        'token': access_token,
                        
                        "role": "Admin",
                        
                    }
                    return JsonResponse(response, status=200)
                try:
                    user_model = User.objects.get(username=username)
                except User.DoesNotExist:
                    try:
                        user_model = Coach.objects.get(username=username)
                    except Coach.DoesNotExist:
                        response = {"error": "User does not exist."}
                        return JsonResponse(response, status=400)
            
            if user is not None:
               
                csrf_token = get_token(request)

                dj_login(request, user_model)
                refresh = RefreshToken.for_user(user_model)
                access_token = str(refresh.access_token)
                response = {
                    "id": user_model.id,
                    'csrfToken': csrf_token,
                    'token': access_token,
                    'email': user_model.email,
                    "role": user_model.role,
                    "username": user_model.username,
                }
                return JsonResponse(response, status=200)
            else:
                response = {"error": "Invalid credentials"}
                return JsonResponse(response, status=400)
        else:
            return JsonResponse({"message": 'Invalid request method'}, status=405)

    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)




@api_view(['GET'])
def get_user_profile(request):

    if request.method == 'GET':
        try:
            print(request.user)
            user = User.objects.get(username=request.user)
            default_picture_url = settings.MEDIA_URL
            if not user.profile_picture:
                upload_default_profile_picture()

                user.profile_picture = 'default_profile_picture.jpg'

            profile_picture_url = f'https://127.0.0.1:8000/{default_picture_url}/{str(user.profile_picture)}'

            profile = {
                'id': user.pk,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'country': user.country,
                'current_country': user.current_country,
                'age': user.age,
                'role': user.role,
                'diamonds': user.diamonds,
                'XP': user.XP,
                'level': user.level,
                'Overall_Score': user.Overall_Score,
                'Total_Assessments': user.Total_Assessments,
                'Total_Live_Sessions': user.Total_Live_Sessions,
                'Total_Joined_Meditations': user.Total_Joined_Meditations,
                'Total_Journal_Entries': user.Total_Journal_Entries,
                'Total_Goals_Set': user.Total_Goals_Set,
                'profile_picture': profile_picture_url,
                'voices': list(user.voices.values_list('name', flat=True)),

            }
            return JsonResponse(profile, status=200)
        except Users.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
        return JsonResponse({}, status=400)

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.http import JsonResponse

@csrf_exempt
def reset_password(request):
    data = json.loads(request.body)
    uidb64 = data.get("uid")
    token = data.get("token")
    new_password = data.get("new_password")

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Users.objects.get(pk=uid)
    except (Users.DoesNotExist, ValueError, OverflowError, TypeError):
        return JsonResponse({"message": "Invalid reset link."}, status=400)

    if default_token_generator.check_token(user, token):
        user.set_password(new_password)
        user.save()

        return JsonResponse({"message": "Password reset successful."}, status=200)
    else:
        return JsonResponse({"message": "Invalid reset link."}, status=400)

@csrf_exempt
def passwordReset(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')

        try:
            user = Users.objects.get(email=email)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            subject = 'Password Reset'
            message = f'Click the following link to reset your password: https://127.0.0.1:3000/reset-password/{uid}/{token}/'
            from_email = 'wellbeingbucket@gmail.com'
            recipient_list = [email]
            print(message)
            print(recipient_list)
            try:
                send_mail(subject= subject, message=message, recipient_list = recipient_list, from_email=from_email)
            except Exception as e:
                print(e)
                return JsonResponse({'error': 'Failed to send email'}, status=400)
            
            print('here')

            return JsonResponse({'message': 'Password reset email sent'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
        return JsonResponse({}, status=400)
    
@api_view(['POST'])
def set_profile_picture(request):
    try:
        user = Users.objects.get(username=request.user)


        if 'profile_picture' in request.FILES:
            uploaded_picture = request.FILES['profile_picture']

            user.profile_picture.save(uploaded_picture.name, uploaded_picture)

            return JsonResponse({'message': 'Profile picture uploaded successfully.'})
        else:
            return JsonResponse({'error': 'No profile picture file found in the request.'}, status=400)
    except Users.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@api_view(['GET'])
def get_coach_profile(request):
    
    if request.method == 'GET':
        try:
            print(request.user)
            user = Coach.objects.get(username=request.user)
            default_picture_url = settings.MEDIA_URL
            if not user.profile_picture:
                upload_default_profile_picture()

                user.profile_picture = 'default_profile_picture.jpg'

            profile_picture_url = f'https://127.0.0.1:8000/{default_picture_url}/{str(user.profile_picture)}'
   
            if user is not None:
                profile = {
                    'id': user.pk,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'bio': user.bio,
                    'profession': user.profession,
                    'country': user.country,
                    'avg_session_rating': user.avg_session_rating,
                    'current_country': user.current_country,
                    'age': user.age,
                    'created_assessments': user.created_assessments,
                    'approved_assessments': user.approved_assessments,
                    'requested_sessions': user.requested_sessions,
                    'support_groups_created': user.support_groups_created,
                    'profile_picture': profile_picture_url,
                }
                return JsonResponse(profile, status=200)
        except Users.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
        return JsonResponse({}, status=400)



@api_view(['POST'])
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'}, status=200)


@api_view(['PUT'])
def edit_profile_user(request):
    if request.method == 'PUT':
        try:
            user = User.objects.get(username=request.user)

            username = request.POST.get('username')
            email = request.POST.get('email')
            current_country = request.POST.get('current_country')
            profile_picture = request.FILES.get('profile_picture')

            if(username != user.username):
                if Users.objects.filter(username=username).exists():
                    return JsonResponse({'error': 'User with this username already exists.'}, status=400)

            user.username = username
            user.email = email
            user.current_country = current_country

            if profile_picture:
                user.profile_picture = profile_picture

            user.save()

            return JsonResponse({'message': 'Profile updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({}, status=400)


#edit voices user

@api_view(['POST'])
def add_voices(request):
    if request.method == 'POST':
        try:
            user = User.objects.get(username=request.user)
            voices = request.data.get('voices')  # Use request.data instead of request.POST
            if isinstance(voices, str):
                voices = json.loads(voices)
            for voice_name in voices:
                voice, created = Voice.objects.get_or_create(name=voice_name)
                user.voices.add(voice)

            user.save()

            return JsonResponse({'message': 'Voices added successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({}, status=400)


@api_view(['PUT'])
def edit_profile_coach(request):
    if request.method == 'PUT':
        try:
            user = Coach.objects.get(username=request.user)

            username = request.POST.get('username')
            email = request.POST.get('email')
            bio = request.POST.get('bio')
            current_country = request.POST.get('current_country')
            profile_picture = request.FILES.get('profile_picture')

            if(username != user.username):
                if Users.objects.filter(username=username).exists():
                    return JsonResponse({'error': 'User with this username already exists.'}, status=400)

            user.username = username
            user.email = email
            user.bio = bio
            user.current_country = current_country

            if profile_picture:
                user.profile_picture = profile_picture

            user.save()

            return JsonResponse({'message': 'Profile updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({}, status=400)
@csrf_exempt
@api_view(['POST'])
def add_user_diamonds(request, username, diamonds):
    if request.method == 'POST':
        try:
            user = User.objects.get(username=username)
            user.diamonds += diamonds
            user.save()
            return JsonResponse({"message": "Diamonds added successfully"}, status=200)
        except User.DoesNotExist:
            return JsonResponse({"message": "User not found"}, status=404)


@csrf_exempt
@api_view(['POST'])
def add_Coach_to_Favourite(request, id):
    if request.method == 'PUT':
        try:
            user = User.objects.get(username=request.user)
            user.FavouriteCoachesIds.append(id)
            user.save()
            return JsonResponse({"message": "Favourite coach added"}, status=200)
        except User.DoesNotExist:
            return JsonResponse({"message": "User not found"}, status=404)


def promote_to_coach(user_id, working_days_hours, password):
    try:
        user = Users.objects.get(id=user_id)
        
        temp = user
        password = User.objects.make_random_password()

        user.delete()


        coach = Coach.objects.create_user(email=temp.email, password=password ,birthday_day = temp.birthday_day ,birthday_month = temp.birthday_month
        ,birthday_year = temp.birthday_year , country = temp.country , current_country = temp.current_country,profile_picture = temp.profile_picture
        , username=temp.username, age=temp.age, first_name=temp.first_name, last_name=temp.last_name, role ="Coach")
    
        models.Calendar.objects.filter(username=user.username).delete()
        models.CoachCalendar.objects.create(
            username=coach.username, working_days_hours=working_days_hours)
        coach.save()

        subject = 'Congratulations'
        message = f'Congratulations {coach.first_name} {coach.last_name}, your request to become a coach has been approved. Your password is {password}'
        from_email = 'wellbeingbucket@gmail.com'
        recipient_list = [coach.email]
        print(message)
        print(recipient_list)
        try:
            send_mail(subject= subject, message=message, recipient_list = recipient_list, from_email=from_email)
        except Exception as e:
            print(e)
            
        return True
    except User.DoesNotExist:
        return None


@csrf_exempt
def upgrade(request):
    try:
        if request.method == 'POST':
            body = json.loads(request.body)
            username = body.get('username')
            working_days_hours = body.get('working_days_hours')
            workingHours = body.get('WorkingHours')
            password = body.get('password')
            
            user = authenticate(username=username, password=password)

            users = User.objects.get(username=username)
            if user is not None:
                if users.role == 'USER':
                    if promote_to_coach(user.id, working_days_hours, password):
                        return JsonResponse({'message': 'User upgraded to Coach successfully'}, status=200)
                    else:
                        return JsonResponse({'message': 'User not found'}, status=404)
                else:
                    return JsonResponse({'message': 'Invalid user role'}, status=400)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)


@csrf_exempt
def get_all_coaches(request):
    coaches = Coach.objects.all()
    coach_data = []
    for coach in coaches:
        default_picture_url = settings.MEDIA_URL
        if not coach.profile_picture:
            upload_default_profile_picture()

            coach.profile_picture = 'default_profile_picture.jpg'

        profile_picture_url = f'https://127.0.0.1:8000/{default_picture_url}/{str(coach.profile_picture)}'

        coach_data.append({
            'id': coach.id,
            'username': coach.username,
            'email': coach.email,
            'bio': coach.bio,
            'profession': coach.profession,
            'created_assessments': coach.created_assessments,
            'approved_assessments': coach.approved_assessments,
            'requested_sessions': coach.requested_sessions,
            'support_groups_created': coach.support_groups_created,
            'avg_session_rating': coach.avg_session_rating,
            'profile_picture': profile_picture_url,
        })
    return JsonResponse(coach_data, safe=False)


@csrf_exempt
@api_view(['GET'])
def get_user_favourite_coaches(request):
    try:
        user = User.objects.get(username=request.user)
        favourite_coaches_ids = user.FavouriteCoachesIds
        favourite_coaches = Coach.objects.filter(id__in=favourite_coaches_ids)

        coach_data = []
        for coach in favourite_coaches:
            coach_data.append({
                'id': coach.id,
                'username': coach.user.username,
                'email': coach.user.email,
                'bio': coach.bio,
                'created_assessments': coach.created_assessments,
                'approved_assessments': coach.approved_assessments,
                'requested_sessions': coach.requested_sessions,
                'support_groups_created': coach.support_groups_created,
            })

        return JsonResponse(coach_data, safe=False)

    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)

@api_view(['POST'])
def annonymousName(request):
    if(request.method == 'POST' ) :
        body = json.loads(request.body)
        print(body)
        user = User.objects.get(username=request.user)
        user.annonymous_username = body
        user.save()
        return JsonResponse({"message" : "success"})
    
def getUserByUsername(request, name):

    if Users.objects.filter(username=name).exists():
        user = Users.objects.get(username=name)
        serializer_user = UserSerializer(user)
        return JsonResponse( {"username" : user.username} , safe=False)
    else:
        return JsonResponse({"message" : "no user found"})
    

@csrf_exempt
@api_view(['POST'])
def createPromotionRequest(request):
    data = json.loads(request.body)
    questions = data.get('Questions')
    working_days_hours = data.get('working_days_hours')
    username = request.user
    documents = request.FILES.get('file')
    print(documents)

    existing_request = PromotionRequest.objects.filter(username=username).first()

    if existing_request:
        return JsonResponse({"error": "A promotion request already exists for this user."}, status=400)

    promotion_request = PromotionRequest(
        Questions=questions,
        working_days_hours=working_days_hours,
        username=username,
        documents=documents
    )
    promotion_request.save()

    return JsonResponse({"message": "Promotion request created successfully"}, status=201)


@csrf_exempt
@api_view(['GET'])
@admin_required
def get_promotion_requests(request):
    promotion_requests_list = []
    
    promotion_requests = PromotionRequest.objects.all()
    for request_entry in promotion_requests:
        promotion_requests_list.append({
            'Questions': request_entry.Questions,
            'working_days_hours': request_entry.working_days_hours,
            'username': request_entry.username,
            'documents_url': request_entry.documents.url if request_entry.documents else None,
            'created_at': request_entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    return JsonResponse({"promotion_requests": promotion_requests_list}, status=200)

from django.http import JsonResponse
from .models import PromotionRequest

@api_view(['GET'])
@admin_required
def get_promotion_request_by_username(request, username):
    try:
        promotion_request = PromotionRequest.objects.get(username=username)
        data = {
            'Questions': promotion_request.Questions,
            'working_days_hours': promotion_request.working_days_hours,
            'username': promotion_request.username,
            'documents_url': promotion_request.documents.url if promotion_request.documents else None,
            'created_at': promotion_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            
        }
        return JsonResponse(data , status=200)
    except PromotionRequest.DoesNotExist:
        return JsonResponse({"error": "Promotion request not found"}, status=404)

@api_view(['POST'])
@admin_required
def accept_request(request):
    data = json.loads(request.body)
    username = data.get('username')
    promotion = PromotionRequest.objects.get(username=username)
    user = Users.objects.get(username=username)
    if user is not None:
        if user.role == 'USER':
            if promote_to_coach(user.id, promotion.working_days_hours):
                promotion.delete()

                return JsonResponse({'message': 'User upgraded to Coach successfully'}, status=200)
                
            else:
                return JsonResponse({'message': 'User not found'}, status=400)
        else:
            return JsonResponse({'message': 'Invalid user role'}, status=400)

    else:
    
        return JsonResponse({"message": "user not found"}, status=400)
    
@api_view(['POST'])
@admin_required
def reject_request(request):
    data = json.loads(request.body)
    username = data.get('username')
    user = Users.objects.get(username=username)
    subject = 'Sorry'
    message = f'Sorry {user.first_name} {user.last_name}, your request to become a coach has been rejected.'
    from_email = 'wellbeingbucket@gmail.com'
    recipient_list = [user.email]
    print(message)
    print(recipient_list)
    try:
        send_mail(subject= subject, message=message, recipient_list = recipient_list, from_email=from_email)
    except Exception as e:
        print(e)
            
    promotion = PromotionRequest.objects.get(username=username)
    promotion.delete()
    return JsonResponse({'message': 'Request rejected'}, status=200)

