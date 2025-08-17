# Admin Router API 명세서

## 개요
관리자 전용 기능을 제공하는 API입니다. 직원 등록, 시스템 관리 등의 기능을 포함합니다.

## 기본 정보
- **Base URL**: `/admin`
- **Content-Type**: `application/json`
- **인증**: 관리자 권한 필요 (admin role)

## API 엔드포인트

### 1. 직원 등록 (관리자만)
**POST** `/admin/register-employee`

#### 설명
employee_info 테이블에 등록된 직원에 대해서만 계정을 생성합니다. 이름과 사번으로 직원을 확인하고, 검증 후 계정을 생성하여 employee_info와 연결합니다.

#### 헤더
```
Authorization: Bearer <admin_token>
```

#### 요청 본문
```json
{
  "name": "홍길동",
  "employee_number": "EMP001",
  "email": "hong@example.com",
  "password": "password123",
  "role": "user"
}
```

#### 요청 필드
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | Y | 직원 이름 (employee_info 테이블과 일치해야 함) |
| employee_number | string | Y | 사번 (employee_info 테이블과 일치해야 함) |
| email | string | Y | 이메일 주소 (유니크해야 함) |
| password | string | Y | 패스워드 (최소 8자) |
| role | string | N | 역할 (user/manager/admin, 기본값: user) |

#### 응답
```json
{
  "employee_id": 3,
  "email": "hong@example.com",
  "name": "홍길동",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 프로세스
1. employee_info 테이블에서 이름과 사번으로 직원 조회
2. 직원이 존재하는지 확인
3. 이미 계정이 있는지 확인 (employee_id가 설정되어 있는지)
4. 이메일 중복 확인
5. 계정 생성 (employees 테이블)
6. employee_info 테이블의 employee_id 필드 업데이트

#### 에러 응답
- **404**: 등록되지 않은 직원입니다. 인사 정보를 먼저 등록해주세요.
- **400**: 해당 직원은 이미 계정이 존재합니다.
- **400**: 이메일이 이미 사용중입니다.
- **500**: 계정 생성 중 오류가 발생했습니다.

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/admin/register-employee" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "홍길동",
    "employee_number": "EMP001",
    "email": "hong@example.com",
    "password": "password123",
    "role": "user"
  }'
```

---

### 2. 초기 관리자 계정 생성
**POST** `/admin/init-admin`

#### 요청 본문
```json
{
  "email": "admin@example.com",
  "password": "admin123",
  "name": "시스템 관리자",
  "role": "admin"
}
```

#### 응답
```json
{
  "employee_id": 1,
  "email": "admin@example.com",
  "name": "시스템 관리자",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/admin/init-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123",
    "name": "시스템 관리자",
    "role": "admin"
  }'
```

#### 주의사항
- 최초 1회만 사용 가능
- 이미 관리자가 존재하면 400 에러 반환
- 인증이 필요하지 않음 (시스템 초기화용)

---

### 3. 깨진 문서 정리
**DELETE** `/admin/cleanup-corrupted-documents`

#### 헤더
```
Authorization: Bearer <admin_token>
```

#### 응답
```json
{
  "success": true,
  "message": "깨진 문서 데이터 정리 완료: 5개 청크 삭제됨",
  "deleted_count": 5
}
```

#### 사용 예시
```bash
curl -X DELETE "http://localhost:8010/admin/cleanup-corrupted-documents" \
  -H "Authorization: Bearer <admin_token>"
```

#### 기능 설명
- OpenSearch에서 깨진 텍스트가 포함된 문서 청크들을 삭제
- 시스템 성능 향상 및 데이터 무결성 보장
- 관리자만 접근 가능
- 삭제된 청크 수 반환

#### 삭제 대상 패턴
- "ߩ+)]N" - 실제 결과에서 발견된 패턴
- "\\u6M~g~l" - 유니코드 깨짐 패턴
- "zi'$&3" - 바이너리 깨짐 패턴
- "xml]O0" - XML 파싱 오류 패턴

---

## 에러 응답

### 400 Bad Request
```json
{
  "detail": "해당 직원은 이미 계정이 존재합니다."
}
```

```json
{
  "detail": "이메일이 이미 사용중입니다."
}
```

```json
{
  "detail": "관리자 계정이 이미 존재합니다."
}
```

```json
{
  "detail": "role은 반드시 'admin'이어야 합니다."
}
```

### 404 Not Found
```json
{
  "detail": "등록되지 않은 직원입니다. 인사 정보를 먼저 등록해주세요."
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin privileges required"
}
```

### 500 Internal Server Error
```json
{
  "detail": "관리자 계정 생성 중 오류 발생: <error_message>"
}
```

```json
{
  "detail": "OpenSearch 클라이언트가 초기화되지 않았습니다."
}
```

---

## 권한 요구사항

### 관리자 권한이 필요한 기능
- 직원 등록 (`/admin/register-employee`)
- 깨진 문서 정리 (`/admin/cleanup-corrupted-documents`)

### 인증 불필요한 기능
- 초기 관리자 생성 (`/admin/init-admin`) - 시스템 초기화용

---

## 초기 관리자 생성 프로세스

### 1단계: 시스템 초기화
```bash
# 최초 관리자 계정 생성
curl -X POST "http://localhost:8010/admin/init-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123",
    "name": "시스템 관리자",
    "role": "admin"
  }'
```

### 2단계: 관리자 로그인
```bash
# 생성된 관리자로 로그인
curl -X POST "http://localhost:8010/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```

### 3단계: 추가 직원 등록
```bash
# 관리자 토큰으로 추가 직원 등록
# 주의: employee_info 테이블에 미리 등록된 직원만 계정 생성 가능
curl -X POST "http://localhost:8010/admin/register-employee" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "김직원",
    "employee_number": "EMP002",
    "email": "kim@example.com",
    "password": "password123",
    "role": "user"
  }'
```

---

## 시스템 관리 기능

### 깨진 문서 정리
- **목적**: OpenSearch에서 깨진 텍스트 청크 제거
- **대상**: 특정 패턴이 포함된 문서 청크
- **권한**: 관리자만 실행 가능
- **안전성**: 삭제 전 백업 권장

### 정리 프로세스
1. 깨진 텍스트 패턴 정의
2. OpenSearch에서 패턴 검색
3. 해당 청크들 삭제
4. 삭제된 개수 반환

---

## 주의사항ㅇ

1. **초기 관리자 생성**: 시스템 최초 실행 시에만 사용
2. **직원 계정 생성**: employee_info 테이블에 먼저 직원 정보가 등록되어 있어야 계정 생성 가능
3. **관리자 권한**: 대부분의 기능은 admin 역할이 필요
4. **데이터 백업**: 깨진 문서 정리 전에 데이터 백업 권장
5. **보안**: 관리자 계정 정보를 안전하게 보관
6. **토큰 관리**: 관리자 토큰의 안전한 보관 및 사용
7. **문서 정리**: 깨진 문서 정리는 신중하게 실행
8. **계정 연결**: 계정 생성 시 자동으로 employee_info와 연결됨 