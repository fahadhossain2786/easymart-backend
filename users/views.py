from django.contrib.auth import get_user_model, authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import permission_classes
from rest_framework.permissions import BasePermission
from rest_framework import IsAuthenticated
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()


# ---------------- REGISTER ----------------
@api_view(['POST'])
def register(request):
    data = request.data

    full_name = data.get('full_name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    role = data.get('role', 'customer')

    # validation
    if not full_name or not username or not email or not password or not phone:
        return Response({"error": "All fields are required"})

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"})

    if User.objects.filter(phone=phone).exists():
        return Response({"error": "Phone already exists"})

    # create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        role=role
    )

    user.is_active = False
    user.save()

    # ---------------- EMAIL VERIFICATION (FIXED INDENTATION) ----------------

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    verification_link = f"http://127.0.0.1:8000/api/users/verify-email/{uid}/{token}/"

    send_mail(
        subject='Verify your EasyMart account',
        message=f'Click this link to verify your account:\n{verification_link}',
        from_email='admin@easymart.com',
        recipient_list=[user.email],
    )

    return Response({
        "message": "User created successfully. Please verify email to activate account."
    })

# ---------------- LOGIN ----------------
@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(username=email, password=password)

    if user is None:
        return Response({"error": "Invalid credentials"})

    if not user.is_email_verified:
        return Response({"error": "Email not verified"})

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": user.role,
        "full_name": user.full_name
    })

@api_view(['GET'])
def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

    except:
        return Response({"error": "Invalid link"})

    # check token validity
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.is_email_verified = True
        user.save()

        return Response({
            "message": "Email verified successfully. You can now login."
        })

    return Response({"error": "Invalid or expired token"})



class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'vendor'


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_only_view(request):
    if request.user.role != 'admin':
        return Response({"error": "Access denied"})

    return Response({"message": "Welcome Admin"})