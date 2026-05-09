from django.contrib.auth import get_user_model, authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

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
    if not full_name:
        return Response({"error": "Full name is required"})

    if not username:
        return Response({"error": "Username is required"})

    if not email:
        return Response({"error": "Email is required"})

    if not password:
        return Response({"error": "Password is required"})

    if not phone:
        return Response({"error": "Phone is required"})
    
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

    user.is_active = False  # email verification later
    user.save()

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