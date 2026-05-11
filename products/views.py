from django.db.models import Q
from django.db.models import Sum, F
from django.db import transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sslcommerz_lib import SSLCOMMERZ
from .models import Commission, Product, Category, Cart, CartItem, Order, OrderItem, Payment, Notification
from .serializers import ProductSerializer, CategorySerializer, CartSerializer, CartItemSerializer,OrderSerializer, OrderItemSerializer
from users.models import User, Address
from decimal import Decimal


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def categories(request):

    # ---------------- GET (ONLY APPROVED) ----------------
    
    if request.method == 'GET':
        cats = Category.objects.filter(is_approved=True)
        return Response(CategorySerializer(cats, many=True).data)

    # ---------------- CREATE CATEGORY / SUBCATEGORY ----------------
    data = request.data.copy()
    data['created_by'] = request.user.id

    serializer = CategorySerializer(data=data)

    if serializer.is_valid():
        obj = serializer.save()

        # vendor-created → needs approval
        if request.user.role == 'vendor':
            obj.is_approved = False
        else:
            obj.is_approved = True

        obj.save()
        return Response(serializer.data)

    return Response(serializer.errors)

 # Catagory admin control
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_categories(request):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    cats = Category.objects.filter(is_approved=False)
    return Response(CategorySerializer(cats, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_category(request, pk):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    cat = Category.objects.get(pk=pk)
    cat.is_approved = True
    cat.save()

    return Response({"message": "Category approved"})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def reject_category(request, pk):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    Category.objects.get(pk=pk).delete()

    return Response({"message": "Category rejected"})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def products(request):

    # ---------------- GET (SEARCH + LIST) ----------------
    if request.method == 'GET':

        query = request.GET.get('search', '')

        products = Product.objects.filter(is_approved=True)

        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(category__name__icontains=query) |
                Q(category__parent__name__icontains=query)
            )

        return Response(ProductSerializer(products, many=True).data)

    # ---------------- CREATE PRODUCT (VENDOR ONLY) ----------------
    if request.user.role != 'vendor':
        return Response({"error": "Only vendors allowed"})

    data = request.data.copy()
    data['vendor'] = request.user.id
    data['is_approved'] = False

    serializer = ProductSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def product_detail(request, pk):

    try:
        product = Product.objects.get(pk=pk)
    except:
        return Response({"error": "Not found"})

    if request.user.role != 'admin' and product.vendor != request.user:
        return Response({"error": "Not allowed"})

    # ---------------- UPDATE ----------------
    if request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            obj = serializer.save()

            # vendor edit → re-approval required
            if request.user.role == 'vendor':
                obj.is_approved = False
                obj.save()

            return Response(serializer.data)

        return Response(serializer.errors)

    # ---------------- DELETE ----------------
    product.delete()
    return Response({"message": "Deleted"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_products(request):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    products = Product.objects.filter(is_approved=False)
    return Response(ProductSerializer(products, many=True).data)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_product(request, pk):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    product = Product.objects.get(pk=pk)
    product.is_approved = True
    product.save()

    return Response({"message": "Product approved"})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def reject_product(request, pk):

    if request.user.role != 'admin':
        return Response({"error": "Only admin allowed"})

    Product.objects.get(pk=pk).delete()

    return Response({"message": "Product rejected"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request, product_id):

    try:
        product = Product.objects.get(
            id=product_id,
            is_approved=True
        )
    except:
        return Response({"error": "Product not found"})

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if not created:
        cart_item.quantity += 1

    cart_item.save()

    return Response({
        "message": "Added to cart"
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    serializer = CartSerializer(cart)

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):

    try:
        item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )
    except:
        return Response({"error": "Item not found"})

    quantity = request.data.get('quantity')

    if not quantity or int(quantity) < 1:
        return Response({"error": "Invalid quantity"})

    item.quantity = quantity
    item.save()

    return Response({
        "message": "Cart updated"
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):

    try:
        item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )
    except:
        return Response({"error": "Item not found"})

    item.delete()

    return Response({
        "message": "Item removed"
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):

    cart_items = CartItem.objects.filter(cart__user=request.user)

    if not cart_items.exists():
        return Response({"error": "Cart is empty"})

    address = Address.objects.filter(
        user=request.user,
        is_default=True
    ).first()

    with transaction.atomic():

        # ---------------- CREATE ORDER ----------------
        order = Order.objects.create(
            user=request.user,
            full_name=address.full_name if address else request.user.full_name,
            phone=address.phone if address else request.user.phone,
            address=address.address if address else "No address",
            status="pending",
            total_price=0
        )

        total = 0

        # ---------------- CREATE ORDER ITEMS ----------------
        for item in cart_items:

            # stock check (IMPORTANT IMPROVEMENT)
            if item.product.stock < item.quantity:
                raise Exception(f"Not enough stock for {item.product.name}")

            subtotal = item.product.price * item.quantity
            total += subtotal

            OrderItem.objects.create(
                order=order,
                product=item.product,
                vendor=item.product.vendor,
                quantity=item.quantity,
                price=item.product.price
            )

            # reduce stock
            item.product.stock -= item.quantity
            item.product.save()

        # ---------------- FINAL UPDATE ----------------
        order.total_price = total
        order.save()

        # ---------------- CLEAR CART ----------------
        cart_items.delete()

    return Response({
        "message": "Checkout successful",
        "order_id": order.id,
        "total_price": total,
        "next": "Create payment"
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by('-id')

    serializer = OrderSerializer(
        orders,
        many=True
    )

    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request, order_id):

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except:
        return Response({"error": "Order not found"})

    # ✅ use env/settings instead of hardcode
    sslcz_settings = {
        'store_id': settings.SSLC_STORE_ID,
        'store_pass': settings.SSLC_STORE_PASSWORD,
        'issandbox': settings.SSLC_SANDBOX
    }

    sslcz = SSLCOMMERZ(sslcz_settings)

    data = {
        'total_amount': float(order.total_price),
        'currency': "BDT",
        'tran_id': f"EZMART_{order.id}",

        'success_url': "http://127.0.0.1:8000/api/payment/success/",
        'fail_url': "http://127.0.0.1:8000/api/payment/fail/",
        'cancel_url': "http://127.0.0.1:8000/api/payment/cancel/",

        # ❗ FIXED: use user data, not order fields
        'cus_name': request.user.full_name,
        'cus_email': request.user.email,
        'cus_phone': request.user.phone if hasattr(request.user, "phone") else "N/A",

        'shipping_method': "NO",
        'product_name': "EasyMart Order",
        'product_category': "General",
        'product_profile': "general"
    }

    response = sslcz.createSession(data)

    return Response({
        "payment_url": response['GatewayPageURL']
    })
from django.db import transaction
from decimal import Decimal

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_success(request):

    tran_id = request.data.get("tran_id")

    if not tran_id:
        return Response({"error": "Transaction ID missing"})

    try:
        order_id = tran_id.split("_")[1]
        order = Order.objects.get(id=order_id)
    except:
        return Response({"error": "Order not found"})

    # 🚨 Prevent duplicate payment
    if Payment.objects.filter(order=order).exists():
        return Response({"message": "Already paid"})

    # 🔒 TRANSACTION SAFETY START
    with transaction.atomic():

        # 1. Create Payment
        Payment.objects.create(
            order=order,
            amount=order.total_price,
            status="success",
            transaction_id=tran_id,
            method="sslcommerz"
        )

        # 2. Update Order
        order.status = "paid"
        order.save()

        # 3. Commission calculation
        total = order.total_price
        platform_fee = total * Decimal("0.10")
        vendor_amount = total - platform_fee

        Commission.objects.create(
            order=order,
            amount=total,
            platform_fee=platform_fee,
            vendor_amount=vendor_amount
        )

        # 4. Notification
        Notification.objects.create(
            user=order.user,
            title="Payment Successful",
            message=f"Your payment for Order #{order.id} was successful."
        )

    # 🔒 TRANSACTION END

    return Response({
        "message": "Payment successful",
        "order_id": order.id,
        "status": order.status
    })

@csrf_exempt
@api_view(['POST'])
def payment_fail(request):

    tran_id = request.data.get("tran_id")

    if tran_id:
        try:
            order_id = tran_id.split("_")[1]
            order = Order.objects.get(id=order_id)

            order.status = "failed"
            order.save()

        except:
            pass

    return Response({
        "message": "Payment failed"
    })
@csrf_exempt
@api_view(['POST'])
def payment_cancel(request):

    tran_id = request.data.get("tran_id")

    if tran_id:
        try:
            order_id = tran_id.split("_")[1]
            order = Order.objects.get(id=order_id)

            order.status = "cancelled"
            order.save()

        except:
            pass

    return Response({
        "message": "Payment cancelled"
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_dashboard(request):

    if request.user.role != 'vendor':
        return Response({"error": "Only vendors allowed"})

    products = Product.objects.filter(vendor=request.user)

    total_products = products.count()

    approved_products = products.filter(
        is_approved=True
    ).count()

    pending_products = products.filter(
        is_approved=False
    ).count()

    order_items = OrderItem.objects.filter(
        product__vendor=request.user,
        order__status='paid'
    )

    total_orders = order_items.values(
        'order'
    ).distinct().count()

    total_sales = order_items.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0

    vendor_commission = total_sales * Decimal("0.90")

    return Response({

        "products": {
            "total": total_products,
            "approved": approved_products,
            "pending": pending_products
        },

        "orders": {
            "total_orders": total_orders
        },

        "earnings": {
            "gross_sales": total_sales,
            "vendor_income": vendor_commission
        }
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_orders(request):

    if request.user.role != 'vendor':
        return Response({"error": "Only vendors allowed"})

    items = OrderItem.objects.filter(product__vendor=request.user)

    data = []

    for item in items:
        data.append({
            "order_id": item.order.id,
            "product": item.product.name,
            "quantity": item.quantity,
            "price": item.price,
            "customer": item.order.user.email,
            "status": item.order.status
        })

    return Response(data)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def addresses(request):

    # ---------------- GET ----------------
    if request.method == 'GET':

        data = Address.objects.filter(user=request.user).order_by('-id')

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

    # ---------------- POST (CREATE) ----------------
    data = request.data

    # validation
    if not data.get("full_name") or not data.get("phone") or not data.get("address"):
        return Response({
            "error": "full_name, phone and address are required"
        })

    # OPTIONAL: only one default address
    if data.get("is_default", False):
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

    address = Address.objects.create(
        user=request.user,
        full_name=data.get("full_name"),
        phone=data.get("phone"),
        address=data.get("address"),
        city=data.get("city", ""),
        postal_code=data.get("postal_code", ""),
        is_default=data.get("is_default", False)
    )

    return Response({
        "message": "Address added successfully",
        "id": address.id
    })