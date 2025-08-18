# Schedule Router API 명세서

## 개요
직원 일정 관리 시스템의 API입니다. 일정 생성, 조회, 수정, 삭제 및 관리 기능을 제공합니다.

## 기본 정보
- **Base URL**: `/schedules`
- **인증**: JWT 토큰 기반 (Bearer Token)
- **Content-Type**: `application/json`

## 데이터 모델

### Schedule Type (일정 유형)
```
VISIT = "방문"
MEETING = "회의"
EDUCATION = "교육"
OTHER = "기타"
```

### Schedule Status (일정 상태)
```
SCHEDULED = "예정"
IN_PROGRESS = "진행중"
COMPLETED = "완료"
CANCELLED = "취소"
```

### ScheduleResponse
```json
{
  "schedule_id": 1,
  "employee_id": 100,
  "title": "삼성병원 방문",
  "location": "서울시 강남구",
  "contact_person": "김담당",
  "schedule_date": "2024-12-20",
  "schedule_time": "14:00:00",
  "schedule_type": "방문",
  "status": "예정",
  "notes": "신약 설명회",
  "created_at": "2024-12-15T10:00:00",
  "updated_at": "2024-12-15T10:00:00"
}
```

### ScheduleWithEmployee
```json
{
  "schedule_id": 1,
  "employee_id": 100,
  "employee_name": "홍길동",
  "title": "삼성병원 방문",
  "location": "서울시 강남구",
  "contact_person": "김담당",
  "schedule_date": "2024-12-20",
  "schedule_time": "14:00:00",
  "schedule_type": "방문",
  "status": "예정",
  "notes": "신약 설명회",
  "created_at": "2024-12-15T10:00:00",
  "updated_at": "2024-12-15T10:00:00"
}
```

## API 엔드포인트

### 1. 일정 목록 조회
**GET** `/schedules`

#### 설명
일정 목록을 조회합니다. 다양한 필터링 옵션을 제공합니다.

#### 쿼리 파라미터
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|--------|
| employee_id | integer | N | 특정 직원의 일정만 조회 | - |
| schedule_date | date | N | 특정 날짜의 일정 (YYYY-MM-DD) | - |
| start_date | date | N | 검색 시작 날짜 | - |
| end_date | date | N | 검색 종료 날짜 | - |
| schedule_type | string | N | 일정 유형 (방문/회의/교육/기타) | - |
| status | string | N | 일정 상태 (예정/진행중/완료/취소) | - |
| skip | integer | N | 페이지네이션 오프셋 | 0 |
| limit | integer | N | 페이지 크기 | 100 |

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 응답
```json
[
  {
    "schedule_id": 1,
    "employee_id": 100,
    "employee_name": "홍길동",
    "title": "삼성병원 방문",
    "location": "서울시 강남구",
    "contact_person": "김담당",
    "schedule_date": "2024-12-20",
    "schedule_time": "14:00:00",
    "schedule_type": "방문",
    "status": "예정",
    "notes": "신약 설명회",
    "created_at": "2024-12-15T10:00:00",
    "updated_at": "2024-12-15T10:00:00"
  }
]
```

#### 사용 예시
```bash
# 특정 직원의 일정 조회
curl -X GET "http://localhost:8010/schedules?employee_id=100" \
  -H "Authorization: Bearer <access_token>"

# 날짜 범위로 조회
curl -X GET "http://localhost:8010/schedules?start_date=2024-12-01&end_date=2024-12-31" \
  -H "Authorization: Bearer <access_token>"

# 방문 일정만 조회
curl -X GET "http://localhost:8010/schedules?schedule_type=방문" \
  -H "Authorization: Bearer <access_token>"
```

---

### 2. 특정 일정 조회
**GET** `/schedules/{schedule_id}`

#### 설명
ID로 특정 일정을 조회합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_id | integer | Y | 일정 ID |

