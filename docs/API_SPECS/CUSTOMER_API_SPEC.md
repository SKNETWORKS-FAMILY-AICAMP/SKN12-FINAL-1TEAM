# 거래처 성과 관리 API 명세서

## 개요
거래처(고객)별 월간 성과 데이터를 조회하고 분석하는 RESTful API입니다. 매출, 예산, 환자수 등의 데이터를 월 단위로 관리하며, 기간별 조회 및 비교 기능을 제공합니다.

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

## 1. 단일 거래처 성과 조회

특정 거래처의 지정 기간 동안의 월별 성과 데이터를 조회합니다.

### Endpoint
```
GET /customer/{customer_id}/performance
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| customer_id | integer | Yes | 거래처 고유 ID (Path Parameter) | 1 |
| start_month | string | Yes | 조회 시작 월 (YYYYMM 형식) | "202401" |
| end_month | string | Yes | 조회 종료 월 (YYYYMM 형식) | "202412" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/customer/1/performance?start_month=202401&end_month=202412" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "customer_id": 1,
  "customer_name": "서울병원",
  "customer_grade": "A",
  "period": {
    "start": "202401",
    "end": "202412"
  },
  "monthly_data": [
    {
      "month": "202401",
      "매출": 2500000,
      "사용예산": 400000,
      "총환자수": 1500
    },
    {
      "month": "202402",
      "매출": 2800000,
      "사용예산": 420000,
      "총환자수": 1600
    },
    {
      "month": "202403",
      "매출": 2600000,
      "사용예산": 410000,
      "총환자수": 1550
    }
    // ... 각 월별 데이터 계속
  ],
  "summary": {
    "total_sales": 32100000,
    "total_budget": 4920000,
    "total_patients": 18650,
    "average_monthly_sales": 2675000,
    "average_monthly_budget": 410000,
    "average_monthly_patients": 1554,
    "month_count": 12
  }
}
```

#### Error Responses

**400 Bad Request - 날짜 형식 오류**
```json
{
  "detail": "잘못된 날짜 형식입니다. YYYYMM 형식을 사용하세요."
}
```

**400 Bad Request - 날짜 순서 오류**
```json
{
  "detail": "시작 월이 종료 월보다 늦을 수 없습니다."
}
```

**404 Not Found - 거래처 없음**
```json
{
  "detail": "거래처 ID 1를 찾을 수 없습니다."
}
```

**401 Unauthorized - 인증 실패**
```json
{
  "detail": "Could not validate credentials"
}
```

### Response Fields Description

| Field | Type | Description |
|-------|------|-------------|
| customer_id | integer | 거래처 고유 ID |
| customer_name | string | 거래처명 (병원/약국명) |
| customer_grade | string | 거래처 등급 (A, B, C, VIP 등) |
| period | object | 조회 기간 정보 |
| period.start | string | 조회 시작 월 (YYYYMM) |
| period.end | string | 조회 종료 월 (YYYYMM) |
| monthly_data | array | 월별 상세 데이터 배열 |
| monthly_data[].month | string | 해당 월 (YYYYMM) |
| monthly_data[].매출 | number | 월 매출액 (원) |
| monthly_data[].사용예산 | number | 월 사용 예산 (원) |
| monthly_data[].총환자수 | number | 월 총 환자수 (명) |
| summary | object | 전체 기간 요약 통계 |
| summary.total_sales | number | 기간 총 매출액 (원) |
| summary.total_budget | number | 기간 총 사용 예산 (원) |
| summary.total_patients | number | 기간 총 환자수 (명) |
| summary.average_monthly_sales | number | 월 평균 매출액 (원) |
| summary.average_monthly_budget | number | 월 평균 사용 예산 (원) |
| summary.average_monthly_patients | number | 월 평균 환자수 (명) |
| summary.month_count | integer | 데이터가 있는 월 수 |

---

## 2. 다중 거래처 성과 조회

