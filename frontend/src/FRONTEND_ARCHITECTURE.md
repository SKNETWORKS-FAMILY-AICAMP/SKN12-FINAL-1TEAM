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

2. **라우팅 설정**
   - React Router v6 사용
   - 보호된 라우트 구현
   - 비로그인 시 로그인 페이지로 리다이렉트

3. **상태 관리**
   - `isLoggedIn`: 로그인 상태
   - `currentUser`: 현재 사용자 정보
   - `schedules`: 일정 데이터 (localStorage 저장)
   - `sidebarVisible`: 사이드바 표시 여부

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

## 📝 다음 작업 시 참고사항

### UI 수정 시
- 모든 컴포넌트는 currentUser prop 활용 가능
- Admin 컴포넌트의 SSE 업로드 기능 정상 작동 중
- 사이드바 토글 기능 구현됨

### API 추가 시
1. services/api.js에 API 함수 추가
2. 필요시 setupProxy.js에 프록시 경로 추가
3. 백엔드 agent_server.py 프록시 로직 확인

### 컴포넌트 수정 시
- 각 컴포넌트는 독립적인 CSS 파일 보유
- 라우팅은 App.js에서 중앙 관리
- 로그인 상태는 App.js에서 전역 관리

---
최종 업데이트: 2025-01-15
SSE 업로드 기능 정상 작동 확인됨