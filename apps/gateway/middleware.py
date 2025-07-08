"""
Gateway middleware for QA Chatbot System
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class GatewayMiddleware(MiddlewareMixin):
    """
    API 게이트웨이 미들웨어
    - 요청 로깅
    - 응답 시간 측정
    - Rate limiting (기본 구현)
    """
    
    def process_request(self, request):
        """
        요청 처리 전 실행
        """
        request.start_time = time.time()
        
        # 요청 로깅
        logger.info(f"Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}")
        
        return None
    
    def process_response(self, request, response):
        """
        응답 처리 후 실행
        """
        # 응답 시간 계산
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Response-Time'] = f"{duration:.3f}s"
            
            # 응답 로깅
            logger.info(f"Response: {response.status_code} for {request.path} ({duration:.3f}s)")
        
        # CORS 헤더 추가 (개발 환경)
        if settings.DEBUG:
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        
        return response
    
    def process_exception(self, request, exception):
        """
        예외 처리
        """
        logger.error(f"Exception in {request.path}: {str(exception)}")
        
        if settings.DEBUG:
            return None  # Django가 기본 에러 페이지를 보여줌
        else:
            return JsonResponse({
                'error': 'Internal server error',
                'message': '서버 내부 오류가 발생했습니다.'
            }, status=500) 