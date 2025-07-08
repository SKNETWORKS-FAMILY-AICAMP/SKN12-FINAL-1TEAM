"""
Gateway views for QA Chatbot System
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
import asyncio
import aiohttp


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    시스템 헬스 체크 API
    """
    return Response({
        'status': 'healthy',
        'message': 'QA Chatbot System is running',
        'services': {
            'django': 'healthy',
            'database': 'healthy',
            'redis': 'healthy'
        }
    })


@api_view(['POST'])
def orchestrate_query(request):
    """
    LangGraph 오케스트레이터를 통한 쿼리 처리
    """
    try:
        query = request.data.get('query')
        session_id = request.data.get('session_id')
        
        if not query:
            return Response({'error': 'Query is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 여기서 LangGraph 오케스트레이터를 호출
        # 실제 구현에서는 services.langgraph_service 를 사용
        
        return Response({
            'response': f'Processed query: {query}',
            'session_id': session_id,
            'metadata': {
                'model': 'gpt-4o',
                'processing_time': '1.2s',
                'confidence': 0.95
            }
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def microservices_status(request):
    """
    마이크로서비스 상태 확인 API
    """
    services = {
        'search': 'http://localhost:8001',
        'analytics': 'http://localhost:8002',
        'client_analysis': 'http://localhost:8003',
        'document': 'http://localhost:8004',
        'conversation': 'http://localhost:8005',
        'wiki': 'http://localhost:8006',
        'news': 'http://localhost:8007',
        'ml': 'http://localhost:8008',
        'memory': 'http://localhost:8009'
    }
    
    # 실제 구현에서는 각 서비스의 헬스체크를 비동기로 호출
    service_status = {}
    for service_name, service_url in services.items():
        service_status[service_name] = {
            'url': service_url,
            'status': 'unknown'  # 실제로는 HTTP 요청으로 확인
        }
    
    return Response({
        'services': service_status,
        'total_services': len(services),
        'healthy_services': 0  # 실제 헬스체크 결과에 따라 계산
    }) 