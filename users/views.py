from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product, Category

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

    if not all([full_name, username, email, password, phone]):
        return Response({"error": "All fields required"})

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email exists"})

    if User.objects.filter(phone=phone).exists():
        return Response({"error": "Phone exists"})

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

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    link = f"http://127.0.0.1:8000/api/users/verify-email/{uid}/{token}/"

    send_mail(
        "Verify Account",
        f"Click: {link}",
        "admin@easymart.com",
        [email]
    )

    return Response({"message": "Check email to verify account"})


# ---------------- EMAIL VERIFY ----------------
@api_view(['GET'])
def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        return Response({"error": "Invalid link"})

    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.is_email_verified = True
        user.save()
        return Response({"message": "Verified successfully"})

    return Response({"error": "Invalid token"})


# ---------------- LOGIN ----------------
@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(username=email, password=password)

    if not user:
        return Response({"error": "Invalid credentials"})

    if not user.is_email_verified:
        return Response({"error": "Email not verified"})

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "role": user.role,
        "name": user.full_name
    })


# ---------------- ADMIN DASHBOARD ----------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    return Response({
        "users": {
            "total": User.objects.count(),
            "vendors": User.objects.filter(role='vendor').count(),
            "customers": User.objects.filter(role='customer').count(),
            "vendors_without_code": User.objects.filter(role='vendor', vendor_code__isnull=True).count()
        },
        "products": {
            "total": Product.objects.count(),
            "pending": Product.objects.filter(is_approved=False).count(),
            "approved": Product.objects.filter(is_approved=True).count()
        },
        "categories": {
            "main": Category.objects.filter(parent=None).count(),
            "sub": Category.objects.exclude(parent=None).count()
        }
    })


# ---------------- VENDOR CODE ----------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_vendor_code(request, user_id):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    user = User.objects.get(id=user_id)

    if user.role != 'vendor':
        return Response({"error": "Not vendor"})

    user.vendor_code = request.data.get('vendor_code')
    user.save()

    return Response({"message": "Vendor code assigned"})


# ---------------- PERMISSIONS ----------------
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'vendor'