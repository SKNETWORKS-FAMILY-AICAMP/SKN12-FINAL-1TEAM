# Config 모듈 설명서

## 📋 개요

`backend/app/core/config.py`는 백엔드 시스템 전체에서 사용되는 설정을 중앙에서 관리하는 모듈입니다.

## 🎯 목적

- **중앙화된 설정 관리**: 모든 서비스가 동일한 설정을 사용하도록 보장
- **환경별 자동 설정**: Docker/로컬 환경을 자동으로 감지하여 적절한 설정 적용
- **유지보수 용이성**: 한 곳에서 설정을 변경하면 전체 시스템에 반영

## 🏗️ 구조

### Config 클래스

싱글톤 패턴으로 구현된 설정 관리 클래스입니다.

#### 주요 메서드

##### 1. `get_database_api_url() -> str`
Database API의 URL을 반환합니다.

**우선순위:**
1. Docker 환경 자동 감지 (`/.dockerenv` 존재 여부) → `http://fastapi-app:8000`
2. 로컬 개발 환경 기본값 → `http://localhost:8010`

##### 2. `get_jwt_secret_key() -> str`
JWT 토큰 서명에 사용되는 시크릿 키를 반환합니다.
- 환경변수: `JWT_SECRET_KEY`
- 기본값: `"your-secret-key-here"`

##### 3. `get_openai_api_key() -> Optional[str]`
OpenAI API 키를 반환합니다.
- 환경변수: `OPENAI_API_KEY`
- 필수 설정 (기본값 없음)

##### 4. `is_docker_env() -> bool`
현재 실행 환경이 Docker 컨테이너인지 확인합니다.
- 판단 기준: `/.dockerenv` 파일 존재 여부

##### 5. `get_environment() -> str`
현재 실행 환경을 문자열로 반환합니다.
- Docker 환경: `"docker"`
- 그 외: `ENVIRONMENT` 환경변수 또는 `"development"`

### 전역 변수 (Export)

자주 사용되는 설정들을 미리 계산하여 상수로 제공합니다:

```python
DATABASE_API_URL  # Database API URL
JWT_SECRET_KEY    # JWT 시크릿 키
OPENAI_API_KEY    # OpenAI API 키
IS_DOCKER_ENV     # Docker 환경 여부 (boolean)
ENVIRONMENT       # 실행 환경 문자열
```

## 🔧 사용 방법

### 기본 사용법

```python
from app.core.config import config

# 메서드 호출
url = config.get_database_api_url()
api_key = config.get_openai_api_key()
```

### 전역 변수 사용

```python
from app.core.config import DATABASE_API_URL, IS_DOCKER_ENV

if IS_DOCKER_ENV:
    print(f"Docker 환경에서 실행 중: {DATABASE_API_URL}")
```

### 서비스에서 활용 예시

```python
# search_agent.py
from app.core.config import config

class SearchAgent:
    def __init__(self, base_url: Optional[str] = None):
        # base_url이 없으면 config에서 자동으로 가져옴
        self.base_url = base_url or config.get_database_api_url()
```

## 🌐 환경별 동작

### Docker 환경
- `/.dockerenv` 파일 자동 감지
- Database API URL: `http://fastapi-app:8000` (컨테이너 간 내부 통신)
- Environment: `"docker"`

### 로컬 개발 환경
- `/.dockerenv` 파일 없음
- Database API URL: `http://localhost:8010` (호스트 포트)
- Environment: `"development"`

### 환경변수 오버라이드
필요시 환경변수로 설정을 덮어쓸 수 있습니다:

```bash
export JWT_SECRET_KEY=my-secure-key
export OPENAI_API_KEY=sk-...
export ENVIRONMENT=production
```

## 📝 설정 가능한 환경변수

| 환경변수 | 설명 | 기본값 | 필수 |
|---------|------|--------|------|
| `JWT_SECRET_KEY` | JWT 토큰 서명 키 | `"your-secret-key-here"` | ⚠️ |
| `OPENAI_API_KEY` | OpenAI API 키 | 없음 | ✅ |
| `ENVIRONMENT` | 실행 환경 | `"development"` | ❌ |

`DATABASE_API_URL`은 `get_database_api_url()`이 Docker/로컬 환경을 자동 감지해 결정하며, 환경 코드 수정 없이 값만 바꾸려면 `config.py`를 직접 수정하면 됩니다.

## 🔍 Docker 환경 감지 로직

```python
IS_DOCKER_ENV = os.path.exists("/.dockerenv")
```

Docker 컨테이너는 루트 디렉토리에 `.dockerenv` 파일을 자동 생성합니다. 이를 통해 별도의 환경변수 설정 없이도 Docker 환경을 자동으로 감지합니다.

## 🎯 장점

1. **중앙화**: 모든 설정을 한 곳에서 관리
2. **자동화**: 환경을 자동으로 감지하여 적절한 설정 적용
3. **유연성**: 환경변수로 언제든 오버라이드 가능
4. **타입 안정성**: 타입 힌트 제공
5. **성능**: 전역 변수로 미리 계산하여 반복 호출 최소화

## 📚 관련 파일

- `backend/.env.example`: 환경변수 예시
- `docker-compose.yml`: Docker 환경변수 설정
- 각 서비스 파일들: config 모듈 사용

## ⚠️ 주의사항

1. **JWT_SECRET_KEY**: 프로덕션 환경에서는 반드시 강력한 키로 변경
2. **OPENAI_API_KEY**: 필수 설정이므로 반드시 제공
3. **DATABASE_API_URL**: Docker와 로컬 환경의 URL이 다름을 인지

---

*최종 업데이트: 2025년 1월*