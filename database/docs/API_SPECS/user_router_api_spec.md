# User Router API 명세서

## 개요
사용자 인증 및 관리 기능을 제공하는 API입니다.

## 기본 정보
- **Base URL**: `/user`
- **Content-Type**: `application/json`
- **인증**: JWT 토큰 기반

## API 엔드포인트

### 1. 사용자 로그인
**POST** `/user/login`

#### 요청 본문 (Form Data)
```
username: string (필수, 실제로는 이메일 주소를 입력)
password: string (필수)
```

**참고**: OAuth2 표준에 따라 필드명은 'username'이지만, 실제로는 이메일 주소를 입력해야 합니다.

#### 응답
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=password123"
```

---

### 2. 현재 사용자 정보 조회
**GET** `/user/me`

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 응답
```json
{
  "employee_id": 1,
  "email": "admin@example.com",
  "name": "관리자",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/user/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 3. 전체 직원 목록 조회 (관리자만)
**GET** `/user/employees`

#### 헤더
```
Authorization: Bearer <admin_token>
```

#### 응답
```json
[
  {
    "employee_id": 1,
    "email": "admin@example.com",
    "name": "관리자",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z"
  },
  {
    "employee_id": 2,
    "email": "user@example.com",
    "name": "일반 사용자",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/user/employees" \
  -H "Authorization: Bearer <admin_token>"
```

---

### 4. 전체 직원 목록 조회 (일반 사용자)
**GET** `/user/employees/all`

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 응답
```json
[
  {
    "employee_id": 1,
    "email": "admin@example.com",
    "name": "관리자",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z"
  },
  {
    "employee_id": 2,
    "email": "user@example.com",
    "name": "일반 사용자",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/user/employees/all" \
  -H "Authorization: Bearer <access_token>"
```

#### 기능 설명
- 일반 사용자도 전체 직원 목록을 조회할 수 있음
- 관리자 전용 엔드포인트와 동일한 데이터 반환
- 권한 차이는 없지만 별도 엔드포인트로 제공

---

## 에러 응답

### 400 Bad Request
```json
{
  "detail": "Incorrect email or password"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

### 403 Forbidden
```json
{
  "detail": "Admin privileges required"
}
```

---

## JWT 토큰 사용법

### 토큰 획득
1. `/user/login` 엔드포인트로 로그인
2. 응답에서 `access_token` 추출

### 토큰 사용
- 모든 보호된 API 호출 시 `Authorization: Bearer <token>` 헤더 포함
- 토큰 만료 시간: 60분 (기본값)

### 토큰 검증
- 모든 보호된 엔드포인트에서 자동으로 토큰 검증
- 만료된 토큰이나 잘못된 토큰은 401 에러 반환

---

## 권한 레벨

### 일반 사용자 (user)
- 자신의 정보 조회 (`/user/me`)
- 전체 직원 목록 조회 (`/user/employees/all`)

### 관리자 (admin)
- 모든 일반 사용자 권한
- 전체 직원 목록 조회 (`/user/employees`)

---

## 주의사항

1. **로그인 필드**: OAuth2 표준에 따라 'username' 필드명을 사용하지만, 실제로는 이메일 주소를 입력
2. **토큰 보안**: 토큰을 안전하게 보관하고 노출하지 마세요
3. **토큰 만료**: 60분 후 자동 만료되므로 재로그인 필요
4. **권한 확인**: 관리자 기능은 admin 역할이 필요합니다
5. **HTTPS 사용**: 프로덕션 환경에서는 반드시 HTTPS 사용
6. **직원 목록**: 일반 사용자와 관리자 모두 전체 직원 목록 조회 가능 