여러 거래처의 성과 데이터를 한 번에 조회합니다.

### Endpoint
```
GET /customers/performance
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| customer_ids | string | Yes | 거래처 ID 목록 (쉼표 구분) | "1,2,3,5" |
| start_month | string | Yes | 조회 시작 월 (YYYYMM 형식) | "202401" |
| end_month | string | Yes | 조회 종료 월 (YYYYMM 형식) | "202412" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/customers/performance?customer_ids=1,2,3&start_month=202401&end_month=202412" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "customer_id": 1,
    "customer_name": "서울병원",
    "customer_grade": "A",
    "period": {
      "start": "202401",
      "end": "202412"
    },
    "monthly_data": [
      {
        "month": "202401",
        "매출": 2500000,
        "사용예산": 400000,
        "총환자수": 1500
      }
      // ... 월별 데이터
    ],
    "summary": {
      "total_sales": 32100000,
      "total_budget": 4920000,
      "total_patients": 18650,
      "average_monthly_sales": 2675000,
      "average_monthly_budget": 410000,
      "average_monthly_patients": 1554,
      "month_count": 12
    }
  },
  {
    "customer_id": 2,
    "customer_name": "부산의원",
    "customer_grade": "B",
    "period": {
      "start": "202401",
      "end": "202412"
    },
    "monthly_data": [
      // ... 월별 데이터
    ],
    "summary": {
      // ... 요약 통계
    }
  },
  {
    "customer_id": 3,
    "customer_name": "대구약국",
    "customer_grade": "C",
    "period": {
      "start": "202401",
      "end": "202412"
    },
    "monthly_data": [
      // ... 월별 데이터
    ],
    "summary": {
      // ... 요약 통계
    }
  }
]
```

#### Error Responses

**400 Bad Request - ID 형식 오류**
```json
{
  "detail": "잘못된 거래처 ID 형식입니다. 숫자를 쉼표로 구분하여 입력하세요."
}
```

### Notes
- 존재하지 않는 거래처 ID는 조용히 무시되고, 결과에서 제외됩니다
- 최대 한 번에 조회 가능한 거래처 수는 시스템 설정에 따라 제한될 수 있습니다

---

## 3. 거래처 성과 기간 비교

특정 거래처의 두 기간 성과를 비교 분석합니다.

### Endpoint
```
GET /customer/{customer_id}/performance/comparison
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| customer_id | integer | Yes | 거래처 고유 ID (Path Parameter) | 1 |
| period1_start | string | Yes | 첫 번째 기간 시작 월 (YYYYMM) | "202301" |
| period1_end | string | Yes | 첫 번째 기간 종료 월 (YYYYMM) | "202306" |
| period2_start | string | Yes | 두 번째 기간 시작 월 (YYYYMM) | "202401" |
| period2_end | string | Yes | 두 번째 기간 종료 월 (YYYYMM) | "202406" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/customer/1/performance/comparison?period1_start=202301&period1_end=202306&period2_start=202401&period2_end=202406" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "customer_id": 1,
  "customer_name": "서울병원",
  "period1": {
    "range": "202301~202306",
    "summary": {
      "total_sales": 15000000,
      "total_budget": 2400000,
      "total_patients": 9000,
      "average_monthly_sales": 2500000,
      "average_monthly_budget": 400000,
      "average_monthly_patients": 1500,
      "month_count": 6
    }
  },
  "period2": {
    "range": "202401~202406",
    "summary": {
      "total_sales": 18000000,
      "total_budget": 2700000,
      "total_patients": 10200,
      "average_monthly_sales": 3000000,
      "average_monthly_budget": 450000,
      "average_monthly_patients": 1700,
      "month_count": 6
    }
  },
  "comparison": {
    "sales_change": {
      "amount": 3000000,
      "rate": 20.0
    },
    "budget_change": {
      "amount": 300000,
      "rate": 12.5
    },
    "patients_change": {
      "amount": 1200,
      "rate": 13.3
    },
    "avg_monthly_sales_change": {
      "amount": 500000,
      "rate": 20.0
    },
    "avg_monthly_budget_change": {
      "amount": 50000,
      "rate": 12.5
    },
    "avg_monthly_patients_change": {
      "amount": 200,
      "rate": 13.3
    }
  }
}
```

