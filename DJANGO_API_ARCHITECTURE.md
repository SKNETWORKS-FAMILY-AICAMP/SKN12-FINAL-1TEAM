# 🏗️ Django API 아키텍처 가이드

## 📋 **전체 아키텍처 개요**

Narutalk의 Django 백엔드는 모듈화된 앱 구조로 설계되어 있으며, REST API와 WebSocket을 통해 프론트엔드와 통신합니다.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Client  │◄──►│   Django API    │◄──►│   Database      │
│   (Port 3000)   │    │   (Port 8000)   │    │   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   FastAPI       │    │   AI Services   │
│   (Real-time)   │    │   (Port 8001)   │    │   (LangGraph)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 **Django 설정 구조**

### **config/settings/** - 환경별 설정 관리

#### **base.py** - 기본 공통 설정
```python
# 기본 Django 설정
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# 서드파티 앱
THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'drf_spectacular',
]

# 로컬 앱
LOCAL_APPS = [
    'apps.authentication',
    'apps.chat',
    'apps.gateway',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
```

#### **development.py** - 개발 환경 설정
```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# 개발용 데이터베이스
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'databases' / 'db.sqlite3',
    }
}
```

### **config/urls.py** - 메인 URL 라우팅
```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # 관리자
    path('admin/', admin.site.urls),
    
    # API 문서
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
    
    # 앱 URL 포함
    path('api/auth/', include('apps.authentication.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/', include('apps.gateway.urls')),
]
```

### **config/asgi.py** - WebSocket 설정
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.chat.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

## 🔐 **인증 시스템 (apps/authentication/)**

### **models.py** - 사용자 모델
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """커스텀 사용자 모델"""
    ROLE_CHOICES = [
        ('admin', '관리자'),
        ('doctor', '의사'),
        ('nurse', '간호사'),
        ('user', '일반 사용자'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="custom_user_set", 
        related_query_name="custom_user",
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
```

### **serializers.py** - API 직렬화
```python
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'department', 'is_verified']
        read_only_fields = ['id', 'is_verified']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'role', 'department']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user
```

### **views.py** - API 뷰
```python
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, CustomTokenObtainPairSerializer, UserRegistrationSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """사용자 대시보드 데이터"""
    user = request.user
    data = {
        'user': UserSerializer(user).data,
        'recent_chats': 5,  # 최근 채팅 수
        'total_messages': 150,  # 총 메시지 수
    }
    return Response(data)
