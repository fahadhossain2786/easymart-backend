from django.urls import path
from .views import login, register

urlpatterns = [
    path('register/', register),
    path('login/', login),
]