### Comparison Fields Description

| Field | Type | Description |
|-------|------|-------------|
| comparison | object | 두 기간 비교 분석 결과 |
| comparison.sales_change | object | 매출 변화 |
| comparison.sales_change.amount | number | 매출 변화량 (원) |
| comparison.sales_change.rate | number | 매출 변화율 (%) |
| comparison.budget_change | object | 예산 변화 |
| comparison.budget_change.amount | number | 예산 변화량 (원) |
| comparison.budget_change.rate | number | 예산 변화율 (%) |
| comparison.patients_change | object | 환자수 변화 |
| comparison.patients_change.amount | number | 환자수 변화량 (명) |
| comparison.patients_change.rate | number | 환자수 변화율 (%) |
| comparison.avg_monthly_*_change | object | 월평균 변화 (sales/budget/patients) |

### 변화율 계산 방식
```
변화율 = ((period2_value - period1_value) / period1_value) * 100
```
- 양수(+): 증가
- 음수(-): 감소
- 0: 변화 없음

---

## 4. 거래처 목록 조회

모든 거래처의 기본 정보를 목록으로 조회합니다.

### Endpoint
```
GET /customers
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| skip | integer | No | 건너뛸 항목 수 (페이지네이션) | 0 |
| limit | integer | No | 조회할 최대 항목 수 (기본값: 100) | 50 |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/customers?skip=0&limit=50" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
[
  {
    "customer_id": 1,
    "customer_name": "서울병원",
    "customer_grade": "A",
    "address": "서울시 강남구 테헤란로 123",
    "doctor_name": "김철수",
    "contact_number": "02-1234-5678",
    "notes": "VIP 고객",
    "created_at": "2024-01-15T09:30:00"
  },
  {
    "customer_id": 2,
    "customer_name": "부산의원",
    "customer_grade": "B",
    "address": "부산시 해운대구 마린시티 456",
    "doctor_name": "이영희",
    "contact_number": "051-9876-5432",
    "notes": null,
    "created_at": "2024-01-20T14:20:00"
  },
  {
    "customer_id": 3,
    "customer_name": "대구약국",
    "customer_grade": "C",
    "address": "대구시 중구 동성로 789",
    "doctor_name": "박민수",
    "contact_number": "053-1111-2222",
    "notes": "소규모 거래처",
    "created_at": "2024-02-01T11:00:00"
  }
]
```

### Notes
- 삭제된 거래처(`is_deleted=true`)는 목록에서 제외됩니다
- 기본적으로 최대 100개까지 조회되며, 더 많은 데이터가 필요한 경우 페이지네이션을 사용하세요

---

## 5. 거래처명으로 검색

거래처명을 기준으로 거래처 정보와 ID를 검색합니다.

### Endpoint
```
GET /customer/search
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| name | string | Yes | 검색할 거래처명 (부분 일치) | "서울" |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/customer/search?name=서울" \
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
      "customer_id": 1,
      "customer_name": "서울병원",
      "customer_grade": "A",
      "address": "서울시 강남구 테헤란로 123"
    },
    {
      "customer_id": 15,
      "customer_name": "서울대학교병원",
      "customer_grade": "VIP",
      "address": "서울시 종로구 대학로 101"
    }
  ]
}
```

#### No Results Found (200 OK)
```json
{
  "search_term": "제주",
  "count": 0,
  "results": []
}
```

### Notes
- 검색은 대소문자를 구분하지 않습니다
- 부분 일치 검색을 지원합니다 (예: "서울"로 검색 시 "서울병원", "서울대학교병원" 모두 검색)
- 삭제된 거래처는 검색 결과에서 제외됩니다