```

### **urls.py** - URL 라우팅
```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    UserProfileView,
    user_dashboard
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
]
```

## 💬 **채팅 시스템 (apps/chat/)**

### **models.py** - 채팅 모델
```python
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ChatSession(models.Model):
    """채팅 세션"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=[
        ('medical', '의료 상담'),
        ('general', '일반 문의'),
        ('emergency', '응급'),
        ('consultation', '진료 상담'),
    ], default='general')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

class Message(models.Model):
    """채팅 메시지"""
    MESSAGE_TYPES = [
        ('text', '텍스트'),
        ('image', '이미지'),
        ('file', '파일'),
        ('error', '오류'),
    ]
    
    SENDER_TYPES = [
        ('user', '사용자'),
        ('ai', 'AI'),
        ('system', '시스템'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_TYPES)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']
```

### **serializers.py** - 채팅 직렬화
```python
from rest_framework import serializers
from .models import ChatSession, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'message_type', 'metadata', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'category', 'created_at', 'updated_at', 'is_active', 
                 'messages', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()

class ChatSessionListSerializer(serializers.ModelSerializer):
    """세션 목록용 간소화된 직렬화기"""
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'category', 'created_at', 'updated_at', 
                 'last_message', 'message_count']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        return MessageSerializer(last_msg).data if last_msg else None
    
    def get_message_count(self, obj):
        return obj.messages.count()
```

### **consumers.py** - WebSocket 컨슈머
```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatSession, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        
        # 방에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # 방에서 나가기
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        sender = text_data_json.get('sender', 'user')
        
        # 메시지 데이터베이스에 저장
        message = await self.save_message(message_content, sender)
        
        # 그룹에 메시지 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender': sender,
                'timestamp': str(message.timestamp),
                'message_id': str(message.id)
            }
        )
        
        # AI 응답 처리 (사용자 메시지인 경우)
        if sender == 'user':
            await self.process_ai_response(message_content)
    
    async def chat_message(self, event):
        # WebSocket으로 메시지 전송
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))
    
    @database_sync_to_async
    def save_message(self, content, sender):
        session = ChatSession.objects.get(id=self.session_id)
        return Message.objects.create(
            session=session,
            content=content,
            sender=sender
        )
    
    async def process_ai_response(self, user_message):
        # AI 처리 로직 (LangGraph 연동)
        ai_response = await self.get_ai_response(user_message)
        
        # AI 응답 저장
        ai_message = await self.save_message(ai_response, 'ai')
        
        # AI 응답 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': ai_response,
                'sender': 'ai',
                'timestamp': str(ai_message.timestamp),
                'message_id': str(ai_message.id)
            }
        )
    
    async def get_ai_response(self, message):
        # LangGraph AI 서비스 호출
        # 실제 구현에서는 langgraph_orchestrator와 연동
        return f"AI 응답: {message}에 대한 의료 정보를 제공합니다."
```

### **routing.py** - WebSocket 라우팅
```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<session_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]
```

## 🌐 **API 게이트웨이 (apps/gateway/)**

### **middleware.py** - 커스텀 미들웨어
```python
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class APILoggingMiddleware(MiddlewareMixin):
    """API 요청 로깅 미들웨어"""
    
    def process_request(self, request):
        request.start_time = time.time()
        
        # API 요청 로깅
        if request.path.startswith('/api/'):
            logger.info(f"API Request: {request.method} {request.path}")
        
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            if request.path.startswith('/api/'):
                logger.info(
                    f"API Response: {request.method} {request.path} "
                    f"- {response.status_code} - {duration:.2f}s"
                )
        
        return response

class CORSHeadersMiddleware(MiddlewareMixin):
    """CORS 헤더 추가 미들웨어"""
    
    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response
```

### **views.py** - 게이트웨이 뷰
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests

@api_view(['GET'])
def health_check(request):
    """시스템 상태 확인"""
    return Response({
        'status': 'healthy',
        'services': {
            'django': 'running',
            'database': 'connected',
            'ai_service': 'available'
        }
    })

@api_view(['POST'])
def proxy_to_fastapi(request):
    """FastAPI 마이크로서비스 프록시"""
    try:
        response = requests.post(
            'http://localhost:8001/api/search/',
            json=request.data,
            timeout=30
        )
        return Response(response.json(), status=response.status_code)
    except requests.RequestException as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
```

## 📊 **REST Framework 설정**

### **settings/base.py** - DRF 설정
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT 설정
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# API 문서화 설정
SPECTACULAR_SETTINGS = {
    'TITLE': 'Narutalk API',
    'DESCRIPTION': '의료업계 QA 챗봇 시스템 API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

## 🔄 **API 엔드포인트 매핑**

### **인증 API** (`/api/auth/`)
- `POST /api/auth/login/` - 로그인
- `POST /api/auth/token/refresh/` - 토큰 갱신
- `POST /api/auth/register/` - 회원가입
- `GET /api/auth/profile/` - 사용자 프로필 조회
- `PUT /api/auth/profile/` - 사용자 프로필 수정
- `GET /api/auth/dashboard/` - 사용자 대시보드

### **채팅 API** (`/api/chat/`)
- `GET /api/chat/sessions/` - 채팅 세션 목록
- `POST /api/chat/sessions/` - 새 채팅 세션 생성
- `GET /api/chat/sessions/{id}/` - 특정 세션 조회
- `DELETE /api/chat/sessions/{id}/` - 세션 삭제
- `GET /api/chat/sessions/{id}/messages/` - 세션 메시지 목록
- `POST /api/chat/sessions/{id}/messages/` - 새 메시지 전송

### **게이트웨이 API** (`/api/`)
- `GET /api/health/` - 시스템 상태 확인
- `POST /api/proxy/search/` - 검색 서비스 프록시

### **WebSocket** (`ws://`)
- `ws://localhost:8000/ws/chat/{session_id}/` - 실시간 채팅

이 구조는 확장 가능하고 유지보수가 용이하도록 설계되었으며, REST API와 WebSocket을 통해 실시간 의료 상담 서비스를 제공합니다. 