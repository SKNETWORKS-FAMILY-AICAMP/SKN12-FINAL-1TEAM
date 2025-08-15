"""
중앙 설정 관리 모듈
모든 서비스에서 공통으로 사용하는 설정을 관리합니다.
"""
import os
from typing import Optional


class Config:
    """중앙 설정 관리 클래스"""
    
    @staticmethod
    def get_database_api_url() -> str:
        """
        환경에 따라 적절한 Database API URL 반환
        
        우선순위:
        1. Docker 환경 자동 감지 (/.dockerenv 파일 존재 여부)
        2. 기본값 (로컬 개발 환경)
        
        Returns:
            str: Database API URL
        """
        
        # 1. Docker 환경 자동 감지
        # Docker 컨테이너 내부에는 /.dockerenv 파일이 존재
        if os.path.exists("/.dockerenv"):
            return "http://fastapi-app:8000"
        
        # 2. 기본값 (로컬 개발 환경)
        return "http://localhost:8010"
    
    @staticmethod
    def get_jwt_secret_key() -> str:
        """JWT 시크릿 키 반환"""
        return os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    
    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """OpenAI API 키 반환"""
        return os.getenv("OPENAI_API_KEY")
    
    @staticmethod
    def is_docker_env() -> bool:
        """Docker 환경인지 확인"""
        return os.path.exists("/.dockerenv")
    
    @staticmethod
    def get_environment() -> str:
        """현재 환경 반환 (development, production, docker)"""
        if Config.is_docker_env():
            return "docker"
        return os.getenv("ENVIRONMENT", "development")


# 싱글톤 인스턴스
config = Config()


# 자주 사용되는 설정들을 직접 export
DATABASE_API_URL = config.get_database_api_url()
JWT_SECRET_KEY = config.get_jwt_secret_key()
OPENAI_API_KEY = config.get_openai_api_key()
IS_DOCKER_ENV = config.is_docker_env()
ENVIRONMENT = config.get_environment()