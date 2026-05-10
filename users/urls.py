from django.urls import path
from .views import login, register , verify_email, assign_vendor_code
from rest_framework.decorators import api_view
from .views import admin_dashboard

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('verify-email/<uidb64>/<token>/', verify_email, name='verify-email'),
    path('admin/dashboard/', admin_dashboard),
    path('admin/assign-vendor/<int:user_id>/', assign_vendor_code),
]