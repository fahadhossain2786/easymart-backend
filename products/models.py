from django.db import models
from users.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    is_approved = models.BooleanField(default=False)  # 🔥 NEW

    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    


# ---------------- CART ----------------
class Cart(models.Model):
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# ---------------- CART ITEM ----------------
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.product.name
    

# ---------------- ORDER ----------------
class Order(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id}"


# ---------------- ORDER ITEM ----------------
class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    vendor = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.product.name