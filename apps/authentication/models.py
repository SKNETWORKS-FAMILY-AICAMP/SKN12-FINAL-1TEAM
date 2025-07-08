"""
Authentication models for QA Chatbot System
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    사용자 모델 - Django 기본 User 모델 확장
    """
    email = models.EmailField(unique=True, verbose_name='이메일')
    phone = models.CharField(max_length=20, blank=True, verbose_name='전화번호')
    department = models.CharField(max_length=100, blank=True, verbose_name='부서')
    position = models.CharField(max_length=100, blank=True, verbose_name='직책')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='가입일')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='마지막 로그인')
    
    # 추가 필드
    profile_image = models.ImageField(
        upload_to='profiles/', 
        blank=True, 
        null=True, 
        verbose_name='프로필 이미지'
    )
    bio = models.TextField(blank=True, verbose_name='자기소개')
    preferences = models.JSONField(default=dict, verbose_name='사용자 설정')
    
    # AbstractUser의 groups와 user_permissions 필드에 related_name 추가
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
        
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name


class UserSession(models.Model):
    """
    사용자 세션 모델 - 활성 세션 추적
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    session_key = models.CharField(max_length=40, unique=True, verbose_name='세션 키')
    ip_address = models.GenericIPAddressField(verbose_name='IP 주소')
    user_agent = models.TextField(verbose_name='사용자 에이전트')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='마지막 활동')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = '사용자 세션'
        verbose_name_plural = '사용자 세션들'
        
    def __str__(self):
        return f"{self.user.email} - {self.session_key[:10]}..."


class UserProfile(models.Model):
    """
    사용자 프로필 모델 - 추가 정보 저장
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='사용자')
    company = models.CharField(max_length=200, blank=True, verbose_name='회사')
    industry = models.CharField(max_length=100, blank=True, verbose_name='업계')
    experience_years = models.IntegerField(default=0, verbose_name='경력 년수')
    specialization = models.CharField(max_length=200, blank=True, verbose_name='전문 분야')
    interests = models.JSONField(default=list, verbose_name='관심사')
    language_preference = models.CharField(max_length=10, default='ko', verbose_name='언어 설정')
    timezone = models.CharField(max_length=50, default='Asia/Seoul', verbose_name='시간대')
    notification_settings = models.JSONField(default=dict, verbose_name='알림 설정')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필들'
        
    def __str__(self):
        return f"{self.user.email} Profile" 