"""
Authentication serializers for QA Chatbot System
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, UserSession


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    사용자 등록 시리얼라이저
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'password', 'password_confirm', 'phone', 'department', 'position'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    사용자 로그인 시리얼라이저
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
            
            if not user.is_active:
                raise serializers.ValidationError("계정이 비활성화되었습니다.")
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError("이메일과 비밀번호를 모두 입력해주세요.")


class UserSerializer(serializers.ModelSerializer):
    """
    사용자 정보 시리얼라이저
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone', 'department', 'position', 'is_active', 'date_joined',
            'profile_image', 'bio', 'preferences', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']
    
    def get_profile(self, obj):
        try:
            profile = obj.userprofile
            return UserProfileSerializer(profile).data
        except UserProfile.DoesNotExist:
            return None


class UserProfileSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 시리얼라이저
    """
    class Meta:
        model = UserProfile
        fields = [
            'company', 'industry', 'experience_years', 'specialization',
            'interests', 'language_preference', 'timezone', 'notification_settings'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults=validated_data
        )
        if not created:
            for attr, value in validated_data.items():
                setattr(profile, attr, value)
            profile.save()
        return profile


class UserSessionSerializer(serializers.ModelSerializer):
    """
    사용자 세션 시리얼라이저
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'session_key', 'user_email', 'ip_address', 'user_agent',
            'created_at', 'last_activity', 'is_active'
        ]
        read_only_fields = ['created_at', 'last_activity']


class PasswordChangeSerializer(serializers.Serializer):
    """
    비밀번호 변경 시리얼라이저
    """
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("기존 비밀번호가 올바르지 않습니다.")
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user 