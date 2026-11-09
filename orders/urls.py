from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/add/', views.cart_add_view, name='cart_add'),
    path('cart/update/<str:item_key>/', views.cart_update_view, name='cart_update'),
    path('cart/remove/<str:item_key>/', views.cart_remove_view, name='cart_remove'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('summary/<uuid:access_token>/', views.order_summary_view, name='order_summary'),
    path('track/', views.order_track_view, name='order_track'),
    path('shipping-label/<uuid:access_token>/', views.shipping_label_view, name='shipping_label'),
]