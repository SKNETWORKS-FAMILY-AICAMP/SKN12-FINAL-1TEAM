# 애플리케이션 테스트 가이드

## 📚 목차
1. [테스트 환경 구성](#-테스트-환경-구성)
2. [로컬 테스트](#-로컬-테스트)
3. [API 엔드포인트 테스트](#-api-엔드포인트-테스트)
4. [프로덕션 테스트](#-프로덕션-테스트)
5. [테스트 자동화](#-테스트-자동화)
6. [성능 테스트](#-성능-테스트)
7. [트러블슈팅](#-트러블슈팅)

---

## 🔧 테스트 환경 구성

### 필요한 도구
- **Postman** 또는 **Insomnia** (API 테스트)
- **curl** (명령줄 테스트)
- **Python** (테스트 스크립트)
- **Docker Desktop** (로컬 환경)
- **JMeter** 또는 **K6** (성능 테스트)

### 테스트 도구 설치
```bash
# curl (Windows - 기본 설치됨)
curl --version

# Python requests 라이브러리
pip install requests pytest pytest-asyncio

# K6 (성능 테스트)
choco install k6  # Windows (Chocolatey)
brew install k6    # Mac
```

---

## 🏠 로컬 테스트

### 1. Docker Compose로 로컬 환경 실행
```bash
# 프로젝트 루트로 이동
cd C:\Users\user\Desktop\database_api

# Docker Compose 실행
docker-compose -f docker/docker-compose.yml up --build

# 백그라운드 실행
docker-compose -f docker/docker-compose.yml up -d
```

### 2. 로컬 서비스 확인
```bash
# 헬스체크
curl http://localhost:8010/health

# API 문서 확인 (Swagger UI)
start http://localhost:8010/docs

# ReDoc 문서
start http://localhost:8010/redoc
```

### 3. 로컬 환경 종료
```bash
docker-compose -f docker/docker-compose.yml down

# 볼륨까지 삭제
docker-compose -f docker/docker-compose.yml down -v
```

---

## 🌐 API 엔드포인트 테스트

### 기본 엔드포인트

#### 1. 헬스체크
```bash
# 로컬
curl http://localhost:8010/health

# 프로덕션 (ALB 사용 시)
curl http://your-alb-domain.amazonaws.com/health
```

#### 2. 루트 엔드포인트
```bash
curl http://localhost:8010/
```

### 주요 API 테스트

#### 1. 문서 관련 API
```bash
# 문서 목록 조회
curl -X GET http://localhost:8010/documents/

# 문서 업로드 (multipart/form-data)
curl -X POST http://localhost:8010/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "document_type=contract"

# 문서 검색
curl -X GET "http://localhost:8010/documents/search?query=test&limit=10"
```

#### 2. 사용자 인증 API
```bash
# 로그인
curl -X POST http://localhost:8010/user/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# 토큰 검증
curl -X GET http://localhost:8010/user/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 3. 하이브리드 검색 API
```bash
# 하이브리드 검색
curl -X POST http://localhost:8010/search/hybrid \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "보험 계약",
    "filters": {
      "document_type": "contract"
    },
    "limit": 10
  }'
```

#### 4. 대시보드 API
```bash
# 대시보드 통계
curl -X GET http://localhost:8010/dashboard/stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# 성능 메트릭
curl -X GET http://localhost:8010/dashboard/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 테스트 스크립트

### Python 테스트 스크립트 (test_api.py)
```python
import requests
import json
import time

# 설정
BASE_URL = "http://localhost:8010"  # 로컬
# BASE_URL = "http://your-alb-domain.amazonaws.com"  # 프로덕션

def test_health():
    """헬스체크 테스트"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_login():
    """로그인 테스트"""
    data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/user/login", json=data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful, token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_protected_endpoint(token):
    """인증이 필요한 엔드포인트 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/user/me", headers=headers)
    if response.status_code == 200:
        print(f"✅ Protected endpoint access successful")
        print(f"   User info: {response.json()}")
    else:
        print(f"❌ Protected endpoint access failed: {response.text}")

def test_search(token):
    """검색 API 테스트"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "query": "테스트",
        "limit": 5
    }
    response = requests.post(f"{BASE_URL}/search/hybrid", headers=headers, json=data)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Search successful, found {len(results.get('results', []))} results")
    else:
        print(f"❌ Search failed: {response.text}")

def test_performance():
    """성능 테스트 - 응답 시간 측정"""
    endpoints = [
        "/health",
        "/",
        "/docs"
    ]
    
    print("\n📊 Performance Test Results:")
    for endpoint in endpoints:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}")
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # ms
        
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {endpoint}: {response_time:.2f}ms (Status: {response.status_code})")

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 Starting API Tests...\n")
    
    # 1. 헬스체크
    test_health()
    
    # 2. 로그인
    token = test_login()
    
    if token:
        # 3. 인증 테스트
        test_protected_endpoint(token)
        
        # 4. 검색 테스트
        test_search(token)
    
    # 5. 성능 테스트
    test_performance()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    run_all_tests()
```

### 테스트 실행
```bash
# Python 스크립트 실행
python test_api.py

# pytest 사용
pytest test_api.py -v
```

---

## 🚀 프로덕션 테스트

### 1. ECS 서비스 상태 확인
```bash
# 서비스 상태
aws ecs describe-services \
  --cluster database-api-cluster \
  --services database-api-service \
  --region ap-northeast-2 \
  --query "services[0].{Status: status, Running: runningCount, Desired: desiredCount}"

# 태스크 헬스 상태
aws ecs list-tasks \
  --cluster database-api-cluster \
  --service-name database-api-service \
  --region ap-northeast-2
```

### 2. ALB 엔드포인트 테스트 (있는 경우)
```bash
# ALB DNS 찾기
aws elbv2 describe-load-balancers \
  --region ap-northeast-2 \
  --query "LoadBalancers[?LoadBalancerName=='database-api-alb'].DNSName"

# ALB 헬스체크
curl http://database-api-alb-xxxxx.ap-northeast-2.elb.amazonaws.com/health
```

### 3. CloudWatch 로그 확인
```bash
# 최근 에러 로그
aws logs filter-log-events \
  --log-group-name /ecs/database-fastapi-app \
  --filter-pattern "ERROR" \
  --region ap-northeast-2 \
  --query "events[-10:].message" \
  --output text

# 특정 시간대 로그
aws logs filter-log-events \
  --log-group-name /ecs/database-fastapi-app \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --region ap-northeast-2
```

---

## 🤖 테스트 자동화

### GitHub Actions CI/CD 파이프라인 (.github/workflows/test.yml)
```yaml
name: API Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements/requirements-base.txt
        pip install pytest pytest-asyncio httpx
    
    - name: Run unit tests
      run: |
        pytest tests/ -v
    
    - name: Start services
      run: |
        docker-compose -f docker/docker-compose.yml up -d
        sleep 30  # Wait for services to start
    
    - name: Run integration tests
      run: |
        python test_api.py
    
    - name: Stop services
      if: always()
      run: |
        docker-compose -f docker/docker-compose.yml down
```

---

## 📊 성능 테스트

### K6 스크립트 (load-test.js)
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 10 },  // Ramp up to 10 users
    { duration: '3m', target: 10 },  // Stay at 10 users
    { duration: '1m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.1'],    // Error rate must be below 10%
  },
};

const BASE_URL = 'http://localhost:8010';

export default function () {
  // 1. Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  sleep(1);
  
  // 2. Root endpoint
  const rootRes = http.get(`${BASE_URL}/`);
  check(rootRes, {
    'root endpoint status is 200': (r) => r.status === 200,
  });
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'summary.html': htmlReport(data),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

### 성능 테스트 실행
```bash
# K6 실행
k6 run load-test.js

# HTML 리포트 생성
k6 run --out html=report.html load-test.js

# JSON 출력
k6 run --out json=results.json load-test.js
```

---

## 🔧 Postman Collection

### Postman 환경 변수
```json
{
  "name": "Database API",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8010",
      "enabled": true
    },
    {
      "key": "token",
      "value": "",
      "enabled": true
    }
  ]
}
```

### Postman 테스트 스크립트
```javascript
// 로그인 후 토큰 저장
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.access_token);
});

// 응답 시간 체크
pm.test("Response time is less than 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

// 헬스체크 검증
pm.test("Health check passed", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql("healthy");
});
```

---

## 🐛 트러블슈팅

### 1. 연결 거부 (Connection Refused)
```bash
# Docker 컨테이너 상태 확인
docker ps

# 포트 확인
netstat -an | findstr :8010  # Windows
lsof -i :8010                 # Mac/Linux

# 방화벽 확인
# Windows Defender 방화벽에서 8010 포트 허용
```

### 2. 인증 실패 (401 Unauthorized)
```bash
# 토큰 유효성 확인
# JWT 토큰 디코드 (https://jwt.io)

# 환경변수 확인
docker exec fastapi-app env | grep JWT

# Parameter Store 값 확인 (프로덕션)
aws ssm get-parameter --name /database-api/jwt/secret-key --region ap-northeast-2
```

### 3. 느린 응답 시간
```bash
# 컨테이너 리소스 확인
docker stats fastapi-app

# 로그 확인
docker logs fastapi-app --tail 100

# CPU/메모리 증설 (docker-compose.yml)
# deploy:
#   resources:
#     limits:
#       cpus: '2'
#       memory: 4G
```

### 4. 데이터베이스 연결 실패
```bash
# PostgreSQL 상태 확인
docker exec postgres-db pg_isready

# 연결 테스트
docker exec fastapi-app python -c "
from app.services.utils.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('DB Connection OK')
"
```

---

## 📝 테스트 체크리스트

### 기본 테스트
- [ ] 헬스체크 엔드포인트 응답
- [ ] Swagger UI 접근 가능
- [ ] 데이터베이스 연결 정상
- [ ] OpenSearch 연결 정상
- [ ] S3/MinIO 연결 정상

### API 테스트
- [ ] 사용자 로그인/로그아웃
- [ ] JWT 토큰 발급 및 검증
- [ ] 문서 업로드/다운로드
- [ ] 검색 기능
- [ ] 대시보드 데이터 조회

### 성능 테스트
- [ ] 응답 시간 < 500ms
- [ ] 동시 사용자 10명 처리
- [ ] 에러율 < 1%
- [ ] 메모리 사용률 < 80%
- [ ] CPU 사용률 < 70%

### 보안 테스트
- [ ] SQL Injection 방어
- [ ] XSS 방어
- [ ] 인증 없이 보호된 엔드포인트 접근 불가
- [ ] Rate Limiting 동작

---

## 📊 모니터링 대시보드

### Grafana 대시보드 설정
```json
{
  "dashboard": {
    "title": "Database API Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## 📞 지원

테스트 중 문제 발생 시:
1. 로그 확인 (`docker logs` 또는 CloudWatch)
2. 환경변수 확인
3. 네트워크 연결 확인
4. GitHub Issues 생성

---

*최종 업데이트: 2025-08-20*