from django.urls import path
from .views import login, register , verify_email
from rest_framework.decorators import api_view

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('verify-email/<uidb64>/<token>/', verify_email, name='verify-email'),
]