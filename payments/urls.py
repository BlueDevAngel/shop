from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('start/<uuid:access_token>/', views.start_payment_view, name='start_payment'),
    path('verify/<uuid:access_token>/', views.verify_payment_view, name='verify_payment'),
    path('result/<uuid:access_token>/', views.payment_result_view, name='payment_result'),
]