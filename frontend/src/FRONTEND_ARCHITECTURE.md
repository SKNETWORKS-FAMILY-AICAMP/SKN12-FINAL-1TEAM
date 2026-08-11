# Frontend Architecture Documentation

## 📁 프로젝트 구조
```
frontend/src/
├── App.js                 # 메인 애플리케이션 컴포넌트
├── setupProxy.js          # 개발 서버 프록시 설정
├── components/            # React 컴포넌트들
├── services/              # API 통신 서비스
└── index.js              # React 앱 진입점
```

## 🎯 App.js (메인 애플리케이션)

### 주요 기능
1. **인증 관리**
   - JWT 토큰 기반 인증
   - 자동 로그인 상태 확인
   - 토큰 유효성 검증
   - 토큰은 `narutalk_token`으로 localStorage에 저장

2. **라우팅 설정**
   - React Router v6 사용
   - 보호된 라우트 구현
   - 비로그인 시 로그인 페이지로 리다이렉트

3. **상태 관리**
   - `isLoggedIn`: 로그인 상태
   - `currentUser`: 현재 사용자 정보
   - `schedules`: 일정 데이터 (localStorage 저장)
   - `sidebarVisible`: 사이드바 표시 여부
   - `isLoading`: 초기 로딩 상태

### 라우트 구조
```javascript
/ (Main)                    # 메인 대시보드
/search (SearchPage)         # 검색 페이지
/chat (ChatBot)             # AI 챗봇
/docs (Docs)                # 문서 관리
/client (ClientAnalysis)    # 고객 분석
/employee (EmployeePerformance) # 직원 성과
/schedule (Schedule)        # 일정 관리
/admin (Admin)              # 관리자 페이지
/login (Login)              # 로그인 페이지
```

### 컴포넌트 Props
모든 페이지 컴포넌트는 `currentUser` prop을 받습니다:
```javascript
{
  employee_id: number,
  email: string,
  username: string,
  name: string,
  role: 'admin' | 'user'
}
```

### 로그인 플로우
1. 앱 시작 시 localStorage에서 토큰 확인
2. 토큰이 있으면 `/user/me`로 유효성 검증
3. 유효하면 로그인 상태 유지, 무효하면 로그아웃
4. 로그인 페이지에서 인증 후 메인 페이지로 이동

## 🔧 setupProxy.js (프록시 설정)

### 목적
React 개발 서버(포트 3000)에서 백엔드 API(포트 8000)로의 요청을 프록시

### 프록시 구성

#### 1. SSE 프록시 (Server-Sent Events)
```javascript
const sseProxy = createProxyMiddleware({
  target: 'http://backend:8000',
  changeOrigin: true,
  onProxyReq: // 버퍼링 비활성화
  onProxyRes: // SSE 헤더 설정
})
```
- **대상 엔드포인트**: 
  - `/documents/upload-sse`
  - `/documents/upload-batch-sse`
- **특징**: 
  - 실시간 스트리밍 지원
  - 버퍼링 비활성화 (X-Accel-Buffering: no)
  - Content-Type: text/event-stream

#### 2. 일반 API 프록시
```javascript
const apiProxy = createProxyMiddleware({
  target: 'http://backend:8000',
  changeOrigin: true,
  ws: false
})
```
- **대상 경로 prefix**:
  - `/user/*` - 사용자 인증 API
  - `/admin/*` - 관리자 API
  - `/documents/*` - 문서 관리 API
  - `/employee-info/*` - 직원 정보 API
  - `/api/*` - 기타 API

### 미들웨어 라우팅 로직
```javascript
app.use((req, res, next) => {
  const path = req.path;
  
  // 1. SSE 엔드포인트 체크
  if (path === '/documents/upload-sse' || 
      path === '/documents/upload-batch-sse') {
    return sseProxy(req, res, next);
  }
  
  // 2. 일반 API 경로 체크
  if (path.startsWith('/user') || 
      path.startsWith('/admin') || 
      path.startsWith('/documents') || 
      path.startsWith('/employee-info') || 
      path.startsWith('/api')) {
    return apiProxy(req, res, next);
  }
  
  // 3. 정적 파일 등은 React 개발 서버가 처리
  return next();
});
```

### Docker 환경 고려사항
- **타겟 호스트**: `backend:8000` (Docker 네트워크 내부 호스트명)
- **changeOrigin: true**: Origin 헤더를 타겟으로 변경
- **logLevel: 'debug'**: 개발 중 디버깅용 로그

## 📦 컴포넌트 구조

### 페이지 컴포넌트
1. **Main.js** - 메인 대시보드
2. **Search.js** - 문서 검색 페이지 (내부/외부 문서 분류 로직 포함)
3. **ChatBot.js** - AI 챗봇 (Router Agent 및 4개 전문 에이전트)
4. **Docs.js** - 문서 관리
5. **ClientAnalysis.js** - 고객/거래처 분석
6. **EmployeePerformance.js** - 직원 성과 관리
7. **Schedule.js** - 일정 관리
8. **Admin.js** - 관리자 페이지 (SSE 파일 업로드 지원)
9. **Login.js** - 로그인 페이지

