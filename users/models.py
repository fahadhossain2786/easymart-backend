from django.contrib.auth.models import AbstractUser
from django.db import models
import re
from django.core.exceptions import ValidationError

def validate_phone(value):
    if not re.match(r"^\+?[0-9]{10,15}$", value):
        raise ValidationError("Enter a valid phone number")

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        unique=True,
        validators=[validate_phone]
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_email_verified = models.BooleanField(default=False)
 
    username = models.CharField(max_length=150, unique=True)
    vendor_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

USERNAME_FIELD = 'email'

REQUIRED_FIELDS = ['username', 'full_name', 'phone']