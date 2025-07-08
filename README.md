## 제약영업사원 업무효율을 위한 문서검색 및 업무자동화 AI partner - llm기반 QA 챗봇 - Phase 1
### "LLM을 활용한 사내 문서 검색 및 업무지원형 디지털 비서 시스템"
##### 내 생각을 이해하고, 내 일을 함께하는 디지털 분신- 나루톡 <br/>
##### 모든 문서와 대화를 하나로 연결하는 스마트 허브 챗봇 - 나투록 <br/>
###### 나루톡 ( 모든 기능의 허브라는 뜻의 순우리말 '나룻터' 와 대화를 주고받는 talk의 합성어로,사용자의 모든 생각과 행동을 연결해주는 디지털 분신 챗봇 )

---

</div>


## 👥 팀 소개

<table>
  <tr>
    <td align="center">
      <img src="./team/1.png" width="120px"><br/>
      <b>김도윤</b><br/><span style="font-size:14px;">시스템 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/2.png" width="120px"><br/>
      <b>손현성</b><br/><span style="font-size:14px;">백앤드/인프라팀장</sub>
    </td>
    <td align="center">
      <img src="./team/3.png" width="120px"><br/>
      <b>이용규</b><br/><span style="font-size:14px;">QC 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/4.png" width="120px"><br/>
      <b>최문영</b><br/><span style="font-size:14px;">프론트 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/5.png" width="120px"><br/>
      <b>허한결</b><br/><span style="font-size:14px;">DB 팀장</sub>
    </td>
  </tr>
</table>
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
## Lang Graph 기능별 흐름도
<img src="./team/f1.png" width="100%"></td>
<img src="./team/f2.png" width="100%"></td>
<img src="./team/f3.png" width="100%"></td>
<img src="./team/f4.png" width="100%"></td>

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

```
### **환경 변수 설정**
```env
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic API 키 (선택)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# Django 비밀키
DJANGO_SECRET_KEY=your-secret-key-here
```

### 🌐 **접속 URL**
- **메인 웹사이트**: http://localhost:3000
- **Django 관리자**: http://localhost:8000/admin
- **FastAPI 문서**: http://localhost:8001/docs

## 📚 **API 문서**

### Django REST API
- **인증**: `/api/auth/`
- **채팅**: `/api/chat/`
- **사용자**: `/api/users/`
- **관리자**: `/api/admin/`

### FastAPI 마이크로서비스
- **검색**: `/search/`
- **분석**: `/analyze/`
- **예측**: `/predict/`

### WebSocket
- **실시간 채팅**: `ws://localhost:8000/ws/chat/`

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

# LangGraph 테스트
python langgraph_orchestrator/test_workflow.py
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

# 정적 파일 수집
python manage.py collectstatic

# Gunicorn으로 실행
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 🔧 **개발**

### 🎨 **코드 스타일**
```bash
# 코드 포매팅
black .
isort .

# 린팅
flake8 .
eslint src/
```


## 📄 **라이선스**

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🆘 **문제 해결**

### 자주 묻는 질문 (FAQ)

**Q: 'vite' 명령어를 찾을 수 없다는 오류가 발생합니다.**
```bash
# 전역 설치
npm install -g vite

# 또는 npx 사용
npx vite
```

**Q: Django 마이그레이션 오류가 발생합니다.**
```bash
# 마이그레이션 파일 삭제 후 재생성
python manage.py makemigrations --empty your_app_name
python manage.py migrate
```

**Q: React 프론트엔드가 로드되지 않습니다.**
```bash
# 캐시 삭제 후 재설치
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 🐛 **버그 리포트**
버그를 발견하셨나요? [Issues](https://github.com/your-username/narutalk/issues)에 리포트해주세요.

### 💬 **지원**
- 📧 Email: support@narutalk.com
- 💬 Discord: [Narutalk Community](https://discord.gg/narutalk)
- 📖 Wiki: [Documentation](https://github.com/your-username/narutalk/wiki)

---

<p align="center">
  <b>🏥 의료업계를 위한 AI 솔루션 - Narutalk</b><br>
  Made with ❤️ by the Narutalk Team
</p> 
### 📝 Phase 1

1. **기본 인프라 구축**
   - Docker 환경 설정
   - 데이터베이스 초기화
   - 기본 API Gateway 구축

2. **핵심 서비스 개발**
   - 데이터베이스 자동 업데이트 및 검색
   - 직원 실적 분석 : 실적 분석을 통해 요약 보고서를 생성, 관리자/직원 모드에 따라 다르게 제공
   - 거래처 실적 분석 및 등급 분류
   - 서류 자동화 및 규정 검토

3. **🆕 ML 서비스 개발**
   - MLflow 환경 구축
   - 데이터 파이프라인 구축
   - 모델 학습 및 평가
   - 예측 서비스 개발

4. **UI 및 통합 테스트**
   - React 프론트엔드 개발
   - 전체 시스템 통합
   - 성능 테스트 및 최적화
