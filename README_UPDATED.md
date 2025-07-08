# 🏥 Narutalk - 의료업계 QA 챗봇 시스템

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18.2+-blue.svg)](https://reactjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Narutalk**은 의료업계 전용 AI 기반 QA 챗봇 시스템입니다. GPT-4o와 LangGraph를 활용하여 의료진이 빠르고 정확한 정보를 얻을 수 있도록 설계되었습니다.

## 🚀 **주요 기능**

### 💬 **AI 챗봇**
- GPT-4o 기반 의료 전문 답변
- 실시간 채팅 (WebSocket)
- 다중 세션 관리
- 의료 카테고리별 분류 (의료상담, 일반문의, 응급, 진료상담)

### 🔐 **사용자 관리**
- 역할 기반 접근 제어 (관리자, 의사, 간호사, 일반사용자)
- JWT 기반 인증 시스템
- 의료진 전용 기능 및 권한 관리

### 🎨 **현대적 UI**
- Material-UI 기반 반응형 디자인
- Redux Toolkit을 통한 상태 관리
- 다크/라이트 테마 지원
- 모바일 친화적 인터페이스

### 📊 **데이터 분석**
- 의료 문서 검색 및 분석
- 실시간 차트 및 통계
- 성능 모니터링 및 로깅

## 🏗️ **시스템 아키텍처**

```
Frontend (React)     Backend (Django)     AI Layer (LangGraph)
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Port 3000      │◄─│  Port 8000      │◄─│  AI Orchestrator│
│                 │  │                 │  │                 │
│ • Material-UI   │  │ • REST API      │  │ • GPT-4o        │
│ • Redux Store   │  │ • WebSocket     │  │ • LangGraph     │
│ • TypeScript    │  │ • JWT Auth      │  │ • Vector DB     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Node.js        │  │  SQLite/PgSQL   │  │  FastAPI        │
│  Vite Build     │  │  Database       │  │  Port 8001+     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 📂 **프로젝트 구조**

### **📁 백엔드 (Django Apps)**
```
apps/
├── 🔐 authentication/     # 사용자 인증 및 권한 관리
│   ├── models.py         # 커스텀 User 모델
│   ├── serializers.py    # JWT 토큰, 사용자 직렬화
│   ├── views.py          # 로그인/회원가입/프로필 API
│   └── urls.py           # 인증 URL 라우팅
│
├── 💬 chat/              # 채팅 및 메시지 시스템
│   ├── models.py         # ChatSession, Message 모델
│   ├── consumers.py      # WebSocket 실시간 통신
│   ├── serializers.py    # 채팅 데이터 직렬화
│   ├── views.py          # 채팅 세션 관리 API
│   └── routing.py        # WebSocket 라우팅
│
└── 🌐 gateway/           # API 게이트웨이
    ├── middleware.py     # 로깅, CORS 미들웨어
    └── views.py          # 상태확인, 프록시 뷰
```

### **⚛️ 프론트엔드 (React)**
```
src/
├── 🎯 components/        # React 컴포넌트
│   └── Chat/            # 채팅 인터페이스
│
├── 🗃️ store/             # Redux 상태 관리
│   ├── index.ts         # 스토어 설정
│   └── slices/          # 상태 슬라이스
│       ├── authSlice.ts # 인증 상태
│       ├── chatSlice.ts # 채팅 상태
│       └── uiSlice.ts   # UI 상태
│
├── 🎨 theme/            # Material-UI 테마
└── 📱 App.tsx           # 메인 앱 컴포넌트
```

### **🤖 AI 워크플로우**
```
langgraph_orchestrator/
├── 🧠 qa_agent/         # QA 에이전트 구현
│   ├── agent.py        # 메인 AI 로직
│   └── utils/          # 워크플로우 유틸
│       ├── nodes.py    # AI 처리 노드들
│       ├── state.py    # 상태 관리
│       └── tools.py    # AI 도구들
│
└── 🧪 test_*.py         # AI 시스템 테스트
```

### **⚡ 마이크로서비스**
```
service_8001_search/     # FastAPI 검색 서비스
├── main.py             # FastAPI 앱 진입점
├── routes.py           # API 라우트
└── services.py         # 비즈니스 로직
```

## 📋 **시스템 요구사항**

### 필수 소프트웨어
- **Python**: 3.10 이상
- **Node.js**: 18.x 이상 (LTS 권장)
- **npm**: 9.x 이상

### 권장 사양
- **RAM**: 8GB 이상
- **Storage**: 2GB 이상 여유 공간
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

## 🛠️ **설치 방법**

### 📥 **자동 설치 (Windows 권장)**
```bash
# 1. 저장소 클론
git clone [repository-url]
cd Narutalk

# 2. 자동 설치 실행
install.bat
```

### 🔧 **수동 설치**
```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 2. Python 패키지 설치
pip install -r requirements/development.txt

# 3. Node.js 패키지 설치
npm install

# 4. 데이터베이스 설정
python manage.py makemigrations
python manage.py migrate

# 5. 환경 변수 설정
cp config/env.example .env
# .env 파일을 편집하여 API 키 등을 설정
```

## 🚀 **실행 방법**

### 🎯 **간단한 실행 (권장)**
```bash
# Windows PowerShell (권장)
powershell -ExecutionPolicy Bypass -File start_narutalk.ps1

# 배치 파일
start_narutalk.bat

# Python 통합 스크립트
python run_narutalk.py
```

### 🔄 **수동 실행**
```bash
# 터미널 1: Django 백엔드
.\.venv\Scripts\activate
python manage.py runserver

# 터미널 2: React 프론트엔드
npm run dev

# 터미널 3: FastAPI 서비스 (선택사항)
.\.venv\Scripts\activate
cd service_8001_search
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 🌐 **접속 URL**
- **🎯 메인 웹사이트**: http://localhost:3000
- **🔧 Django 관리자**: http://localhost:8000/admin
- **📡 Django API**: http://localhost:8000/api
- **⚡ FastAPI 서비스**: http://localhost:8001
- **📚 API 문서**: http://localhost:8000/api/docs

## 📚 **API 문서**

### **인증 API** (`/api/auth/`)
```
POST /api/auth/login/           # 로그인
POST /api/auth/register/        # 회원가입
GET  /api/auth/profile/         # 프로필 조회
PUT  /api/auth/profile/         # 프로필 수정
POST /api/auth/token/refresh/   # 토큰 갱신
GET  /api/auth/dashboard/       # 대시보드 데이터
```

### **채팅 API** (`/api/chat/`)
```
GET  /api/chat/sessions/        # 채팅 세션 목록
POST /api/chat/sessions/        # 새 채팅 세션
GET  /api/chat/sessions/{id}/   # 특정 세션 조회
DELETE /api/chat/sessions/{id}/ # 세션 삭제
WebSocket: ws://localhost:8000/ws/chat/{session_id}/
```

### **게이트웨이 API** (`/api/`)
```
GET  /api/health/               # 시스템 상태 확인
POST /api/proxy/search/         # 검색 서비스 프록시
```

## 🧪 **테스트**

### 단위 테스트
```bash
# Django 테스트
python manage.py test

# Pytest 실행
pytest

# 커버리지 포함
pytest --cov=apps --cov-report=html
```

### 통합 테스트
```bash
# 전체 시스템 테스트
python test_workflow.py

# LangGraph AI 테스트
cd langgraph_orchestrator
python test_workflow.py
```

## 📦 **배포**

### 🐳 **Docker 배포**
```bash
# Docker 이미지 빌드
docker build -t narutalk:latest .

# 컨테이너 실행
docker run -p 3000:3000 -p 8000:8000 narutalk:latest
```

### 🌐 **프로덕션 배포**
```bash
# 프로덕션 패키지 설치
pip install -r requirements/production.txt

# React 프로덕션 빌드
npm run build

# 정적 파일 수집
python manage.py collectstatic

# Gunicorn으로 실행
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 🔧 **개발 가이드**

### **새 기능 추가 워크플로우**
1. **백엔드**: Django 앱 생성 → 모델 정의 → API 뷰 작성 → URL 연결
2. **프론트엔드**: Redux 슬라이스 생성 → 컴포넌트 구현 → 상태 연결
3. **AI 기능**: LangGraph 노드 추가 → 도구 구현 → 워크플로우 연결
4. **테스트**: 단위 테스트 → 통합 테스트 → API 테스트

### **코딩 규칙**
- **Python**: PascalCase (클래스), snake_case (함수/변수)
- **TypeScript**: PascalCase (컴포넌트), camelCase (함수/변수)
- **Git**: feat/fix/docs/style/refactor/test/chore 접두사 사용

## 🆘 **문제 해결**

### 자주 묻는 질문

**Q: 'vite' 명령어 오류가 발생합니다.**
```bash
npm install -g vite  # 전역 설치
# 또는 npx vite       # npx 사용
```

**Q: Django 마이그레이션 오류가 발생합니다.**
```bash
python manage.py migrate --fake-initial
python manage.py makemigrations
python manage.py migrate
```

**Q: React가 로드되지 않습니다.**
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Q: JWT 토큰 오류가 발생합니다.**
```python
# settings에서 JWT 설정 확인
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
```

## 📁 **주요 설정 파일**

### **Python 환경**
- `requirements/` - 환경별 패키지 요구사항
- `config/settings/` - Django 환경별 설정
- `config/env.example` - 환경 변수 템플릿

### **Node.js 환경**
- `package.json` - Node.js 의존성 및 스크립트
- `vite.config.ts` - Vite 빌드 설정
- `tsconfig.json` - TypeScript 설정

### **실행 스크립트**
- `install.bat` - 자동 설치
- `start_narutalk.ps1` - PowerShell 실행
- `run_narutalk.py` - Python 통합 실행

## 📖 **관련 문서**

- [📂 PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 상세 파일 구조 분석
- [🛠️ DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - 개발 및 확장 가이드
- [🏗️ DJANGO_API_ARCHITECTURE.md](DJANGO_API_ARCHITECTURE.md) - Django/API 구조 설명
- [📋 실행가이드.md](실행가이드.md) - 상세 실행 방법

## 🤝 **기여하기**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 **라이선스**

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

<p align="center">
  <b>🏥 의료업계를 위한 AI 솔루션 - Narutalk</b><br>
  Made with ❤️ by the Narutalk Team
</p> 