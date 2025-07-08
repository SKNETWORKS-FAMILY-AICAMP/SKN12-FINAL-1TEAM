# 🏗️ Narutalk 프로젝트 구조 분석

이 문서는 Narutalk 의료업계 QA 챗봇 시스템의 전체 파일 구조와 각 구성 요소의 역할을 상세히 설명합니다.

## 📂 **프로젝트 루트 구조**

```
Narutalk/
├── 📁 apps/                     # Django 애플리케이션들
├── 📁 config/                   # Django 설정 파일들
├── 📁 src/                      # React 프론트엔드 소스
├── 📁 langgraph_orchestrator/   # AI 워크플로우 오케스트레이터
├── 📁 service_8001_search/      # FastAPI 검색 마이크로서비스
├── 📁 shared/                   # 공유 유틸리티 및 모델
├── 📁 requirements/             # 환경별 패키지 요구사항
├── 📁 logs/                     # 로그 파일들
├── 📁 data/                     # 데이터베이스 및 데이터 파일
├── 📁 static/                   # 정적 파일 (CSS, JS, 이미지)
├── 📁 templates/                # Django 템플릿
├── 📁 내부자료_규정,인사자료/      # 의료기관 규정 및 인사 자료
├── 📁 내부자료_업무지원/          # 의료업무 지원 자료
├── 📄 manage.py                 # Django 관리 스크립트
├── 📄 package.json              # Node.js 패키지 설정
├── 📄 vite.config.ts            # Vite 빌드 설정
└── 📄 tsconfig.json             # TypeScript 설정
```

## 🔧 **Django 백엔드 구조 (apps/)**

### 📱 **애플리케이션 구조**
```
apps/
├── 🔐 authentication/          # 사용자 인증 및 권한 관리
│   ├── models.py              # User 모델, 권한 모델
│   ├── serializers.py         # API 직렬화기
│   ├── views.py               # 인증 API 뷰
│   ├── urls.py                # 인증 URL 라우팅
│   └── migrations/            # 데이터베이스 마이그레이션
│
├── 💬 chat/                    # 채팅 및 메시지 관리
│   ├── models.py              # 채팅방, 메시지 모델
│   ├── serializers.py         # 채팅 API 직렬화기
│   ├── views.py               # 채팅 API 뷰
│   ├── consumers.py           # WebSocket 컨슈머
│   ├── routing.py             # WebSocket 라우팅
│   ├── urls.py                # 채팅 URL 라우팅
│   └── migrations/            # 데이터베이스 마이그레이션
│
└── 🌐 gateway/                 # API 게이트웨이 및 미들웨어
    ├── views.py               # 게이트웨이 뷰
    ├── middleware.py          # 커스텀 미들웨어
    └── urls.py                # 게이트웨이 URL 라우팅
```

### 🔧 **Django 설정 구조 (config/)**
```
config/
├── settings/                  # 환경별 설정
│   ├── __init__.py
│   ├── base.py               # 기본 공통 설정
│   └── development.py        # 개발 환경 설정
├── urls.py                   # 메인 URL 설정
├── wsgi.py                   # WSGI 설정 (프로덕션)
├── asgi.py                   # ASGI 설정 (WebSocket)
└── env.example               # 환경 변수 템플릿
```

## ⚛️ **React 프론트엔드 구조 (src/)**

### 🎨 **컴포넌트 구조**
```
src/
├── 🎯 components/             # React 컴포넌트
│   └── Chat/                 # 채팅 관련 컴포넌트
│       └── ChatInterface.tsx # 메인 채팅 인터페이스
│
├── 🗃️ store/                  # Redux 상태 관리
│   ├── index.ts              # 스토어 설정
│   └── slices/               # Redux 슬라이스
│       ├── authSlice.ts      # 인증 상태 관리
│       ├── chatSlice.ts      # 채팅 상태 관리
│       └── uiSlice.ts        # UI 상태 관리
│
├── 🎨 theme/                  # 테마 및 스타일 설정
│   └── index.ts              # Material-UI 테마
│
├── 📱 App.tsx                 # 메인 애플리케이션 컴포넌트
└── 🚀 main.tsx                # 애플리케이션 진입점
```

