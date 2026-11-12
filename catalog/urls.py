from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorites/<int:product_id>/<str:action>/', views.favorite_update_view, name='favorite_update'),
    path('product/<str:slug>/', views.product_detail_view, name='product_detail'),
]