#### 응답
```json
{
  "schedule_id": 1,
  "employee_id": 100,
  "employee_name": "홍길동",
  "title": "삼성병원 방문",
  "location": "서울시 강남구",
  "contact_person": "김담당",
  "schedule_date": "2024-12-20",
  "schedule_time": "14:00:00",
  "schedule_type": "방문",
  "status": "예정",
  "notes": "신약 설명회",
  "created_at": "2024-12-15T10:00:00",
  "updated_at": "2024-12-15T10:00:00"
}
```

---

### 3. 일정 생성
**POST** `/schedules`

#### 설명
새로운 일정을 생성합니다.

#### 요청 본문
```json
{
  "employee_id": 100,
  "title": "삼성병원 방문",
  "location": "서울시 강남구",
  "contact_person": "김담당",
  "schedule_date": "2024-12-20",
  "schedule_time": "14:00:00",
  "schedule_type": "방문",
  "status": "예정",
  "notes": "신약 설명회"
}
```

#### 요청 필드
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| employee_id | integer | Y | 직원 ID |
| title | string | Y | 일정 제목 |
| location | string | N | 위치 |
| contact_person | string | N | 담당자 |
| schedule_date | date | Y | 일정 날짜 |
| schedule_time | time | N | 일정 시간 |
| schedule_type | string | Y | 일정 유형 |
| status | string | N | 일정 상태 (기본: 예정) |
| notes | string | N | 메모 |

#### 응답
```json
{
  "schedule_id": 1,
  "employee_id": 100,
  "title": "삼성병원 방문",
  "location": "서울시 강남구",
  "contact_person": "김담당",
  "schedule_date": "2024-12-20",
  "schedule_time": "14:00:00",
  "schedule_type": "방문",
  "status": "예정",
  "notes": "신약 설명회",
  "created_at": "2024-12-15T10:00:00",
  "updated_at": "2024-12-15T10:00:00"
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/schedules" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 100,
    "title": "삼성병원 방문",
    "location": "서울시 강남구",
    "schedule_date": "2024-12-20",
    "schedule_type": "방문"
  }'
```

---

### 4. 일정 수정
**PUT** `/schedules/{schedule_id}`

#### 설명
기존 일정을 수정합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_id | integer | Y | 일정 ID |

#### 요청 본문
```json
{
  "title": "삼성병원 정기 방문",
  "location": "서울시 강남구 삼성동",
  "schedule_time": "15:00:00",
  "status": "진행중",
  "notes": "신약 설명회 및 Q&A"
}
```

#### 요청 필드
모든 필드는 선택사항이며, 제공된 필드만 업데이트됩니다.

#### 응답
수정된 일정 정보를 반환합니다.

---

### 5. 일정 삭제
**DELETE** `/schedules/{schedule_id}`

#### 설명
일정을 삭제합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_id | integer | Y | 일정 ID |

#### 응답
```json
{
  "message": "일정이 삭제되었습니다",
  "schedule_id": 1
}
```

---

### 6. 일정 상태 업데이트
**PATCH** `/schedules/{schedule_id}/status`

#### 설명
일정의 상태만 빠르게 업데이트합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_id | integer | Y | 일정 ID |

#### 요청 본문
```json
{
  "status": "완료"
}
```

#### 응답
```json
{
  "schedule_id": 1,
  "status": "완료",
  "updated_at": "2024-12-20T16:00:00"
}
```

---

### 7. 오늘의 일정 조회
**GET** `/schedules/today`

#### 설명
현재 로그인한 사용자의 오늘 일정을 조회합니다.

#### 응답
```json
[
  {
    "schedule_id": 1,
    "employee_id": 100,
    "employee_name": "홍길동",
    "title": "삼성병원 방문",
    "location": "서울시 강남구",
    "contact_person": "김담당",
    "schedule_date": "2024-12-20",
    "schedule_time": "14:00:00",
    "schedule_type": "방문",
    "status": "예정",
    "notes": "신약 설명회",
    "created_at": "2024-12-15T10:00:00",
    "updated_at": "2024-12-15T10:00:00"
  }
]
```