---

## 6. 거래처 상세 정보 조회

특정 거래처의 모든 상세 정보를 조회합니다.

### Endpoint
```
GET /customer/{customer_id}
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| customer_id | integer | Yes | 거래처 고유 ID (Path Parameter) | 1 |

### Request Example
```bash
curl -X GET "https://your-domain.com/api/customer/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response

#### Success Response (200 OK)
```json
{
  "customer_id": 1,
  "customer_name": "서울병원",
  "customer_grade": "A",
  "address": "서울시 강남구 테헤란로 123",
  "doctor_name": "김철수",
  "contact_number": "02-1234-5678",
  "notes": "VIP 고객, 월말 정산",
  "created_at": "2024-01-15T09:30:00"
}
```

#### Error Response (404 Not Found)
```json
{
  "detail": "거래처 ID 999를 찾을 수 없습니다."
}
```

### Response Fields Description

| Field | Type | Description |
|-------|------|-------------|
| customer_id | integer | 거래처 고유 ID |
| customer_name | string | 거래처명 (병원/약국명) |
| customer_grade | string | 거래처 등급 (A, B, C, VIP 등) |
| address | string | 거래처 주소 |
| doctor_name | string | 담당 의사/약사명 |
| contact_number | string | 연락처 |
| notes | string | 메모 및 특이사항 |
| created_at | datetime | 거래처 등록 일시 |

---

## 사용 예제

### Python
```python
import requests

# 기본 설정
BASE_URL = "https://your-domain.com/api"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

# 1. 거래처 목록 조회
response = requests.get(
    f"{BASE_URL}/customers",
    params={"skip": 0, "limit": 10},
    headers=headers
)
if response.status_code == 200:
    customers = response.json()
    for customer in customers:
        print(f"ID: {customer['customer_id']}, 이름: {customer['customer_name']}, 등급: {customer['customer_grade']}")

# 2. 거래처명으로 검색
response = requests.get(
    f"{BASE_URL}/customer/search",
    params={"name": "서울"},
    headers=headers
)
if response.status_code == 200:
    result = response.json()
    print(f"'{result['search_term']}' 검색 결과: {result['count']}개")
    for customer in result['results']:
        print(f"  - {customer['customer_name']} (ID: {customer['customer_id']})")

# 3. 거래처 상세 정보 조회
response = requests.get(
    f"{BASE_URL}/customer/1",
    headers=headers
)
if response.status_code == 200:
    customer = response.json()
    print(f"거래처명: {customer['customer_name']}")
    print(f"주소: {customer['address']}")
    print(f"연락처: {customer['contact_number']}")

# 4. 단일 거래처 연간 실적 조회
response = requests.get(
    f"{BASE_URL}/customer/1/performance",
    params={
        "start_month": "202401",
        "end_month": "202412"
    },
    headers=headers
)
if response.status_code == 200:
    data = response.json()
    print(f"거래처: {data['customer_name']}")
    print(f"연간 총 매출: {data['summary']['total_sales']:,}원")
    print(f"월 평균 매출: {data['summary']['average_monthly_sales']:,}원")

# 5. 여러 거래처 동시 조회
response = requests.get(
    f"{BASE_URL}/customers/performance",
    params={
        "customer_ids": "1,2,3",
        "start_month": "202401",
        "end_month": "202412"
    },
    headers=headers
)
if response.status_code == 200:
    customers = response.json()
    for customer in customers:
        print(f"{customer['customer_name']}: {customer['summary']['total_sales']:,}원")

# 6. 전년 동기 대비 성장률 분석
response = requests.get(
    f"{BASE_URL}/customer/1/performance/comparison",
    params={
        "period1_start": "202301",
        "period1_end": "202312",
        "period2_start": "202401",
        "period2_end": "202412"
    },
    headers=headers
)
if response.status_code == 200:
    data = response.json()
    print(f"매출 성장률: {data['comparison']['sales_change']['rate']:.1f}%")
    print(f"환자수 증감: {data['comparison']['patients_change']['amount']:,}명")
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');

const BASE_URL = 'https://your-domain.com/api';
const headers = { 
    'Authorization': 'Bearer YOUR_JWT_TOKEN' 
};

// 1. 거래처 목록 조회
async function getCustomerList(skip = 0, limit = 10) {
    try {
        const response = await axios.get(`${BASE_URL}/customers`, {
            params: { skip, limit },
            headers
        });
        
        const customers = response.data;
        customers.forEach(customer => {
            console.log(`${customer.customer_id}: ${customer.customer_name} (${customer.customer_grade}급)`);
        });
        return customers;
    } catch (error) {
        console.error('Error:', error.response?.data?.detail || error.message);
    }
}

// 2. 거래처명으로 검색
async function searchCustomerByName(name) {
    try {
        const response = await axios.get(`${BASE_URL}/customer/search`, {
            params: { name },
            headers
        });
        
        const result = response.data;
        console.log(`'${result.search_term}' 검색 결과: ${result.count}개`);
        return result.results;
    } catch (error) {
        console.error('Error:', error.response?.data?.detail || error.message);
    }
}

// 3. 단일 거래처 성과 조회
async function getCustomerPerformance(customerId, startMonth, endMonth) {
    try {
        const response = await axios.get(
            `${BASE_URL}/customer/${customerId}/performance`,
            {
                params: {
                    start_month: startMonth,
                    end_month: endMonth
                },
                headers
            }
        );
        
        const data = response.data;
        console.log(`거래처: ${data.customer_name}`);
        console.log(`연간 총 매출: ${data.summary.total_sales.toLocaleString()}원`);
        
        // 월별 데이터 차트용 데이터 준비
        const chartData = data.monthly_data.map(month => ({
            month: month.month,
            sales: month['매출'],
            patients: month['총환자수']
        }));
        
        return chartData;
    } catch (error) {
        console.error('Error:', error.response?.data?.detail || error.message);
    }
}

// 사용 예
getCustomerList(0, 20);  // 처음 20개 거래처 목록
searchCustomerByName('서울');  // '서울' 포함된 거래처 검색
getCustomerPerformance(1, '202401', '202412');  // 거래처 성과 조회
```

