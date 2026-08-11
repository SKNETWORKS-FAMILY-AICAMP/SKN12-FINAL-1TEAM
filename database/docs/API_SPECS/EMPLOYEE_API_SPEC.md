# 직원 실적 분석 데이터 API 명세서

## 개요
직원별 실적 데이터를 조회하고 분석하는 RESTful API입니다. 월별 실적, 제품별 판매, 고객별 매출 등의 데이터를 관리하며, 목표 대비 달성률 분석 기능을 제공합니다.

## 인증
모든 API는 JWT 토큰 기반 인증이 필요합니다.

### 인증 헤더
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Base URL
```
http://localhost:8010/employee
```

---

## 1. 직원 목록 조회

활성화된 직원 목록을 조회합니다.

### Endpoint
```
GET /employees
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| department | string | No | 부서명으로 필터링 | "영업1팀" |
| is_active | boolean | No | 활성 직원만 조회 (기본값: true) | true |

### Request Example
```bash
curl -X GET "http://localhost:8010/employee/employees?is_active=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "employee_id": 1,
    "name": "조시현",
    "사번": "MR-01026",
    "department": "영업1팀",
    "email": "user1@example.com",
    "role": "user"
  },
  {
    "employee_id": 2,
    "name": "김영희",
    "사번": "MR-01027",
    "department": "영업2팀",
    "email": "user2@example.com",
    "role": "user"
  }
]
```

---

## 2. 직원 월별 실적 조회

특정 직원의 월별 실적 데이터를 조회합니다.

### Endpoint
```
GET /performance/{employee_id}
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| employee_id | integer | Yes | 직원 ID (Path Parameter) | 1 |
| start_period | string | Yes | 시작 기간 (YYYYMM) | "202301" |
| end_period | string | Yes | 종료 기간 (YYYYMM) | "202312" |

### Request Example
```bash
curl -X GET "http://localhost:8010/employee/performance/1?start_period=202312&end_period=202403" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "employee_id": 1,
    "employee_name": "조시현",
    "year_month": "202312",
    "target_amount": 200000.0,
    "actual_sales": 229005.0,
    "achievement_rate": 114.5,
    "sales_count": 149,
    "customer_count": 27
  },
  {
    "employee_id": 1,
    "employee_name": "조시현",
    "year_month": "202401",
    "target_amount": 220000.0,
    "actual_sales": 200709.0,
    "achievement_rate": 91.2,
    "sales_count": 157,
    "customer_count": 27
  }
]
```

#### Error Responses

**403 Forbidden - 권한 없음**
```json
{
  "detail": "본인 데이터만 조회 가능합니다."
}
```

---

## 3. 직원 실적 요약 조회

특정 직원의 기간별 실적 요약 정보를 조회합니다.

### Endpoint
```
GET /performance/{employee_id}/summary
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| employee_id | integer | Yes | 직원 ID (Path Parameter) | 1 |
| start_period | string | Yes | 시작 기간 (YYYYMM) | "202301" |
| end_period | string | Yes | 종료 기간 (YYYYMM) | "202312" |

### Request Example
```bash
curl -X GET "http://localhost:8010/employee/performance/1/summary?start_period=202312&end_period=202403" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "employee_id": 1,
  "period": "202312~202403",
  "month_count": 4,
  "total_target": 1100000,
  "total_sales": 1126004,
  "avg_achievement_rate": 102.4,
  "total_sales_count": 644,
  "unique_customers": 32
}
```

---

## 4. 제품별 실적 조회

특정 직원의 제품별 판매 실적을 조회합니다.

### Endpoint
```
GET /performance/{employee_id}/products
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| employee_id | integer | Yes | 직원 ID (Path Parameter) | 1 |
| start_period | string | Yes | 시작 기간 (YYYYMM) | "202301" |
| end_period | string | Yes | 종료 기간 (YYYYMM) | "202312" |
| limit | integer | No | 상위 N개 제품 (기본값: 10) | 5 |

### Request Example
```bash
curl -X GET "http://localhost:8010/employee/performance/1/products?start_period=202312&end_period=202403&limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "product_id": 7,
    "product_name": "라베모어정",
    "total_amount": 10605778.0,
    "sales_count": 41,
    "percentage": 27.71
  },
  {
    "product_id": 27,
    "product_name": "하이콘티세미서방정",
    "total_amount": 7754005.0,
    "sales_count": 16,
    "percentage": 20.26
  },
  {
    "product_id": 22,
    "product_name": "가스몬정",
    "total_amount": 6794476.0,
    "sales_count": 15,
    "percentage": 17.75
  }
]
```

---

## 5. 고객별 실적 조회

특정 직원의 고객별 매출 실적을 조회합니다.

