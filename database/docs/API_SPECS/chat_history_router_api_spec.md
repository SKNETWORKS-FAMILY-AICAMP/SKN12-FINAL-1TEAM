# Chat History Router API 명세서

## 개요
채팅 세션 및 대화 기록을 관리하는 API입니다. 사용자의 채팅 세션 생성, 메시지 저장, 대화 기록 조회 등의 기능을 제공합니다.

## 기본 정보
- **Base URL**: `/api/chat-history`
- **Content-Type**: `application/json`
- **인증**: 선택(배포 환경에 따라 전역 JWT 미들웨어 사용 시 필요). 현재 라우터 코드에서는 JWT 검증을 강제하지 않습니다.

## API 엔드포인트

### 1. 메시지 저장
**POST** `/api/chat-history/save-message`

#### 헤더
```
Content-Type: application/json
# (선택) Authorization: Bearer <access_token>
```

#### 요청 본문
```json
{
  "session_id": "session_123",
  "role": "user",
  "message_text": "안녕하세요, 매출 현황을 알려주세요.",
  "employee_id": 1
}
```

#### 응답
```json
{
  "success": true,
  "message_id": "msg_456",
  "timestamp": "2024-01-01T12:00:00+00:00"
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/api/chat-history/save-message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "role": "user",
    "message_text": "안녕하세요, 매출 현황을 알려주세요.",
    "employee_id": 1
  }'
```

---

### 2. 대화 기록 조회
**POST** `/api/chat-history/get-history`

#### 헤더
```
Content-Type: application/json
# (선택) Authorization: Bearer <access_token>
```

#### 요청 본문
```json
{
  "session_id": "session_123",
  "limit": 50,
  "offset": 0
}
```

#### 응답
```json
{
  "success": true,
  "messages": [
    {
      "message_id": "msg_456",
      "timestamp": "2024-01-01T12:00:00+00:00",
      "role": "user",
      "content": "안녕하세요, 매출 현황을 알려주세요."
    }
  ],
  "count": 1
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/api/chat-history/get-history" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "limit": 50,
    "offset": 0
  }'
```

---

### 3. 세션 정보 조회
**POST** `/api/chat-history/get-session-info`

#### 헤더
```
Content-Type: application/json
# (선택) Authorization: Bearer <access_token>
```

#### 요청 본문
```json
{ "session_id": "session_123" }
```

#### 응답
```json
{
  "success": true,
  "session": {
    "session_id": "session_123",
    "session_title": "매출 현황 문의",
    "created_at": "2024-01-01T12:00:00+00:00",
    "last_activity": "2024-01-01T12:01:00+00:00",
    "message_count": 2,
    "is_archived": false,
    "archived_at": null
  }
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/api/chat-history/get-session-info" \
  -H "Content-Type: application/json" \
  -d '{ "session_id": "session_123" }'
```

---

### 4. 사용자 세션 목록 조회
**GET** `/api/chat-history/sessions/{employee_id}`

#### 헤더
```
# (선택) Authorization: Bearer <access_token>
```

#### 쿼리 파라미터
- **include_archived**: 아카이브된 세션 포함 여부 (기본값: false)
- **limit**: 조회할 세션 수 (기본값: 50)
- **offset**: 건너뛸 세션 수 (기본값: 0)

#### 응답
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "session_123",
      "session_title": "매출 현황 문의",
      "created_at": "2024-01-01T12:00:00+00:00",
      "last_activity": "2024-01-01T12:01:00+00:00",
      "message_count": 2,
      "is_archived": false,
      "archived_at": null
    }
  ],
  "count": 1,
  "total_count": 1
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/api/chat-history/sessions/1?include_archived=false&limit=50&offset=0"
```

---

### 5. 세션 제목 업데이트
**PUT** `/api/chat-history/session/{session_id}/title`

#### 헤더
```
Content-Type: application/json
# (선택) Authorization: Bearer <access_token>
```

#### 요청 본문
```json
{ "title": "업데이트된 세션 제목" }
```

#### 응답
```json
{ "success": true, "message": "Session title updated successfully" }
```

#### 사용 예시
```bash
curl -X PUT "http://localhost:8010/api/chat-history/session/session_123/title" \
  -H "Content-Type: application/json" \
  -d '{ "title": "업데이트된 세션 제목" }'
```

---

### 6. 세션 보관
**POST** `/api/chat-history/session/{session_id}/archive`

#### 헤더
```
Content-Type: application/json
# (선택) Authorization: Bearer <access_token>
```

#### 요청 본문
```json
{ "employee_id": 1 }
```

#### 응답
```json
{ "success": true, "message": "Session archived successfully" }
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/api/chat-history/session/session_123/archive" \
  -H "Content-Type: application/json" \
  -d '{ "employee_id": 1 }'
```

---

### 7. 세션 복원
**POST** `/api/chat-history/session/{session_id}/restore`

#### 헤더
```
Content-Type: application/json
# (선택) Authorization: Bearer <access_token>
```

#### 요청 본문
```json
{ "employee_id": 1 }
```

#### 응답
```json
{ "success": true, "message": "Session restored successfully" }
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/api/chat-history/session/session_123/restore" \
  -H "Content-Type: application/json" \
  -d '{ "employee_id": 1 }'
```

---

### 8. 세션 삭제
**DELETE** `/api/chat-history/session/{session_id}`

#### 헤더
```
# (선택) Authorization: Bearer <access_token>
```

#### 쿼리 파라미터
- **employee_id**: 직원 ID (필수)

#### 응답
```json
{ "success": true, "message": "Session deleted successfully" }
```

#### 사용 예시
```bash
curl -X DELETE "http://localhost:8010/api/chat-history/session/session_123?employee_id=1"
```

---

### 9. 시스템 상태 확인
**GET** `/api/chat-history/health`

#### 응답
```json
{ "status": "healthy", "service": "chat-history-api" }
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/api/chat-history/health"
```

---

## 메시지 역할 (Role)

### 사용자 메시지
- **role**: "user"
- 사용자가 입력한 메시지

### 어시스턴트 메시지
- **role**: "assistant"
- 시스템이 생성한 응답

---

## 세션 관리

### 세션 상태
- **활성**: `is_archived = false`
- **보관**: `is_archived = true`

### 세션 라이프사이클
1. **생성**: 첫 메시지 저장 시 자동 생성
2. **활성**: 메시지 주고받기
3. **보관**: 필요시 보관 처리
4. **복원**: 보관된 세션 재활성화
5. **삭제**: 완전 제거

---

## 에러 응답

### 400 Bad Request
```json
{ "detail": "Session is already archived" }
```

```json
{ "detail": "Session is not archived" }
```

### 401 Unauthorized
```json
{ "detail": "Could not validate credentials" }
```

### 404 Not Found
```json
{ "detail": "Session not found" }
```

### 500 Internal Server Error
```json
{ "detail": "메시지 저장 중 오류가 발생했습니다." }
```

---

## 주의사항

1. **메시지 순서**: `created_at` 기준으로 정렬됩니다.
2. **세션 고유성**: `session_id`는 고유해야 합니다.
3. **권한**: 현재 라우터는 인증을 강제하지 않습니다. 배포 환경에서 전역 JWT 미들웨어를 사용하는 경우 Authorization 헤더가 필요할 수 있습니다.
4. **데이터 보존**: 중요한 대화는 별도 백업 권장
5. **성능**: 대용량 메시지는 청킹 처리
6. **URL 경로**: 모든 엔드포인트는 `/api/chat-history` 접두사 사용
