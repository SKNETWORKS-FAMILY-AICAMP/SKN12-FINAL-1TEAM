"""
중앙화된 환경변수 설정 관리 모듈

모든 환경변수를 한 곳에서 관리하고 검증하는 설정 클래스를 제공합니다.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic.types import SecretStr

# 환경 설정
# Windows 로컬 환경 우선 확인
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOTENV_PATH = os.path.join(WORKSPACE_ROOT, '.env')

# Docker 환경인 경우 재설정
if os.path.exists('/app/.env'):
    WORKSPACE_ROOT = '/app'
    DOTENV_PATH = '/app/.env'

print(f"[DEBUG] WORKSPACE_ROOT: {WORKSPACE_ROOT}")
print(f"[DEBUG] Settings .env file path: {DOTENV_PATH}")

# .env 파일이 존재하면 로드
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
    print(f"[OK] .env file loaded: {DOTENV_PATH}")
else:
    print(f"[WARNING] .env file not found: {DOTENV_PATH}")
    print("Environment variables must be set directly.")


class DatabaseSettings(BaseSettings):
    """데이터베이스 관련 설정"""
    user: str
    password: SecretStr
    db: str
    host: str
    port: int = 5432

    @property
    def database_url(self) -> str:
        """데이터베이스 연결 URL 생성"""
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "POSTGRES_"


class PgAdminSettings(BaseSettings):
    """PgAdmin 관련 설정"""
    email: str
    password: SecretStr

    class Config:
        env_prefix = "PGADMIN_"


class MinIOSettings(BaseSettings):
    """MinIO 관련 설정"""
    endpoint: str
    root_user: str
    root_password: SecretStr
    bucket_name: str

    @property
    def access_key(self) -> str:
        """MinIO 접근 키 (root_user와 동일)"""
        return self.root_user

    @property
    def secret_key(self) -> str:
        """MinIO 시크릿 키 (root_password와 동일)"""
        return self.root_password.get_secret_value()

    class Config:
        env_prefix = "MINIO_"


# class AWSS3Settings(BaseSettings):
#     """AWS S3 관련 설정"""
#     access_key_id: str
#     secret_access_key: SecretStr
#     region: str = "ap-northeast-2"
#     bucket_name: str

#     class Config:
#         env_prefix = "AWS_S3_"


class OpenSearchSettings(BaseSettings):
    """OpenSearch 관련 설정"""
    host: str
    port: int = 9200
    user: str = "admin"
    initial_admin_password: SecretStr
    ca_certs: Optional[str] = None

    @property
    def connection_url(self) -> str:
        """OpenSearch 연결 URL 생성"""
        return f"http://{self.host}:{self.port}"

    class Config:
        env_prefix = "OPENSEARCH_"


class JWTSettings(BaseSettings):
    """JWT 관련 설정"""
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_prefix = "JWT_"


class AppSettings(BaseSettings):
    """애플리케이션 전체 설정"""
    env: str = "development"
    debug: bool = True

    class Config:
        env_prefix = "APP_"


class OpenAISettings(BaseSettings):
    """OpenAI 관련 설정"""
    api_key: str

    class Config:
        env_prefix = "OPENAI_"


class Settings:
    """전체 설정을 관리하는 메인 클래스"""
    
    def __init__(self):
        print(f"[DEBUG] Settings loading .env file path: {DOTENV_PATH}")
        # 각 설정 객체 초기화
        self.database = DatabaseSettings()
        self.pgadmin = PgAdminSettings()
        self.minio = MinIOSettings()
        # self.aws_s3 = AWSS3Settings()  # AWS S3 설정 주석 처리
        self.opensearch = OpenSearchSettings()
        self.jwt = JWTSettings()
        self.app = AppSettings()
        self.openai = OpenAISettings()

    def validate_all(self):
        """모든 설정의 유효성을 검증합니다."""
        try:
            # 각 설정 객체가 유효한지 확인
            self.database.database_url
            self.minio.access_key
            self.minio.secret_key
            self.opensearch.connection_url
            self.jwt.secret_key.get_secret_value()
            return True
        except Exception as e:
            raise ValueError(f"설정 검증 실패: {e}")

    def get_database_url(self) -> str:
        """데이터베이스 연결 URL 반환"""
        return self.database.database_url

    def get_minio_config(self) -> dict:
        """MinIO 설정 반환"""
        return {
            "endpoint_url": self.minio.endpoint,
            "aws_access_key_id": self.minio.access_key,
            "aws_secret_access_key": self.minio.secret_key,
            "region_name": "us-east-1",
            "bucket_name": self.minio.bucket_name
        }

    # def get_aws_s3_config(self) -> dict:
    #     """AWS S3 설정 반환"""
    #     return {
    #         "aws_access_key_id": self.aws_s3.access_key_id,
    #         "aws_secret_access_key": self.aws_s3.secret_access_key.get_secret_value(),
    #         "region_name": self.aws_s3.region,
    #         "bucket_name": self.aws_s3.bucket_name
    #     }

    def get_opensearch_config(self) -> dict:
        """OpenSearch 설정 반환"""
        return {
            "host": self.opensearch.host,
            "port": self.opensearch.port,
            "user": self.opensearch.user,
            "password": self.opensearch.initial_admin_password.get_secret_value()
        }

    def get_jwt_config(self) -> dict:
        """JWT 설정 반환"""
        return {
            "secret_key": self.jwt.secret_key.get_secret_value(),
            "algorithm": self.jwt.algorithm,
            "access_token_expire_minutes": self.jwt.access_token_expire_minutes
        }

    def get_openai_config(self) -> dict:
        """OpenAI 설정 반환"""
        return {
            "api_key": self.openai.api_key
        }


# 전역 설정 인스턴스 생성
settings = Settings()

# 앱 시작 시 설정 검증
try:
    settings.validate_all()
    print("[OK] All environment variables are correctly configured.")
except ValueError as e:
    print(f"[ERROR] Environment variable configuration error: {e}")
    print("[INFO] Please check the .env file and set all required environment variables.")
    raise 