### 공통 컴포넌트
1. **Sidebar.js** - 사이드바 네비게이션
2. **ProcessProgressBar.js** - 단일 파일 업로드 진행률 표시
3. **BatchProcessProgressBar.js** - 배치 파일 업로드 진행률 표시
4. **UserModal.js** - 사용자 정보 모달
5. **Notification.js** - 알림 컴포넌트
6. **Setting.js** - 설정 컴포넌트

## 🔌 서비스 레이어 (services/api.js)

### 주요 API 함수
1. **인증 관련**
   - `loginUser()` - 사용자 로그인
   - `verifyToken()` - 토큰 유효성 검증
   - `logoutUser()` - 로그아웃 처리

2. **직원 관리**
   - `registerEmployee()` - 직원 등록 (관리자 전용)
   - `getEmployees()` - 직원 리스트 조회
   - `getEmployeeInfo()` - 직원 인사 정보 조회

3. **문서 관리**
   - `uploadDocument()` - 일반 문서 업로드
   - `uploadDocumentWithSSE()` - SSE 기반 단일 문서 업로드
   - `uploadDocumentsBatchWithSSE()` - SSE 기반 배치 문서 업로드
   - `getDocuments()` - 문서 목록 조회
   - `getDocumentDetail()` - 문서 상세 조회
   - `getDocumentContent()` - 문서 내용 조회

### API 통신 특징
- 모든 API 요청에 JWT 토큰 자동 추가
- FormData 처리 지원
- SSE (Server-Sent Events) 스트리밍 지원
- 상세한 콘솔 로깅으로 디버깅 용이

## 🛠 유틸리티 (utils/)

### markdownParser.js
- Markdown 텍스트를 HTML로 변환
- 헤더, 리스트, 코드 블록, 인라인 코드 등 지원
- **ClientAnalysis 컴포넌트**에서 사용 (ChatBot이 아님 — 아래 참고)

## 🔄 API 통신 흐름

### 일반 API 요청
```
브라우저 → localhost:3000/api/* → setupProxy.js → backend:8000/api/* → Agent Server → Database API
```

### SSE 업로드 요청
```
브라우저 → localhost:3000/documents/upload-sse → setupProxy.js (SSE 프록시) → backend:8000/documents/upload-sse → Agent Server (스트리밍 프록시) → Database API (SSE 응답)
```

## 🚀 개발 시작하기

### 로컬 개발
```bash
cd frontend
npm install
npm start
```

### Docker 환경
```bash
docker-compose up frontend
```

## ⚠️ 주의사항

1. **프록시 설정 변경 시**
   - setupProxy.js 수정 후 개발 서버 재시작 필요
   - 새로운 API 경로 추가 시 프록시 규칙 업데이트

2. **인증 토큰**
   - localStorage에 'narutalk_token'으로 저장
   - 모든 API 요청에 Authorization 헤더 자동 추가

3. **SSE 사용**
   - 파일 업로드 진행 상황 실시간 표시
   - fetch API로 SSE 처리 (EventSource 대신)
   - 청크 단위 스트리밍 파싱

4. **개발 규칙**
   - 기존 기능 보호 최우선 (DEVELOPMENT_RULES.md 참조)
   - 새 기능 추가 시 기존 기능 테스트 필수

## 🎨 ChatBot 컴포넌트 상세

### 에이전트 시스템
1. **Router Agent** - 쿼리 분석 및 자동 라우팅 (`/api/chat`)
2. **Employee Agent** - 직원 실적 분석 (`/api/select-agent`)
3. **Client Agent** - 고객/거래처 분석 (`/api/select-agent`)
4. **Search Agent** - 정보 검색 (`/api/select-agent`)
5. **Docs Agent** - 문서 생성 (`/api/select-agent`)

### 주요 기능
- 세션 ID 기반 대화 관리
- 채팅 히스토리 로컬 스토리지 저장
- Markdown 응답 렌더링 — `react-markdown` 라이브러리 사용(`import ReactMarkdown from 'react-markdown'`). 이전에는 자체 `utils/markdownParser.js`를 사용했으나 리팩토링되었음
- 에이전트별 색상 구분
- 대화형 문서 생성 (Docs Agent)

## 📝 다음 작업 시 참고사항

### UI 수정 시
- 모든 컴포넌트는 currentUser prop 활용 가능
- Admin 컴포넌트의 SSE 업로드 기능 정상 작동 중
- 사이드바 토글 기능 구현됨
- ChatBot의 Router Agent가 자동으로 적절한 에이전트 선택

### API 추가 시
1. services/api.js에 API 함수 추가
2. 필요시 setupProxy.js에 프록시 경로 추가
3. 백엔드 agent_server.py 프록시 로직 확인

### 컴포넌트 수정 시
- 각 컴포넌트는 독립적인 CSS 파일 보유
- 라우팅은 App.js에서 중앙 관리
- 로그인 상태는 App.js에서 전역 관리
- Search 컴포넌트에 내부/외부 문서 자동 분류 로직 포함

---
최종 업데이트: 2026-08-11
- ChatBot 마크다운 렌더링 서술을 `markdownParser.js` → `react-markdown`으로 정정 (실제 코드와 대조 후 수정)

최종 업데이트: 2025-01-18
- 컴포넌트 구조 및 서비스 레이어 상세 문서화
- ChatBot 에이전트 시스템 설명 추가
- SSE 업로드 기능 정상 작동 확인됨