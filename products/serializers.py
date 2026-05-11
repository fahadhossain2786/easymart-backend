from rest_framework import serializers
from .models import Product, Category ,Cart, CartItem ,Order, OrderItem

# ---------------- CATEGORY ----------------
class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'
class ProductSerializer(serializers.ModelSerializer):

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value

    class Meta:
        model = Product
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order
        fields = '__all__'