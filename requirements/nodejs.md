# 🏥 Narutalk 의료업계 QA 챗봇 시스템 - Node.js 요구사항

## 📋 **시스템 요구사항**

### Node.js 버전
- **Node.js**: 18.x 이상 (LTS 권장)
- **npm**: 9.x 이상
- **yarn**: 1.22.x 이상 (선택사항)

### 버전 확인
```bash
node --version    # v18.x.x
npm --version     # 9.x.x
yarn --version    # 1.22.x (선택사항)
```

## 📦 **패키지 설치**

### 기본 설치
```bash
# npm 사용
npm install

# yarn 사용 (선택사항)
yarn install
```

### 패키지 업데이트
```bash
# npm 사용
npm update

# yarn 사용
yarn upgrade
```

## 🔧 **주요 의존성 패키지**

### 🎯 **Core Framework**
- **react**: ^18.2.0 - React 코어 라이브러리
- **react-dom**: ^18.2.0 - React DOM 렌더링
- **react-router-dom**: ^6.17.0 - 라우팅 관리
- **typescript**: ^5.2.2 - TypeScript 지원

### 🎨 **UI Components**
- **@mui/material**: ^5.14.16 - Material-UI 컴포넌트
- **@mui/icons-material**: ^5.14.16 - Material-UI 아이콘
- **@emotion/react**: ^11.11.1 - CSS-in-JS 라이브러리
- **@emotion/styled**: ^11.11.0 - 스타일 컴포넌트
- **framer-motion**: ^10.16.5 - 애니메이션 라이브러리

### 🔄 **상태 관리**
- **@reduxjs/toolkit**: ^1.9.7 - Redux 상태 관리
- **react-redux**: ^8.1.3 - React-Redux 연동
- **@tanstack/react-query**: ^5.8.1 - 서버 상태 관리

### 🌐 **HTTP & WebSocket**
- **axios**: ^1.6.0 - HTTP 클라이언트
- **socket.io-client**: ^4.7.4 - WebSocket 클라이언트

### 📝 **폼 관리**
- **react-hook-form**: ^7.47.0 - 폼 관리
- **@hookform/resolvers**: ^3.3.2 - 폼 검증 리졸버
- **zod**: ^3.22.4 - 스키마 검증

### 📊 **데이터 시각화**
- **recharts**: ^2.8.0 - 차트 라이브러리
- **date-fns**: ^2.30.0 - 날짜 처리

### 🖥️ **코드 표시**
- **react-markdown**: ^9.0.1 - 마크다운 렌더링
- **prismjs**: ^1.29.0 - 코드 하이라이팅
- **react-syntax-highlighter**: ^15.5.0 - 코드 하이라이팅

### 🔔 **알림**
- **react-toastify**: ^9.1.3 - 토스트 알림

## 🛠️ **개발 도구**

### 🔧 **빌드 도구**
- **vite**: ^4.5.0 - 빌드 도구
- **@vitejs/plugin-react**: ^4.1.1 - React 플러그인

### 🧪 **타입 검사**
- **@types/react**: ^18.2.37 - React 타입 정의
- **@types/react-dom**: ^18.2.15 - React DOM 타입 정의
- **@types/prismjs**: ^1.26.3 - PrismJS 타입 정의

### 🔍 **코드 품질**
- **eslint**: ^8.53.0 - 코드 린팅
- **@typescript-eslint/eslint-plugin**: ^6.10.0 - TypeScript ESLint 플러그인
- **@typescript-eslint/parser**: ^6.10.0 - TypeScript ESLint 파서
- **eslint-plugin-react-hooks**: ^4.6.0 - React Hooks 린팅
- **eslint-plugin-react-refresh**: ^0.4.4 - React Refresh 린팅
- **prettier**: ^3.0.3 - 코드 포매팅

## 🚀 **스크립트 명령어**

### 개발 환경
```bash
npm run dev          # 개발 서버 시작
npm run build        # 프로덕션 빌드
npm run preview      # 빌드 미리보기
```

### 코드 품질
```bash
npm run lint         # 린팅 실행
npm run format       # 코드 포매팅
```

## 🌍 **환경 변수**

### .env 파일 설정
```env
# API 엔드포인트
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# 앱 설정
VITE_APP_NAME=Narutalk
VITE_APP_VERSION=1.0.0

# 개발 모드
VITE_DEBUG=true
```

## 🔧 **설정 파일**

### vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0'
  }
})
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## 🐛 **문제 해결**

### 일반적인 오류
```bash
# 의존성 충돌 해결
npm install --legacy-peer-deps

# 캐시 삭제
npm cache clean --force

# node_modules 재설치
rm -rf node_modules package-lock.json
npm install
```

### 포트 변경
```bash
# 다른 포트로 실행
npm run dev -- --port 3001
```

## 📱 **모바일 개발**

### 네트워크 접속
```bash
npm run dev -- --host 0.0.0.0
```

이렇게 하면 모바일 기기에서도 접속할 수 있습니다.

## 🎯 **최적화**

### 프로덕션 빌드
```bash
npm run build
npm run preview
```

### 번들 크기 분석
```bash
npm run build -- --analyze
``` 