### 🔧 **프론트엔드 설정 파일**
```
├── 📄 package.json            # Node.js 의존성 및 스크립트
├── 📄 vite.config.ts          # Vite 빌드 도구 설정
├── 📄 tsconfig.json           # TypeScript 컴파일러 설정
├── 📄 tsconfig.node.json      # Node.js용 TypeScript 설정
└── 📄 index.html              # HTML 진입점
```

## 🤖 **AI 워크플로우 구조 (langgraph_orchestrator/)**

### 🧠 **LangGraph AI 시스템**
```
langgraph_orchestrator/
├── 🤖 qa_agent/               # QA 에이전트 구현
│   ├── agent.py              # 메인 에이전트 로직
│   └── utils/                # 유틸리티 모듈
│       ├── nodes.py          # 워크플로우 노드들
│       ├── state.py          # 상태 관리
│       └── tools.py          # AI 도구들
│
├── 📄 langgraph.json          # LangGraph 설정
├── 📄 requirements.txt        # AI 전용 패키지 요구사항
├── 🧪 test_workflow.py        # 워크플로우 테스트
├── 🧪 test_real_api.py        # 실제 API 테스트
├── 🧪 test_structure.py       # 구조 테스트
├── 🧪 test_env.py             # 환경 테스트
├── 📖 README.md               # AI 시스템 문서
└── 📖 setup_guide.md          # 설정 가이드
```

## ⚡ **FastAPI 마이크로서비스 (service_8001_search/)**

### 🔍 **검색 서비스 구조**
```
service_8001_search/
├── 📄 main.py                 # FastAPI 애플리케이션 진입점
├── 📄 app.py                  # 애플리케이션 설정
├── 📄 routes.py               # API 라우트 정의
└── 📄 services.py             # 비즈니스 로직
```

## 🔗 **공유 모듈 (shared/)**

### 🛠️ **공통 유틸리티**
```
shared/
├── 📄 __init__.py             # 패키지 초기화
├── 📄 models.py               # 공통 데이터 모델
└── 📄 openai_client.py        # OpenAI API 클라이언트
```

## 📦 **패키지 관리 (requirements/)**

### 🎯 **환경별 요구사항**
```
requirements/
├── 📄 base.txt                # 기본 공통 패키지
├── 📄 development.txt         # 개발 환경 패키지
├── 📄 production.txt          # 프로덕션 환경 패키지
├── 📄 test.txt                # 테스트 환경 패키지
└── 📄 nodejs.md               # Node.js 환경 요구사항
```

## 🗂️ **데이터 및 파일 저장소**

### 📊 **데이터 디렉토리 구조**
```
├── 📁 data/                   # 애플리케이션 데이터
│   ├── databases/            # SQLite 데이터베이스 파일
│   └── uploads/              # 사용자 업로드 파일
│
├── 📁 logs/                   # 로그 파일들
│   ├── django.log            # Django 애플리케이션 로그
│   ├── fastapi.log           # FastAPI 서비스 로그
│   └── system.log            # 시스템 전체 로그
│
├── 📁 static/                 # 정적 파일
│   ├── css/                  # 스타일시트
│   ├── js/                   # JavaScript 파일
│   └── images/               # 이미지 파일
│
├── 📁 templates/              # Django 템플릿
│   └── base.html             # 기본 템플릿
│
├── 📁 내부자료_규정,인사자료/    # 의료기관 규정
│   ├── DM_rules.docx         # 당뇨 관리 규정
│   ├── HR information.xlsx   # 인사 정보
│   └── org_chart.docx        # 조직도
│
└── 📁 내부자료_업무지원/        # 업무 지원 자료
    ├── ML_실적/               # 머신러닝 실적 데이터
    ├── 마케팅정책/             # 마케팅 정책 문서
    ├── 보고서양식/             # 보고서 양식 템플릿
    ├── 실적자료.xlsx          # 실적 데이터
    ├── 약품자료/               # 의약품 정보
    └── 필요한양식_라벨붙여서/    # 업무 양식 모음
```

## 🚀 **실행 스크립트들**

### 🔧 **시스템 실행 파일**
```
├── 📄 install.bat             # Windows 자동 설치 스크립트
├── 📄 start_narutalk.ps1      # PowerShell 실행 스크립트
├── 📄 start_narutalk.bat      # 배치 파일 실행 스크립트
├── 📄 run_narutalk.py         # Python 통합 실행 스크립트
├── 📄 build_exe.py            # 실행파일 빌드 스크립트
└── 📄 start_system.bat        # 기본 시스템 시작 스크립트
```

