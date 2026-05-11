from django.urls import path
from .views import login, my_notifications, my_profile, payment_slip, purchase_history, read_notification, register , verify_email, assign_vendor_code
from rest_framework.decorators import api_view
from .views import admin_dashboard

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('verify-email/<uidb64>/<token>/', verify_email, name='verify-email'),
    path('admin/dashboard/', admin_dashboard),
    path('notifications/', my_notifications),
    path('notifications/read/<int:pk>/', read_notification),
    path('purchase-history/', purchase_history),
    path('payment-slip/<int:order_id>/', payment_slip),
    path('admin/assign-vendor/<int:user_id>/', assign_vendor_code),
    path('profile/', my_profile),
]   
