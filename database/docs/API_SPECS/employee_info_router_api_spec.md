# Employee Info API 명세서

## 개요
직원 인사 정보를 조회하는 API 엔드포인트입니다. 직원의 기본 정보, 조직 정보, 급여 정보, 평가 정보 등을 제공합니다.

## 인증
모든 엔드포인트는 JWT 토큰 인증이 필요합니다.
- Header: `Authorization: Bearer {token}`

## 엔드포인트

### 1. 직원 정보 리스트 조회
직원 정보 목록을 조회합니다.

- **URL**: `/employee-info`
- **Method**: `GET`
- **인증 필요**: Yes

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skip | integer | No | 페이지네이션 오프셋 (기본값: 0) |
| limit | integer | No | 페이지 크기 (기본값: 100) |
| branch_id | integer | No | 특정 지점의 직원만 조회 |
| position | string | No | 특정 직급의 직원만 조회 |
| name | string | No | 이름으로 검색 (부분 일치) |
| approval_status | string | No | 승인 상태로 필터링 (pending/approved/rejected) |

#### Response
**Status Code**: 200 OK

**Response Body**:
```json
[
  {
    "employee_info_id": 1,
    "employee_id": 10,
    "name": "홍길동",
    "employee_number": "EMP001",
    "position": "과장",
    "branch_id": 5,
    "contact_number": "010-1234-5678",
    "base_salary": 4000000,
    "incentive_pay": 500000,
    "avg_monthly_budget": 2000000,
    "latest_evaluation": "A",
    "responsibilities": "영업 관리",
    "is_auto_created": false,
    "approval_status": "approved",
    "approved_by": 1,
    "approved_at": "2024-01-15T10:30:00",
    "approval_notes": "승인 완료",
    "created_at": "2024-01-10T09:00:00",
    "updated_at": "2024-01-15T10:30:00",
    "branch_name": "강남지점",
    "headquarters": "서울본부",
    "department": "영업부"
  }
]
```

#### 권한
- **일반 사용자**: 승인된(approved) 정보만 조회 가능
- **관리자(admin)**: 모든 정보 조회 가능

---

### 2. 직원 상세 정보 조회
특정 직원의 상세 정보를 조회합니다.

- **URL**: `/employee-info/{employee_info_id}`
- **Method**: `GET`
- **인증 필요**: Yes

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| employee_info_id | integer | Yes | 조회할 직원 정보 ID |

#### Response
**Status Code**: 200 OK

**Response Body**:
```json
{
  "employee_info_id": 1,
  "employee_id": 10,
  "name": "홍길동",
  "employee_number": "EMP001",
  "position": "과장",
  "branch_id": 5,
  "contact_number": "010-1234-5678",
  "base_salary": 4000000,
  "incentive_pay": 500000,
  "avg_monthly_budget": 2000000,
  "latest_evaluation": "A",
  "responsibilities": "영업 관리",
  "is_auto_created": false,
  "approval_status": "approved",
  "approved_by": 1,
  "approved_at": "2024-01-15T10:30:00",
  "approval_notes": "승인 완료",
  "created_at": "2024-01-10T09:00:00",
  "updated_at": "2024-01-15T10:30:00",
  "branch_name": "강남지점",
  "headquarters": "서울본부",
  "department": "영업부"
}
```

#### Error Responses
- **404 Not Found**: 직원 정보를 찾을 수 없습니다.
- **403 Forbidden**: 승인되지 않은 직원 정보입니다. (일반 사용자가 미승인 정보 조회 시)

---

### 3. 직원 계정 ID로 정보 조회
직원 계정 ID를 사용하여 직원 정보를 조회합니다.

- **URL**: `/employee-info/by-employee/{employee_id}`
- **Method**: `GET`
- **인증 필요**: Yes

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| employee_id | integer | Yes | 직원 계정 ID (employees 테이블의 employee_id) |

#### Response
**Status Code**: 200 OK

**Response Body**: 
위의 직원 상세 정보 조회와 동일한 형식. 해당 직원 정보가 없는 경우 `null` 반환

#### Error Responses
- **403 Forbidden**: 승인되지 않은 직원 정보입니다. (일반 사용자가 미승인 정보 조회 시)

---

### 4. 이름으로 직원 검색
직원 이름으로 검색합니다. (부분 일치)

- **URL**: `/employee-info/search/by-name`
- **Method**: `GET`
- **인증 필요**: Yes

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | 검색할 직원 이름 |

