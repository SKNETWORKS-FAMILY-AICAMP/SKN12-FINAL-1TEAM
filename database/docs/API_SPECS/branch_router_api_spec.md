# 지점 정보 관리 API 명세서

## 개요
지점 정보를 조회하고 검색하는 RESTful API입니다. 지점의 기본 정보, 조직 구조(본부/부서), 연락처 등을 관리하며, 다양한 검색 및 통계 기능을 제공합니다.

## 인증
모든 API는 JWT 토큰 기반 인증이 필요합니다.

### 인증 헤더
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Base URL
```
https://your-domain.com/api
```

---

## 1. 전체 지점 목록 조회

모든 지점 정보를 페이지네이션하여 조회합니다.

### Endpoint
```
GET /branches/
```

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| skip | integer | No | 건너뛸 항목 수 (기본값: 0) | 0 |
| limit | integer | No | 조회할 최대 항목 수 (기본값: 100) | 100 |
| status | string | No | 상태 필터 (active/inactive) | "active" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/branches/?skip=0&limit=10&status=active" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "branch_id": 1,
    "headquarters": "수도권본부",
    "department": "영업1부",
    "branch_name": "서울지점",
    "contact_number": "02-1234-5678",
    "status": "active",
    "notes": "강남 지역 담당",
    "created_at": "2024-01-01T09:00:00",
    "updated_at": "2024-01-15T14:30:00"
  },
  {
    "branch_id": 2,
    "headquarters": "수도권본부",
    "department": "영업2부",
    "branch_name": "인천지점",
    "contact_number": "032-987-6543",
    "status": "active",
    "notes": null,
    "created_at": "2024-01-01T09:00:00",
    "updated_at": null
  }
]
```

#### Error Response (500 Internal Server Error)
```json
{
  "detail": "지점 목록 조회 중 오류가 발생했습니다: [오류 메시지]"
}
```

---

## 2. 지점명으로 검색

지점명을 기준으로 부분 일치 검색을 수행합니다.

### Endpoint
```
GET /branches/search
```

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| name | string | Yes | 검색할 지점명 (부분 일치) | "서울" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/branches/search?name=서울" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "search_term": "서울",
  "count": 2,
  "results": [
    {
      "branch_id": 1,
      "branch_name": "서울지점",
      "headquarters": "수도권본부",
      "department": "영업1부",
      "status": "active",
      "contact_number": "02-1234-5678"
    },
    {
      "branch_id": 3,
      "branch_name": "서울남부지점",
      "headquarters": "수도권본부",
      "department": "영업3부",
      "status": "active",
      "contact_number": "02-2222-3333"
    }
  ]
}
```

#### No Results Response (200 OK)
```json
{
  "search_term": "부산",
  "count": 0,
  "results": []
}
```

---

## 3. 본부별 지점 목록 조회

특정 본부에 속한 모든 지점을 조회합니다.

### Endpoint
```
GET /branches/by-headquarters
```

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| headquarters | string | Yes | 본부명 | "수도권본부" |
| status | string | No | 상태 필터 (active/inactive) | "active" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/branches/by-headquarters?headquarters=수도권본부&status=active" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "branch_id": 1,
    "headquarters": "수도권본부",
    "department": "영업1부",
    "branch_name": "서울지점",
    "contact_number": "02-1234-5678",
    "status": "active",
    "notes": "강남 지역 담당",
    "created_at": "2024-01-01T09:00:00",
    "updated_at": "2024-01-15T14:30:00"
  },
  {
    "branch_id": 2,
    "headquarters": "수도권본부",
    "department": "영업2부",
    "branch_name": "인천지점",
    "contact_number": "032-987-6543",
    "status": "active",
    "notes": null,
    "created_at": "2024-01-01T09:00:00",
    "updated_at": null
  }
]
```

---

## 4. 부서별 지점 목록 조회

특정 부서에 속한 모든 지점을 조회합니다.

### Endpoint
```
GET /branches/by-department
```

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| department | string | Yes | 부서명 | "영업1부" |
| headquarters | string | No | 본부명 (선택사항) | "수도권본부" |
| status | string | No | 상태 필터 (active/inactive) | "active" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/branches/by-department?department=영업1부&headquarters=수도권본부" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "branch_id": 1,
    "headquarters": "수도권본부",
    "department": "영업1부",
    "branch_name": "서울지점",
    "contact_number": "02-1234-5678",
    "status": "active",
    "notes": "강남 지역 담당",
    "created_at": "2024-01-01T09:00:00",
    "updated_at": "2024-01-15T14:30:00"
  },
  {
    "branch_id": 5,
    "headquarters": "수도권본부",
    "department": "영업1부",
    "branch_name": "경기북부지점",
    "contact_number": "031-111-2222",
    "status": "active",
    "notes": null,
    "created_at": "2024-01-05T10:00:00",
    "updated_at": null
  }
]
```