---

## 주의사항

1. **날짜 형식**: 모든 월 파라미터는 반드시 `YYYYMM` 형식을 사용해야 합니다 (예: 202401)

2. **인증**: 모든 API 호출에는 유효한 JWT 토큰이 필요합니다

3. **데이터 지연**: `customer_monthly_performance_mv` Materialized View는 주기적으로 갱신되므로, 최신 데이터가 즉시 반영되지 않을 수 있습니다

4. **성능 고려사항**:
   - 대량의 거래처를 동시 조회할 때는 배치 API (`/customers/performance`)를 사용하세요
   - 긴 기간 조회 시 응답 시간이 길어질 수 있습니다

5. **에러 처리**: 
   - 네트워크 오류나 서버 오류에 대한 재시도 로직을 구현하세요
   - 404 에러는 거래처가 존재하지 않거나 삭제된 경우입니다

6. **데이터 해석**:
   - 월별 데이터가 없는 월은 결과에서 제외됩니다
   - 환자수는 `customer_monthly_patients` 테이블의 데이터를 우선 사용하며, 없을 경우 추정값이 사용될 수 있습니다

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.2 | 2025-01-13 | 거래처 목록, 검색, 상세 정보 API 추가 |
| 1.1 | 2025-01-12 | 성과 평가 로직 제거, 순수 데이터만 제공 |
| 1.0 | 2025-01-01 | 초기 버전 배포 |

---

## 문의

API 관련 문의사항은 다음으로 연락주세요:
- 이메일: api-support@your-domain.com
- 개발자 포털: https://developers.your-domain.com