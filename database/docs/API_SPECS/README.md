# API 명세서 전체 가이드

## 📚 개요
이 문서는 데이터베이스 관리 시스템의 모든 API 엔드포인트에 대한 명세서를 제공합니다.

## 🗂️ API 명세서 목록

### 1. [User Router API](./user_router_api_spec.md)
**사용자 인증 및 관리**
- 사용자 로그인/로그아웃
- JWT 토큰 관리
- 사용자 정보 조회
- 직원 목록 관리

**주요 엔드포인트:**
- `POST /user/login` - 사용자 로그인
- `GET /user/me` - 현재 사용자 정보
- `GET /user/employees` - 전체 직원 목록 (관리자)
- `GET /user/employees/all` - 전체 직원 목록 (일반 사용자)

---

### 2. [Admin Router API](./admin_router_api_spec.md)
**관리자 전용 기능**
- 직원 등록 및 관리
- 시스템 초기화
- 데이터 정리

**주요 엔드포인트:**
- `POST /admin/register-employee` - 직원 등록
- `POST /admin/init-admin` - 초기 관리자 생성
- `DELETE /admin/cleanup-corrupted-documents` - 깨진 문서 정리

---

### 3. [Document Router API](./document_router_api_spec.md)
**문서 관리 시스템**
- 문서 업로드 및 관리
- 다양한 파일 형식 지원
- 문서 분석 및 처리

**지원 파일 형식:**
- **텍스트**: PDF, DOCX, TXT
- **데이터**: CSV, Excel (XLSX, XLS)

**주요 엔드포인트:**
- `POST /documents/upload` - 문서 업로드
- `GET /documents/` - 문서 목록 조회
- `GET /documents/{doc_id}` - 특정 문서 조회
- `DELETE /documents/{doc_id}` - 문서 삭제 (관리자)

---

### 4. [QA Router API](./qa_router_api_spec.md)
**자연어 질문-답변 시스템**
- 자연어 질문 처리
- 문서 기반 답변 생성
- 시스템 상태 모니터링

**주요 엔드포인트:**
- `GET /qa/health` - QA 시스템 상태 확인
- `POST /qa/question` - 자연어 질문-답변
- `POST /qa/test` - 테스트 질문-답변

---

### 5. [Hybrid Search Router API](./hybrid_search_router_api_spec.md)
**통합 검색 시스템**
- 테이블 및 텍스트 통합 검색
- 검색 통계 및 분석
- 성능 모니터링

**주요 엔드포인트:**
- `POST /search/hybrid` - 하이브리드 검색 (POST)
- `GET /search/hybrid` - 하이브리드 검색 (GET)
- `GET /search/hybrid/stats` - 검색 통계

---

### 6. [Chat History Router API](./chat_history_router_api_spec.md)
**채팅 시스템** (Base URL: `/api/chat-history`)
- 채팅 세션 관리
- 대화 기록 저장 및 조회
- 세션 보관 및 복원

**주요 엔드포인트:**
- `POST /api/chat-history/save-message` - 메시지 저장
- `POST /api/chat-history/get-history` - 대화 기록 조회
- `POST /api/chat-history/get-session-info` - 세션 정보 조회
- `GET /api/chat-history/sessions/{employee_id}` - 사용자 세션 목록
- `PUT /api/chat-history/session/{session_id}/title` - 세션 제목 업데이트
- `POST /api/chat-history/session/{session_id}/archive` - 세션 보관
- `POST /api/chat-history/session/{session_id}/restore` - 세션 복원
- `DELETE /api/chat-history/session/{session_id}` - 세션 삭제
- `GET /api/chat-history/health` - 시스템 상태 확인

---

## 🔐 인증 시스템

### JWT 토큰 사용법
```bash
# 1. 로그인하여 토큰 획득
curl -X POST "http://localhost:8010/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=password123"

# 2. 토큰을 헤더에 포함하여 API 호출
curl -X GET "http://localhost:8010/user/me" \
  -H "Authorization: Bearer <access_token>"
```

### 권한 레벨
- **일반 사용자 (user)**: 기본 기능 접근
- **관리자 (admin)**: 모든 기능 접근

---

## 🚀 빠른 시작 가이드

### 1. 시스템 초기화
```bash
# 초기 관리자 계정 생성
curl -X POST "http://localhost:8010/admin/init-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "admin123",
    "name": "시스템 관리자",
    "role": "admin"
  }'
```

### 2. 로그인
```bash
# 관리자 로그인
curl -X POST "http://localhost:8010/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```

### 3. 문서 업로드
```bash
# 문서 업로드
curl -X POST "http://localhost:8010/documents/upload" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@sample.pdf" \
  -F "doc_title=샘플 문서" \
  -F "uploader_id=1"
```

### 4. 질문-답변
```bash
# 자연어 질문
curl -X POST "http://localhost:8010/qa/question" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "회사의 매출 현황은 어떻게 되나요?",
    "top_k": 5
  }'
```

### 5. 검색
```bash
# 하이브리드 검색
curl -X POST "http://localhost:8010/search/hybrid" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "매출 현황",
    "limit": 20
  }'
```

---

## 🔧 개발 환경 설정

### 필수 환경 변수
```bash
# 데이터베이스 설정
DATABASE_URL=postgresql://myuser:mypassword@postgres:5432/mydatabase

# JWT 설정
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# MinIO 설정
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT_URL=http://minio:9000
```

### Docker 실행
```bash
# 서비스 시작
cd docker
docker-compose up -d

# 마이그레이션 실행
docker exec -it fastapi-app alembic upgrade head
```

---

## 📝 에러 코드 참조

### HTTP 상태 코드
- **200**: 성공
- **400**: 잘못된 요청
- **401**: 인증 실패
- **403**: 권한 없음
- **404**: 리소스 없음
- **500**: 서버 오류

### 일반적인 에러 메시지
- `"Could not validate credentials"`: 토큰 만료 또는 잘못됨
- `"Admin privileges required"`: 관리자 권한 필요
- `"문서를 찾을 수 없습니다"`: 존재하지 않는 문서
- `"QA 시스템에 문제가 있습니다"`: QA 시스템 오류

---

## 📞 지원 및 문의

### 문제 해결
1. **로그 확인**: `docker logs fastapi-app`
2. **상태 확인**: 각 API의 `/health` 엔드포인트
3. **데이터베이스 연결**: PostgreSQL 컨테이너 상태 확인

### 개발 가이드
- **API 테스트**: Postman 또는 curl 사용
- **문서화**: Swagger UI (`http://localhost:8010/docs`)
- **모니터링**: 각 API의 통계 엔드포인트 활용

---

## 📄 라이선스 및 버전

- **버전**: 1.0.0
- **최종 업데이트**: 2024년 1월

---

## 🔄 업데이트 로그

### v1.0.0 (2024-01-01)
- 모든 API 명세서 초기 작성
- JWT 인증 시스템 구현
- 하이브리드 검색 기능 추가
- QA 시스템 통합
- 채팅 시스템 구현 