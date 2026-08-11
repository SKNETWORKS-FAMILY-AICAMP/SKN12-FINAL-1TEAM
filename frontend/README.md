# NaruTalk Frontend

React 기반 프론트엔드입니다. (Create React App으로 부트스트랩됨)

## 실행

### 로컬 개발
```bash
cd frontend
npm install
npm start
```
`http://localhost:3000`에서 실행되며, `setupProxy.js`가 `/api/*`, `/user/*`, `/admin/*`, `/documents/*`, `/employee-info/*` 요청을 backend(포트 8000)로 프록시합니다.

### Docker
```bash
docker-compose up frontend
```

## 더 알아보기

프로젝트 구조, 컴포넌트 구성, API 통신, 프록시 설정, ChatBot 에이전트 시스템 등 상세 내용은 [`src/FRONTEND_ARCHITECTURE.md`](src/FRONTEND_ARCHITECTURE.md)를 참고하세요.