---

### 8. 이번 주 일정 조회
**GET** `/schedules/this-week`

#### 설명
현재 로그인한 사용자의 이번 주 일정을 조회합니다.

#### 응답
오늘의 일정 조회와 동일한 형식의 배열

---

### 9. 일정 요약 조회
**GET** `/schedules/summary`

#### 설명
일정 통계 요약을 조회합니다.

#### 쿼리 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| employee_id | integer | N | 특정 직원의 통계만 조회 |
| start_date | date | N | 통계 시작 날짜 |
| end_date | date | N | 통계 종료 날짜 |

#### 응답
```json
{
  "total_schedules": 50,
  "scheduled": 20,
  "in_progress": 5,
  "completed": 20,
  "cancelled": 5,
  "by_type": {
    "방문": 25,
    "회의": 15,
    "교육": 7,
    "기타": 3
  }
}
```

---

## 에러 응답

### 400 Bad Request
```json
{
  "detail": "잘못된 일정 유형입니다: invalid_type"
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
  "detail": "이 일정을 수정할 권한이 없습니다"
}
```

### 404 Not Found
```json
{
  "detail": "일정을 찾을 수 없습니다"
}
```

### 500 Internal Server Error
```json
{
  "detail": "일정 처리 중 오류가 발생했습니다: <error_message>"
}
```

---

## 권한 및 접근 제어

### 일반 사용자 (user)
- 자신의 일정 조회 및 관리
- 오늘/이번 주 자신의 일정 조회

### 매니저 (manager)
- 자신 및 팀원들의 일정 조회
- 팀원 일정 생성 및 수정

### 관리자 (admin)
- 모든 직원의 일정 조회 및 관리
- 일정 통계 전체 조회

---

## 사용 예시

### 일정 생성 후 상태 업데이트 플로우
```bash
# 1. 일정 생성
curl -X POST "http://localhost:8010/schedules" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 100,
    "title": "A병원 방문",
    "schedule_date": "2024-12-25",
    "schedule_type": "방문"
  }'

# 2. 상태를 '진행중'으로 업데이트
curl -X PATCH "http://localhost:8010/schedules/1/status" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "진행중"}'

# 3. 상태를 '완료'로 업데이트
curl -X PATCH "http://localhost:8010/schedules/1/status" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "완료"}'
```

### 월간 일정 조회
```bash
# 2024년 12월 일정 조회
curl -X GET "http://localhost:8010/schedules?start_date=2024-12-01&end_date=2024-12-31" \
  -H "Authorization: Bearer <token>"
```

### 팀 일정 조회 (매니저)
```bash
# 팀원들의 방문 일정 조회
curl -X GET "http://localhost:8010/schedules?schedule_type=방문&status=예정" \
  -H "Authorization: Bearer <manager_token>"
```

---

## 주의사항

1. **날짜 형식**: 모든 날짜는 `YYYY-MM-DD` 형식 사용
2. **시간 형식**: 모든 시간은 `HH:MM:SS` 형식 사용
3. **일정 유형**: 정의된 enum 값만 사용 가능 (방문/회의/교육/기타)
4. **일정 상태**: 정의된 enum 값만 사용 가능 (예정/진행중/완료/취소)
5. **권한 확인**: 자신의 일정이 아닌 경우 적절한 권한 필요
6. **삭제 정책**: 삭제된 일정은 복구 불가
7. **중복 방지**: 동일 시간대에 중복 일정 생성 주의

---

## 통계 및 리포팅

### 월별 일정 현황
- 전체 일정 수
- 상태별 분포
- 유형별 분포
- 직원별 일정 수

### 실적 분석
- 완료율 (완료/전체)
- 취소율 (취소/전체)
- 평균 일정 수/일

### 활용 예시
```bash
# 이번 달 통계 조회
curl -X GET "http://localhost:8010/schedules/summary?start_date=2024-12-01&end_date=2024-12-31" \
  -H "Authorization: Bearer <token>"
```