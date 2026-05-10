from django.urls import path
from .views import categories, product_detail, products, pending_products, approve_product, reject_product

urlpatterns = [
    path('categories/', categories),
    path('products/', products),
    path('products/<int:pk>/', product_detail),
    path('admin/pending-products/', pending_products),
    path('admin/approve/<int:pk>/', approve_product),
    path('admin/reject/<int:pk>/', reject_product),
]