# Schedule API 명세서

## 개요
직원 일정 관리를 위한 API입니다. 일정 생성, 조회, 수정, 삭제 기능을 제공합니다.

## 기본 정보
- **Base URL**: `/schedules`
- **인증**: JWT 토큰 기반 (Bearer Token)
- **Content-Type**: `application/json`

## 데이터 모델

### ScheduleType (일정 유형)
- `방문` - 거래처 방문
- `회의` - 회의
- `교육` - 교육/세미나
- `기타` - 기타

### ScheduleStatus (일정 상태)
- `예정` - 예정된 일정
- `진행중` - 진행중인 일정
- `완료` - 완료된 일정
- `취소` - 취소된 일정

## API 엔드포인트

### 1. 일정 목록 조회
**GET** `/schedules`

#### 설명
일정 목록을 조회합니다. 다양한 필터링 옵션을 제공합니다.

#### 쿼리 파라미터
| 파라미터 | 타입 | 필수 | 설명 | 예시 |
|---------|------|------|------|------|
| employee_id | integer | N | 특정 직원의 일정 조회 | 1 |
| schedule_date | date | N | 특정 날짜의 일정 | 2025-01-08 |
| start_date | date | N | 검색 시작 날짜 | 2025-01-01 |
| end_date | date | N | 검색 종료 날짜 | 2025-01-31 |
| schedule_type | string | N | 일정 유형 | 방문 |
| status | string | N | 일정 상태 | 예정 |
| skip | integer | N | 페이지네이션 오프셋 | 0 |
| limit | integer | N | 페이지 크기 | 100 |

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 응답
```json
[
  {
    "schedule_id": 1,
    "employee_id": 1,
    "title": "삼성병원 신약 설명회",
    "location": "삼성병원",
    "contact_person": "김의사",
    "schedule_date": "2025-01-08",
    "schedule_time": "14:00:00",
    "duration": "2시간",
    "schedule_type": "방문",
    "status": "예정",
    "memo": "신약 3종 프레젠테이션 준비, 샘플 지참",
    "created_at": "2025-01-07T10:00:00",
    "updated_at": null,
    "employee_name": "홍길동",
    "employee_email": "hong@example.com"
  }
]
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/schedules?schedule_date=2025-01-08&status=예정" \
  -H "Authorization: Bearer <access_token>"
```

---

### 2. 내 일정 조회
**GET** `/schedules/my`

#### 설명
로그인한 사용자의 일정만 조회합니다.

#### 쿼리 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_date | date | N | 특정 날짜의 일정 |
| start_date | date | N | 시작 날짜 |
| end_date | date | N | 종료 날짜 |
| status | string | N | 일정 상태 |

#### 응답
```json
[
  {
    "schedule_id": 2,
    "employee_id": 1,
    "title": "한독약국 정기 방문",
    "location": "한독약국",
    "contact_person": "이약사",
    "schedule_date": "2025-01-08",
    "schedule_time": "10:00:00",
    "duration": "1시간",
    "schedule_type": "방문",
    "status": "예정",
    "memo": "재고 확인 및 신규 제품 소개",
    "created_at": "2025-01-07T09:00:00",
    "updated_at": null
  }
]
```

---

### 3. 오늘 일정 조회
**GET** `/schedules/today`

#### 설명
오늘 날짜의 모든 일정을 조회합니다.

#### 응답
ScheduleWithEmployee 배열 (직원 정보 포함)

---

### 4. 이번 주 일정 조회
**GET** `/schedules/week`

#### 설명
이번 주(월요일~일요일)의 모든 일정을 조회합니다.

#### 응답
ScheduleWithEmployee 배열 (직원 정보 포함)

---

### 5. 일정 요약 통계
**GET** `/schedules/summary`

#### 설명
일정 상태별 개수 통계를 조회합니다.

#### 쿼리 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| employee_id | integer | N | 특정 직원의 통계 |
| start_date | date | N | 시작 날짜 |
| end_date | date | N | 종료 날짜 |

#### 응답
```json
{
  "total_count": 10,
  "scheduled_count": 5,
  "in_progress_count": 1,
  "completed_count": 3,
  "cancelled_count": 1
}
```

---

### 6. 특정 일정 상세 조회
**GET** `/schedules/{schedule_id}`

#### 설명
특정 일정의 상세 정보를 조회합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_id | integer | Y | 일정 ID |

#### 응답
```json
{
  "schedule_id": 1,
  "employee_id": 1,
  "title": "삼성병원 신약 설명회",
  "location": "삼성병원",
  "contact_person": "김의사",
  "schedule_date": "2025-01-08",
  "schedule_time": "14:00:00",
  "duration": "2시간",
  "schedule_type": "방문",
  "status": "예정",
  "memo": "신약 3종 프레젠테이션 준비, 샘플 지참",
  "created_at": "2025-01-07T10:00:00",
  "updated_at": null
}
```