---

## 5. 지점 통계 정보 조회

전체 지점에 대한 통계 정보를 조회합니다.

### Endpoint
```
GET /branches/statistics
```

### Request Example
```bash
curl -X GET "https://your-domain.com/api/branches/statistics" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "total_branches": 100,
  "active_branches": 90,
  "inactive_branches": 10,
  "by_headquarters": {
    "수도권본부": 30,
    "경기본부": 25,
    "충청본부": 15,
    "영남본부": 20,
    "호남본부": 10
  },
  "by_department": {
    "영업1부": 20,
    "영업2부": 18,
    "영업3부": 15,
    "영업4부": 17,
    "특수영업부": 10,
    "관리부": 20
  }
}
```

---

## 6. 특정 지점 상세 정보 조회

지점 ID를 기준으로 특정 지점의 상세 정보를 조회합니다.

### Endpoint
```
GET /branches/{branch_id}
```

### Path Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| branch_id | integer | Yes | 지점 고유 ID | 1 |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/branches/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "branch_id": 1,
  "headquarters": "수도권본부",
  "department": "영업1부",
  "branch_name": "서울지점",
  "contact_number": "02-1234-5678",
  "status": "active",
  "notes": "강남 지역 담당",
  "created_at": "2024-01-01T09:00:00",
  "updated_at": "2024-01-15T14:30:00"
}
```

#### Error Response (404 Not Found)
```json
{
  "detail": "지점 ID 1를 찾을 수 없습니다."
}
```

---

## 공통 에러 응답

### 401 Unauthorized
인증 토큰이 없거나 유효하지 않은 경우
```json
{
  "detail": "Could not validate credentials"
}
```

### 500 Internal Server Error
서버 내부 오류가 발생한 경우
```json
{
  "detail": "[작업명] 중 오류가 발생했습니다: [오류 메시지]"
}
```

---

## 데이터 모델

### BranchInfo Schema
```typescript
interface BranchInfo {
  branch_id: number;           // 지점 고유 ID
  headquarters: string;         // 본부명
  department: string;           // 부서명
  branch_name: string;          // 지점명
  contact_number?: string;      // 연락처 (선택)
  status?: string;              // 상태 (active/inactive)
  notes?: string;               // 비고 (선택)
  created_at?: string;          // 생성일시 (ISO 8601 형식)
  updated_at?: string;          // 수정일시 (ISO 8601 형식)
}
```

---

## 주의사항

1. **인증 필수**: 모든 엔드포인트는 유효한 JWT 토큰이 필요합니다.
2. **페이지네이션**: 대량의 데이터 조회 시 skip과 limit 파라미터를 활용하여 페이지네이션을 구현하세요.
3. **상태 필터링**: status 파라미터를 통해 활성/비활성 지점을 필터링할 수 있습니다.
4. **대소문자 구분 없음**: 검색 기능은 대소문자를 구분하지 않습니다.
5. **부분 일치 검색**: 지점명 검색은 부분 일치 방식으로 동작합니다.

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 1.0.0 | 2025-08-18 | 초기 API 명세서 작성 | System |