"""
Chat views for QA Chatbot System
"""
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import ChatSession, ChatMessage


class ChatSessionListView(generics.ListCreateAPIView):
    """
    채팅 세션 목록 조회 및 생성 API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user, is_active=True)
    
    @extend_schema(
        summary="채팅 세션 목록 조회",
        description="현재 사용자의 채팅 세션 목록을 조회합니다.",
        tags=["Chat"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="새 채팅 세션 생성",
        description="새로운 채팅 세션을 생성합니다.",
        tags=["Chat"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request):
    """
    메시지 전송 API
    """
    try:
        session_id = request.data.get('session_id')
        content = request.data.get('content')
        
        if not session_id or not content:
            return Response({'error': 'session_id and content are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 여기서 LangGraph 오케스트레이터를 호출하여 메시지 처리
        # 실제 구현에서는 services.langgraph_service 를 사용
        
        return Response({
            'message': 'Message sent successfully',
            'session_id': session_id,
            'content': content
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 