#### Response
**Status Code**: 200 OK

**Response Body**:
```json
[
  {
    "employee_info_id": 1,
    "employee_id": 10,
    "name": "홍길동",
    "employee_number": "EMP001",
    "position": "과장",
    "branch_id": 5,
    "contact_number": "010-1234-5678",
    "base_salary": 4000000,
    "incentive_pay": 500000,
    "avg_monthly_budget": 2000000,
    "latest_evaluation": "A",
    "responsibilities": "영업 관리",
    "is_auto_created": false,
    "approval_status": "approved",
    "approved_by": 1,
    "approved_at": "2024-01-15T10:30:00",
    "approval_notes": "승인 완료",
    "created_at": "2024-01-10T09:00:00",
    "updated_at": "2024-01-15T10:30:00",
    "branch_name": "강남지점",
    "headquarters": "서울본부",
    "department": "영업부"
  }
]
```

검색 결과가 없는 경우 빈 배열 `[]` 반환

#### 권한
- **일반 사용자**: 승인된(approved) 정보만 검색 가능
- **관리자(admin)**: 모든 정보 검색 가능

---

## 데이터 모델

### EmployeeInfoWithBranch
직원 정보와 지점 정보를 포함한 응답 모델

| Field | Type | Description |
|-------|------|-------------|
| employee_info_id | integer | 인사 정보 고유 ID |
| employee_id | integer or null | 직원 계정 ID (employees 테이블 참조) |
| name | string | 직원명 |
| employee_number | string or null | 사번 |
| position | string or null | 직급 (예: 대리, 과장, 차장) |
| branch_id | integer or null | 지점 ID |
| contact_number | string or null | 연락처 |
| base_salary | integer or null | 기본급 (원 단위) |
| incentive_pay | integer or null | 인센티브/성과급 (원 단위) |
| avg_monthly_budget | integer or null | 월 평균 업무 예산 (원 단위) |
| latest_evaluation | string or null | 최근 평가 결과 (예: A, B, C) |
| responsibilities | string or null | 담당 업무 |
| is_auto_created | boolean | 자동 생성 여부 |
| approval_status | string | 승인 상태 (pending/approved/rejected) |
| approved_by | integer or null | 승인자 ID |
| approved_at | datetime or null | 승인 일시 |
| approval_notes | string or null | 승인/거부 메모 |
| created_at | datetime | 생성일시 |
| updated_at | datetime | 수정일시 |
| branch_name | string or null | 지점명 |
| headquarters | string or null | 본부 |
| department | string or null | 부서 |

---

## 에러 코드

| Status Code | Description |
|-------------|-------------|
| 200 | 성공 |
| 401 | 인증 실패 (유효하지 않은 토큰) |
| 403 | 권한 없음 (승인되지 않은 정보 접근 시) |
| 404 | 리소스를 찾을 수 없음 |
| 500 | 서버 내부 오류 |

---

## 사용 예시

### 1. 직원 정보 리스트 조회
```bash
curl -X GET "http://localhost:8010/employee-info?branch_id=5&position=과장" \
  -H "Authorization: Bearer {your_token}"
```

### 2. 특정 직원 정보 조회
```bash
curl -X GET "http://localhost:8010/employee-info/1" \
  -H "Authorization: Bearer {your_token}"
```

### 3. 직원 계정 ID로 조회
```bash
curl -X GET "http://localhost:8010/employee-info/by-employee/10" \
  -H "Authorization: Bearer {your_token}"
```

### 4. 이름으로 검색
```bash
curl -X GET "http://localhost:8010/employee-info/search/by-name?name=홍길동" \
  -H "Authorization: Bearer {your_token}"
```

---

## 주의사항

1. **권한 관리**: 일반 사용자는 승인된 정보만 조회할 수 있으며, 관리자는 모든 정보에 접근 가능합니다.

2. **페이지네이션**: 대량의 데이터 조회 시 `skip`과 `limit` 파라미터를 활용하여 페이지네이션을 구현하세요.

3. **검색 기능**: 이름 검색은 대소문자를 구분하지 않으며, 부분 일치를 지원합니다.

4. **null 값 처리**: 많은 필드가 nullable이므로 클라이언트에서 null 값 처리에 주의하세요.

5. **지점 정보**: 직원이 지점에 배정되지 않은 경우 `branch_name`, `headquarters`, `department` 필드가 null일 수 있습니다.