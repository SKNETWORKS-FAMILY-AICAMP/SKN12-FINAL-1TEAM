"""
Chat models for QA Chatbot System
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class ChatSession(models.Model):
    """
    채팅 세션 모델
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    title = models.CharField(max_length=200, blank=True, verbose_name='세션 제목')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    class Meta:
        db_table = 'chat_sessions'
        verbose_name = '채팅 세션'
        verbose_name_plural = '채팅 세션들'
        
    def __str__(self):
        return f"{self.user.email} - {self.title or 'Untitled'}"


class ChatMessage(models.Model):
    """
    채팅 메시지 모델
    """
    MESSAGE_TYPES = [
        ('user', '사용자'),
        ('assistant', '어시스턴트'),
        ('system', '시스템'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, verbose_name='메시지 타입')
    content = models.TextField(verbose_name='메시지 내용')
    metadata = models.JSONField(default=dict, verbose_name='메타데이터')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        db_table = 'chat_messages'
        verbose_name = '채팅 메시지'
        verbose_name_plural = '채팅 메시지들'
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.session.title} - {self.message_type}: {self.content[:50]}..." 