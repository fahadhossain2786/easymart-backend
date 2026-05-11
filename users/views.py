from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Sum, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Commission, Notification, Order, OrderItem, Payment, Product, Category

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
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_notifications(request):

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-id')

    data = []

    for n in notifications:
        data.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at
        })

    return Response(data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def read_notification(request, pk):

    try:
        notification = Notification.objects.get(
            id=pk,
            user=request.user
        )
    except:
        return Response({"error": "Notification not found"})

    notification.is_read = True
    notification.save()

    return Response({
        "message": "Notification marked as read"
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def purchase_history(request):

    orders = Order.objects.filter(
        user=request.user,
        status='paid'
    ).order_by('-id')

    data = []

    for order in orders:

        items = OrderItem.objects.filter(order=order)

        products = []

        for item in items:
            products.append({
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price": item.price
            })

        data.append({
            "order_id": order.id,
            "total_price": order.total_price,
            "status": order.status,
            "products": products
        })

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_slip(request, order_id):

    try:
        order = Order.objects.get(
            id=order_id,
            user=request.user
        )
    except:
        return Response({"error": "Order not found"})

    try:
        payment = Payment.objects.get(order=order)
    except:
        return Response({"error": "Payment not found"})

    items = OrderItem.objects.filter(order=order)

    products = []

    for item in items:
        products.append({
            "product": item.product.name,
            "quantity": item.quantity,
            "price": item.price
        })

    return Response({

        "invoice": {
            "order_id": order.id,
            "transaction_id": payment.transaction_id,
            "payment_method": payment.method,
            "payment_status": payment.status,
            "total_paid": payment.amount
        },

        "products": products
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    total_users = User.objects.count()
    total_vendors = User.objects.filter(role='vendor').count()
    total_customers = User.objects.filter(role='customer').count()

    total_products = Product.objects.count()
    approved_products = Product.objects.filter(is_approved=True).count()
    pending_products = Product.objects.filter(is_approved=False).count()

    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(status='paid').count()

    total_revenue = Order.objects.filter(
        status='paid'
    ).aggregate(
        total= Sum('total_price')
    )['total'] or 0

    total_commission = Commission.objects.aggregate(
        total=Sum('platform_fee')
    )['total'] or 0

    return Response({

        "users": {
            "total": total_users,
            "vendors": total_vendors,
            "customers": total_customers
        },

        "products": {
            "total": total_products,
            "approved": approved_products,
            "pending": pending_products
        },

        "orders": {
            "total": total_orders,
            "paid": paid_orders
        },

        "revenue": {
            "total": total_revenue
        },

        "platform_earnings": total_commission
    })
    

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def my_profile(request):

    user = request.user

    # ---------------- GET PROFILE ----------------
    if request.method == 'GET':
        return Response({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "vendor_code": user.vendor_code
        })

    # ---------------- UPDATE PROFILE ----------------
    data = request.data

    user.full_name = data.get("full_name", user.full_name)
    user.phone = data.get("phone", user.phone)

    user.save()

    return Response({
        "message": "Profile updated successfully"
    })

from .models import Address

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def addresses(request):

    # ---------------- GET ADDRESSES ----------------
    if request.method == 'GET':
        data = Address.objects.filter(user=request.user)

        return Response([
            {
                "id": a.id,
                "full_name": a.full_name,
                "phone": a.phone,
                "address": a.address,
                "city": a.city,
                "postal_code": a.postal_code,
                "is_default": a.is_default
            }
            for a in data
        ])

    # ---------------- CREATE ADDRESS ----------------
    data = request.data

    # if this is first address → make default
    is_default = not Address.objects.filter(user=request.user).exists()

    Address.objects.create(
        user=request.user,
        full_name=data.get("full_name"),
        phone=data.get("phone"),
        address=data.get("address"),
        city=data.get("city"),
        postal_code=data.get("postal_code"),
        is_default=is_default
    )

    return Response({"message": "Address added successfully"})