"""
Authentication URLs for QA Chatbot System
"""
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # 사용자 등록/로그인/로그아웃
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    
    # 사용자 정보
    path('user/', views.UserProfileView.as_view(), name='user_profile'),
    path('user/info/', views.user_info, name='user_info'),
    path('user/profile/', views.UserProfileDetailView.as_view(), name='user_profile_detail'),
    
    # 비밀번호 변경
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # 세션 관리
    path('sessions/', views.UserSessionsView.as_view(), name='user_sessions'),
    
    # 토큰 갱신
    path('token/refresh/', views.refresh_token, name='token_refresh'),
] 