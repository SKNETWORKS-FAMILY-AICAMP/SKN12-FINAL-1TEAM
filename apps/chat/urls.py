"""
Chat URLs for QA Chatbot System
"""
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('sessions/', views.ChatSessionListView.as_view(), name='chat_sessions'),
    path('send/', views.send_message, name='send_message'),
] 