### Endpoint
```
GET /performance/{employee_id}/customers
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| employee_id | integer | Yes | 직원 ID (Path Parameter) | 1 |
| start_period | string | Yes | 시작 기간 (YYYYMM) | "202301" |
| end_period | string | Yes | 종료 기간 (YYYYMM) | "202312" |
| limit | integer | No | 상위 N개 고객 (기본값: 10) | 5 |

### Request Example
```bash
curl -X GET "http://localhost:8010/employee/performance/1/customers?start_period=202312&end_period=202403&limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "customer_id": 23,
    "customer_name": "연세정형외과",
    "customer_grade": "A",
    "total_amount": 22776816.0,
    "sales_count": 61,
    "percentage": 33.8
  },
  {
    "customer_id": 18,
    "customer_name": "상쾌한이비인후과",
    "customer_grade": "B",
    "total_amount": 12008884.0,
    "sales_count": 22,
    "percentage": 17.82
  }
]
```

---

## 6. 부서 목록 조회

전체 부서 목록을 조회합니다.

### Endpoint
```
GET /departments
```

### Request Example
```bash
curl -X GET "http://localhost:8010/employee/departments" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  "강남팀",
  "강북팀",
  "경기1팀",
  "경기2팀",
  "영업1팀",
  "영업2팀"
]
```

---

## 7. 에이전트용 실적 데이터 조회

AI 에이전트가 사용하는 구조화된 실적 데이터를 조회합니다.

### Endpoint
```
GET /agent/performance-data
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| employee_name | string | Yes | 직원 이름 | "조시현" |
| start_period | string | Yes | 시작 기간 (YYYYMM) | "202301" |
| end_period | string | Yes | 종료 기간 (YYYYMM) | "202312" |

### Request Example
```bash
curl -X GET "http://localhost:8010/employee/agent/performance-data?employee_name=조시현&start_period=202312&end_period=202403" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "employee_info": {
    "employee_id": 1,
    "name": "조시현",
    "사번": "MR-01026",
    "department": "영업1팀"
  },
  "performance_data": [
    {
      "employee_id": 1,
      "employee_name": "조시현",
      "year_month": "202312",
      "target_amount": 200000,
      "actual_sales": 229005.0,
      "achievement_rate": 114.5,
      "sales_count": 149,
      "customer_count": 27
    },
    {
      "employee_id": 1,
      "employee_name": "조시현",
      "year_month": "202401",
      "target_amount": 220000,
      "actual_sales": 200709.0,
      "achievement_rate": 91.2,
      "sales_count": 157,
      "customer_count": 27
    }
  ],
  "period": {
    "start": "202312",
    "end": "202403"
  }
}
```

#### Error Responses

**404 Not Found - 직원을 찾을 수 없음**
```json
{
  "detail": "직원 '홍길동'을 찾을 수 없습니다."
}
```

---

## 공통 에러 응답

### 401 Unauthorized - 인증 실패
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden - 권한 부족
```json
{
  "detail": "본인 데이터만 조회 가능합니다."
}
```

### 500 Internal Server Error
```json
{
  "detail": "서버 내부 오류가 발생했습니다."
}
```

---

## 권한 정책

### 일반 직원 (role: user)
- 본인의 실적 데이터만 조회 가능
- 직원 목록 조회 시 본인 정보만 표시

### 관리자 (role: admin, manager)
- 모든 직원의 실적 데이터 조회 가능
- 전체 직원 목록 조회 가능
- 부서별 필터링 가능

---

## 데이터 모델

### PerformanceData
| Field | Type | Description |
|-------|------|-------------|
| employee_id | integer | 직원 ID |
| employee_name | string | 직원명 |
| year_month | string | 연월 (YYYYMM) |
| target_amount | float | 목표 금액 |
| actual_sales | float | 실제 매출 |
| achievement_rate | float | 달성률 (%) |
| sales_count | integer | 판매 건수 |
| customer_count | integer | 고객 수 |

### ProductPerformance
| Field | Type | Description |
|-------|------|-------------|
| product_id | integer | 제품 ID |
| product_name | string | 제품명 |
| total_amount | float | 총 매출액 |
| sales_count | integer | 판매 건수 |
| percentage | float | 비율 (%) |

### CustomerPerformance
| Field | Type | Description |
|-------|------|-------------|
| customer_id | integer | 고객 ID |
| customer_name | string | 고객명 |
| customer_grade | string | 고객 등급 |
| total_amount | float | 총 매출액 |
| sales_count | integer | 거래 건수 |
| percentage | float | 비율 (%) |

---

## 주의사항

1. **날짜 형식**: 모든 기간 파라미터는 YYYYMM 형식을 사용합니다.
2. **인증**: 모든 API 호출 시 유효한 JWT 토큰이 필요합니다.
3. **권한**: 일반 직원은 본인 데이터만 조회 가능하며, 관리자만 전체 직원 데이터를 조회할 수 있습니다.
4. **성능**: 대량의 데이터 조회 시 limit 파라미터를 사용하여 결과를 제한하는 것을 권장합니다.
5. **한글 인코딩**: employee_name 파라미터에 한글 사용 시 URL 인코딩이 필요합니다.

---

## 변경 이력

| Version | Date | Description | Author |
|---------|------|-------------|--------|
| 1.0.0 | 2025-08-13 | 초기 버전 작성 | System |

---

## 문의사항

API 관련 문의사항은 다음 채널을 통해 문의해주세요:
- Email: api-support@company.com
- Slack: #api-support