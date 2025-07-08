"""
Authentication views for QA Chatbot System
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import User, UserProfile, UserSession
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserSerializer, 
    UserProfileSerializer,
    UserSessionSerializer,
    PasswordChangeSerializer
)


class UserRegistrationView(generics.CreateAPIView):
    """
    사용자 등록 API
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="사용자 등록",
        description="새로운 사용자를 등록합니다.",
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            
            # 사용자 프로필 생성
            UserProfile.objects.create(user=user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': '회원가입이 완료되었습니다.'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    사용자 로그인 API
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="사용자 로그인",
        description="사용자 로그인을 수행합니다.",
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # 세션 생성
            login(request, user)
            
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            
            # 사용자 세션 기록
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # 마지막 로그인 시간 업데이트
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': '로그인이 완료되었습니다.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """
    사용자 로그아웃 API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="사용자 로그아웃",
        description="사용자 로그아웃을 수행합니다.",
        tags=["Authentication"]
    )
    def post(self, request):
        try:
            # 세션 비활성화
            if hasattr(request, 'session'):
                UserSession.objects.filter(
                    user=request.user,
                    session_key=request.session.session_key
                ).update(is_active=False)
            
            # 로그아웃
            logout(request)
            
            return Response({
                'message': '로그아웃이 완료되었습니다.'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': '로그아웃 중 오류가 발생했습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    사용자 프로필 조회/수정 API
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    @extend_schema(
        summary="사용자 프로필 조회",
        description="현재 로그인한 사용자의 프로필을 조회합니다.",
        tags=["Authentication"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="사용자 프로필 수정",
        description="현재 로그인한 사용자의 프로필을 수정합니다.",
        tags=["Authentication"]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="사용자 프로필 부분 수정",
        description="현재 로그인한 사용자의 프로필을 부분적으로 수정합니다.",
        tags=["Authentication"]
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    사용자 상세 프로필 API
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    @extend_schema(
        summary="사용자 상세 프로필 조회",
        description="현재 로그인한 사용자의 상세 프로필을 조회합니다.",
        tags=["Authentication"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="사용자 상세 프로필 수정",
        description="현재 로그인한 사용자의 상세 프로필을 수정합니다.",
        tags=["Authentication"]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)


class PasswordChangeView(APIView):
    """
    비밀번호 변경 API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="비밀번호 변경",
        description="현재 로그인한 사용자의 비밀번호를 변경합니다.",
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': '비밀번호가 성공적으로 변경되었습니다.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionsView(generics.ListAPIView):
    """
    사용자 세션 목록 API
    """
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user, is_active=True)
    
    @extend_schema(
        summary="사용자 세션 목록 조회",
        description="현재 로그인한 사용자의 활성 세션 목록을 조회합니다.",
        tags=["Authentication"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_info(request):
    """
    사용자 정보 조회 API (간단한 버전)
    """
    user = request.user
    return Response({
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'full_name': user.get_full_name(),
        'is_active': user.is_active,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_token(request):
    """
    JWT 토큰 갱신 API
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        access_token = token.access_token
        
        return Response({
            'access': str(access_token),
            'refresh': str(token)
        })
    except Exception as e:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED) 