from django.urls import path
from .views import categories, product_detail, products, pending_products, approve_product, reject_product,add_to_cart,view_cart,update_cart_item,remove_cart_item,checkout, my_orders

urlpatterns = [
    path('categories/', categories),
    path('products/', products),
    path('products/<int:pk>/', product_detail),
    path('admin/pending-products/', pending_products),
    path('admin/approve/<int:pk>/', approve_product),
    path('admin/reject/<int:pk>/', reject_product),
    path('cart/add/<int:product_id>/', add_to_cart),
    path('cart/', view_cart),
    path('cart/update/<int:item_id>/', update_cart_item),
    path('cart/remove/<int:item_id>/', remove_cart_item),
    path('checkout/', checkout),
    path('my-orders/', my_orders),
]