## 📚 **문서 및 가이드**

### 📖 **프로젝트 문서들**
```
├── 📄 README.md               # 프로젝트 메인 문서
├── 📄 PROJECT_STRUCTURE.md    # 프로젝트 구조 분석 (이 문서)
├── 📄 실행가이드.md            # 상세 실행 가이드
├── 📄 project_structure.md    # 초기 프로젝트 구조 문서
└── 📄 current_packages.txt     # 현재 설치된 패키지 목록
```

## 🔍 **각 구성 요소의 역할**

### 🏢 **애플리케이션 계층 구조**

#### **1. 프레젠테이션 계층 (React Frontend)**
- **역할**: 사용자 인터페이스 제공
- **기술**: React, TypeScript, Material-UI, Redux
- **위치**: `src/` 디렉토리
- **포트**: 3000

#### **2. API 계층 (Django Backend)**
- **역할**: REST API 제공, 비즈니스 로직 처리
- **기술**: Django, Django REST Framework, Channels
- **위치**: `apps/`, `config/` 디렉토리
- **포트**: 8000

#### **3. 마이크로서비스 계층 (FastAPI)**
- **역할**: 특화된 기능 (검색, 분석) 제공
- **기술**: FastAPI, SQLAlchemy, Pydantic
- **위치**: `service_8001_search/` 디렉토리
- **포트**: 8001+

#### **4. AI 워크플로우 계층 (LangGraph)**
- **역할**: AI 기반 질의응답 처리
- **기술**: LangGraph, OpenAI, Anthropic
- **위치**: `langgraph_orchestrator/` 디렉토리

#### **5. 데이터 계층**
- **역할**: 데이터 저장 및 관리
- **기술**: SQLite (개발), PostgreSQL (프로덕션)
- **위치**: `data/databases/` 디렉토리

## 🔄 **데이터 흐름**

```
사용자 요청 (React) 
    ↓
Django REST API 
    ↓
LangGraph AI 처리 ← FastAPI 마이크로서비스
    ↓
데이터베이스 저장/조회
    ↓
WebSocket을 통한 실시간 응답
    ↓
React UI 업데이트
```

## 🔐 **보안 및 인증 흐름**

```
로그인 요청 → Django 인증 → JWT 토큰 발급 → 
React 상태 저장 → API 요청시 토큰 포함 → 
Django 미들웨어 검증 → 권한 확인 → 응답
```

## 🧩 **확장 포인트**

### **새로운 기능 추가 시 고려사항**

1. **새로운 Django 앱 추가**: `apps/` 디렉토리에 새 앱 생성
2. **새로운 React 컴포넌트**: `src/components/` 에 기능별 폴더 생성
3. **새로운 마이크로서비스**: `service_800X_name/` 형태로 추가
4. **새로운 AI 기능**: `langgraph_orchestrator/qa_agent/` 에 확장
5. **새로운 Redux 상태**: `src/store/slices/` 에 슬라이스 추가

## 📊 **성능 최적화 고려사항**

### **병목 지점 및 최적화 전략**

1. **데이터베이스**: 인덱싱, 쿼리 최적화
2. **AI 응답**: 캐싱, 비동기 처리
3. **프론트엔드**: 코드 스플리팅, 지연 로딩
4. **API**: 페이지네이션, 압축
5. **WebSocket**: 연결 풀링, 메시지 배치

## 🔧 **개발 워크플로우**

### **권장 개발 순서**

1. **백엔드 모델 설계** → `apps/*/models.py`
2. **API 엔드포인트 구현** → `apps/*/views.py`, `apps/*/urls.py`
3. **프론트엔드 상태 설계** → `src/store/slices/`
4. **React 컴포넌트 구현** → `src/components/`
5. **AI 워크플로우 연동** → `langgraph_orchestrator/`
6. **테스트 작성** → 각 모듈별 테스트
7. **문서 업데이트** → README, API 문서

이 구조는 확장 가능하고 유지보수가 용이하도록 설계되었으며, 각 계층이 독립적으로 개발될 수 있도록 모듈화되어 있습니다. 