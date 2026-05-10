from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer



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