from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('rules/', views.rules_view, name='rules'),
]