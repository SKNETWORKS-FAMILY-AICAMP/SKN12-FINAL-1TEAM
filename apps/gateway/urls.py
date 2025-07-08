"""
Gateway URLs for QA Chatbot System
"""
from django.urls import path
from . import views

app_name = 'gateway'

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('health/', views.health_check, name='health_check_detail'),
    path('orchestrate/', views.orchestrate_query, name='orchestrate_query'),
    path('services/status/', views.microservices_status, name='microservices_status'),
] 