---

### 7. 일정 생성
**POST** `/schedules`

#### 설명
새로운 일정을 생성합니다. 로그인한 사용자의 employee_id가 자동으로 설정됩니다.

#### 요청 본문
```json
{
  "title": "삼성병원 신약 설명회",
  "location": "삼성병원",
  "contact_person": "김의사",
  "schedule_date": "2025-01-08",
  "schedule_time": "14:00:00",
  "duration": "2시간",
  "schedule_type": "방문",
  "status": "예정",
  "memo": "신약 3종 프레젠테이션 준비, 샘플 지참"
}
```

#### 응답
생성된 일정 정보 (ScheduleResponse)

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/schedules" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "A병원 방문",
    "location": "A병원",
    "contact_person": "박의사",
    "schedule_date": "2025-01-10",
    "schedule_time": "10:00:00",
    "duration": "1시간",
    "schedule_type": "방문",
    "status": "예정",
    "memo": "신규 제품 소개"
  }'
```

---

### 8. 일정 수정
**PUT** `/schedules/{schedule_id}`

#### 설명
기존 일정을 수정합니다. 본인의 일정만 수정 가능합니다 (관리자 제외).

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_id | integer | Y | 수정할 일정 ID |

#### 요청 본문
```json
{
  "title": "삼성병원 정기 회의",
  "location": "삼성병원 회의실",
  "schedule_time": "15:00:00",
  "duration": "3시간",
  "memo": "분기별 실적 리뷰 포함"
}
```

#### 응답
수정된 일정 정보 (ScheduleResponse)

---

### 9. 일정 상태 변경
**PATCH** `/schedules/{schedule_id}/status`

#### 설명
일정의 상태만 변경합니다.

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
수정된 일정 정보 (ScheduleResponse)

#### 사용 예시
```bash
curl -X PATCH "http://localhost:8010/schedules/1/status" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "완료"}'
```

---

### 10. 일정 삭제
**DELETE** `/schedules/{schedule_id}`

#### 설명
일정을 삭제합니다. 본인의 일정만 삭제 가능합니다 (관리자 제외).

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| schedule_id | integer | Y | 삭제할 일정 ID |

#### 응답
```json
{
  "message": "일정 1이(가) 삭제되었습니다"
}
```

---

## 에러 코드

| HTTP 상태 코드 | 설명 |
|---------------|------|
| 200 | 성공 |
| 401 | 인증 실패 (토큰 없음 또는 만료) |
| 403 | 권한 없음 (타인의 일정 수정/삭제 시도) |
| 404 | 일정을 찾을 수 없음 |
| 422 | 잘못된 파라미터 형식 |
| 500 | 서버 내부 오류 |

---

## 주의사항

1. **인증**: 모든 엔드포인트는 JWT 토큰 인증이 필요합니다.
2. **권한**: 일정 수정/삭제는 본인의 일정만 가능합니다 (관리자 제외).
3. **날짜 형식**: 날짜는 `YYYY-MM-DD` 형식으로 입력해야 합니다.
4. **시간 형식**: 시간은 `HH:MM:SS` 형식으로 입력해야 합니다.
5. **일정 충돌**: 동일 시간대에 중복 일정 생성 시 경고가 표시되지만 생성은 허용됩니다.
6. **페이지네이션**: 기본 limit은 100개입니다.

---

## 샘플 데이터

### 일정 생성 예시
```json
{
  "title": "삼성병원 신약 설명회",
  "location": "삼성병원",
  "contact_person": "김의사",
  "schedule_date": "2025-01-08",
  "schedule_time": "14:00:00",
  "duration": "2시간",
  "schedule_type": "방문",
  "status": "예정",
  "memo": "신약 3종 프레젠테이션 준비, 샘플 지참"
}
```

```json
{
  "title": "한독약국 정기 방문",
  "location": "한독약국",
  "contact_person": "이약사",
  "schedule_date": "2025-01-08",
  "schedule_time": "10:00:00",
  "duration": "1시간",
  "schedule_type": "방문",
  "status": "예정",
  "memo": "재고 확인 및 신규 제품 소개"
}
```

```json
{
  "title": "영업팀 주간 회의",
  "location": "본사 회의실",
  "contact_person": "팀장",
  "schedule_date": "2025-01-09",
  "schedule_time": "09:00:00",
  "duration": "1시간",
  "schedule_type": "회의",
  "status": "예정",
  "memo": "주간 실적 리뷰 및 계획 공유"
}
```

```json
{
  "title": "신제품 교육",
  "location": "교육센터",
  "contact_person": "교육팀",
  "schedule_date": "2025-01-10",
  "schedule_time": "13:00:00",
  "duration": "4시간",
  "schedule_type": "교육",
  "status": "예정",
  "memo": "신제품 3종 상세 교육 및 판매 전략"
}
```