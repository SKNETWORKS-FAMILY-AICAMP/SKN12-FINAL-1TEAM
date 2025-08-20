# 애플리케이션 수정 및 재배포 가이드

## 📚 목차
1. [개요](#-개요)
2. [사전 준비사항](#-사전-준비사항)
3. [코드 수정 및 테스트](#-코드-수정-및-테스트)
4. [Docker 이미지 빌드](#-docker-이미지-빌드)
5. [ECR 푸시](#-ecr-푸시)
6. [ECS 서비스 재배포](#-ecs-서비스-재배포)
7. [배포 확인](#-배포-확인)
8. [롤백 절차](#-롤백-절차)
9. [자동화 스크립트](#-자동화-스크립트)
10. [트러블슈팅](#-트러블슈팅)

---

## 🎯 개요

### 배포 프로세스 플로우
```
코드 수정 → 로컬 테스트 → Docker 빌드 → ECR 푸시 → Task Definition 업데이트 → ECS 재배포 → 검증
```

### 필요한 도구
- Docker Desktop
- AWS CLI
- Git
- 코드 에디터 (VS Code 등)

### 필요한 AWS 권한
- ECR 접근 권한
- ECS 업데이트 권한
- CloudWatch Logs 읽기 권한

---

## 🔧 사전 준비사항

### 1. AWS CLI 로그인 확인
```bash
# AWS 계정 확인
aws sts get-caller-identity

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 634531197710.dkr.ecr.ap-northeast-2.amazonaws.com
```

### 2. 환경변수 설정
```bash
# 프로젝트 경로로 이동
cd C:\Users\user\Desktop\database_api

# AWS 계정 ID 설정 (본인 계정으로 변경)
set AWS_ACCOUNT_ID=634531197710
set AWS_REGION=ap-northeast-2
```

---

## 💻 코드 수정 및 테스트

### 1. 코드 수정
```bash
# 브랜치 생성 (선택사항)
git checkout -b feature/your-feature-name

# 코드 수정 작업 수행
# 예: app/main.py, app/routers/*.py 등
```

### 2. 로컬 테스트 (선택사항)
```bash
# 로컬 Docker Compose로 테스트
docker-compose -f docker/docker-compose.yml up --build

# 테스트 완료 후 종료
docker-compose -f docker/docker-compose.yml down
```

### 3. 변경사항 커밋
```bash
# 변경사항 확인
git status
git diff

# 커밋
git add .
git commit -m "feat: 기능 설명"
git push origin feature/your-feature-name
```

---

## 🐳 Docker 이미지 빌드

### 1. 버전 태그 결정
```bash
# 현재 ECR에 있는 이미지 태그 확인
aws ecr describe-images --repository-name database-fastapi-app --region ap-northeast-2 --query "imageDetails[*].imageTags" --output json

# 다음 버전 결정 (예: v5, v6, ...)
set IMAGE_TAG=v5
```

### 2. Production 이미지 빌드
```bash
# Production Dockerfile로 빌드
docker build -t database-fastapi-app:%IMAGE_TAG% -f docker/database-fastapi-app-production.Dockerfile .

# 빌드 확인
docker images | findstr database-fastapi-app
```

---

## 📤 ECR 푸시

### 1. 이미지 태그 지정
```bash
# ECR 리포지토리용 태그 추가
docker tag database-fastapi-app:%IMAGE_TAG% %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/database-fastapi-app:%IMAGE_TAG%
```

### 2. ECR 푸시
```bash
# 이미지 푸시
docker push %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/database-fastapi-app:%IMAGE_TAG%

# 푸시 확인
aws ecr describe-images --repository-name database-fastapi-app --region %AWS_REGION% --query "imageDetails[?contains(imageTags, '%IMAGE_TAG%')]"
```

---

## 🚀 ECS 서비스 재배포

### 1. Task Definition 업데이트
```bash
# 현재 Task Definition 다운로드
aws ecs describe-task-definition --task-definition database-fastapi-app --region %AWS_REGION% --query taskDefinition > task-definition-new.json

# task-definition-new.json 파일 수정
# "image" 필드를 새 버전으로 변경
# 예: "image": "634531197710.dkr.ecr.ap-northeast-2.amazonaws.com/database-fastapi-app:v5"
```

### 2. 새 Task Definition 등록
```bash
# 새 Task Definition 등록
aws ecs register-task-definition --cli-input-json file://task-definition-new.json --region %AWS_REGION%

# Revision 번호 확인 (예: 8)
```

### 3. ECS 서비스 업데이트
```bash
# 서비스 업데이트 (revision 번호 변경 필요)
aws ecs update-service ^
  --cluster database-api-cluster ^
  --service database-api-service ^
  --task-definition database-fastapi-app:8 ^
  --force-new-deployment ^
  --region %AWS_REGION%
```

---

## ✅ 배포 확인

### 1. 배포 상태 모니터링
```bash
# 배포 상태 확인
aws ecs describe-services ^
  --cluster database-api-cluster ^
  --services database-api-service ^
  --region %AWS_REGION% ^
  --query "services[0].deployments[?status=='PRIMARY']"

# 실행 중인 태스크 확인
aws ecs list-tasks ^
  --cluster database-api-cluster ^
  --service-name database-api-service ^
  --desired-status RUNNING ^
  --region %AWS_REGION%
```

### 2. 헬스체크 확인
```bash
# 태스크 상태 확인
aws ecs describe-tasks ^
  --cluster database-api-cluster ^
  --tasks [TASK_ARN] ^
  --region %AWS_REGION% ^
  --query "tasks[*].{Status: lastStatus, Health: healthStatus}"
```

### 3. CloudWatch 로그 확인
```bash
# 최근 로그 확인
aws logs filter-log-events ^
  --log-group-name /ecs/database-fastapi-app ^
  --region %AWS_REGION% ^
  --query "events[-20:].message" ^
  --output text
```

---

## ⏪ 롤백 절차

### 이전 버전으로 롤백
```bash
# 이전 Task Definition revision으로 서비스 업데이트
aws ecs update-service ^
  --cluster database-api-cluster ^
  --service database-api-service ^
  --task-definition database-fastapi-app:7 ^
  --force-new-deployment ^
  --region %AWS_REGION%

# 롤백 상태 확인
aws ecs describe-services ^
  --cluster database-api-cluster ^
  --services database-api-service ^
  --region %AWS_REGION% ^
  --query "services[0].deployments"
```

---

## 🤖 자동화 스크립트

### deploy.bat (Windows)
```batch
@echo off
setlocal

:: 설정
set AWS_ACCOUNT_ID=634531197710
set AWS_REGION=ap-northeast-2
set IMAGE_TAG=%1

if "%IMAGE_TAG%"=="" (
    echo Usage: deploy.bat [IMAGE_TAG]
    echo Example: deploy.bat v5
    exit /b 1
)

echo Starting deployment with tag %IMAGE_TAG%...

:: 1. Docker 빌드
echo Building Docker image...
docker build -t database-fastapi-app:%IMAGE_TAG% -f docker/database-fastapi-app-production.Dockerfile .
if %ERRORLEVEL% neq 0 exit /b 1

:: 2. ECR 로그인
echo Logging in to ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
if %ERRORLEVEL% neq 0 exit /b 1

:: 3. 이미지 태그
echo Tagging image...
docker tag database-fastapi-app:%IMAGE_TAG% %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/database-fastapi-app:%IMAGE_TAG%
if %ERRORLEVEL% neq 0 exit /b 1

:: 4. ECR 푸시
echo Pushing to ECR...
docker push %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/database-fastapi-app:%IMAGE_TAG%
if %ERRORLEVEL% neq 0 exit /b 1

:: 5. Task Definition 업데이트
echo Updating task definition...
powershell -Command "(Get-Content docker/aws/task-definition-v2.json) -replace '\"image\": \".*\"', '\"image\": \"%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/database-fastapi-app:%IMAGE_TAG%\"' | Set-Content task-definition-temp.json"

:: 6. Task Definition 등록
echo Registering new task definition...
aws ecs register-task-definition --cli-input-json file://task-definition-temp.json --region %AWS_REGION% > task-def-output.json
if %ERRORLEVEL% neq 0 exit /b 1

:: 7. Revision 번호 추출
for /f "tokens=2 delims=:" %%a in ('findstr /c:"\"revision\":" task-def-output.json') do set REVISION=%%a
set REVISION=%REVISION:,=%
set REVISION=%REVISION: =%

echo New task definition revision: %REVISION%

:: 8. 서비스 업데이트
echo Updating ECS service...
aws ecs update-service ^
  --cluster database-api-cluster ^
  --service database-api-service ^
  --task-definition database-fastapi-app:%REVISION% ^
  --force-new-deployment ^
  --region %AWS_REGION%
if %ERRORLEVEL% neq 0 exit /b 1

:: 정리
del task-definition-temp.json
del task-def-output.json

echo Deployment completed successfully!
echo Monitoring deployment status...

:: 배포 상태 확인
timeout /t 10 /nobreak > nul
aws ecs describe-services ^
  --cluster database-api-cluster ^
  --services database-api-service ^
  --region %AWS_REGION% ^
  --query "services[0].deployments[?status=='PRIMARY'].{Status: rolloutState, Tasks: runningCount, Desired: desiredCount}" ^
  --output table

endlocal
```

### deploy.sh (Linux/Mac)
```bash
#!/bin/bash

# 설정
AWS_ACCOUNT_ID=634531197710
AWS_REGION=ap-northeast-2
IMAGE_TAG=$1

if [ -z "$IMAGE_TAG" ]; then
    echo "Usage: ./deploy.sh [IMAGE_TAG]"
    echo "Example: ./deploy.sh v5"
    exit 1
fi

echo "Starting deployment with tag $IMAGE_TAG..."

# 1. Docker 빌드
echo "Building Docker image..."
docker build -t database-fastapi-app:$IMAGE_TAG -f docker/database-fastapi-app-production.Dockerfile .
if [ $? -ne 0 ]; then exit 1; fi

# 2. ECR 로그인
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
if [ $? -ne 0 ]; then exit 1; fi

# 3. 이미지 태그
echo "Tagging image..."
docker tag database-fastapi-app:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/database-fastapi-app:$IMAGE_TAG
if [ $? -ne 0 ]; then exit 1; fi

# 4. ECR 푸시
echo "Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/database-fastapi-app:$IMAGE_TAG
if [ $? -ne 0 ]; then exit 1; fi

# 5. Task Definition 업데이트
echo "Updating task definition..."
sed "s|\"image\": \".*\"|\"image\": \"$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/database-fastapi-app:$IMAGE_TAG\"|" docker/aws/task-definition-v2.json > task-definition-temp.json

# 6. Task Definition 등록
echo "Registering new task definition..."
TASK_DEF_OUTPUT=$(aws ecs register-task-definition --cli-input-json file://task-definition-temp.json --region $AWS_REGION)
if [ $? -ne 0 ]; then exit 1; fi

# 7. Revision 번호 추출
REVISION=$(echo $TASK_DEF_OUTPUT | grep -o '"revision": [0-9]*' | grep -o '[0-9]*')
echo "New task definition revision: $REVISION"

# 8. 서비스 업데이트
echo "Updating ECS service..."
aws ecs update-service \
  --cluster database-api-cluster \
  --service database-api-service \
  --task-definition database-fastapi-app:$REVISION \
  --force-new-deployment \
  --region $AWS_REGION
if [ $? -ne 0 ]; then exit 1; fi

# 정리
rm task-definition-temp.json

echo "Deployment completed successfully!"
echo "Monitoring deployment status..."

# 배포 상태 확인
sleep 10
aws ecs describe-services \
  --cluster database-api-cluster \
  --services database-api-service \
  --region $AWS_REGION \
  --query "services[0].deployments[?status=='PRIMARY'].{Status: rolloutState, Tasks: runningCount, Desired: desiredCount}" \
  --output table
```

---

## 🔍 트러블슈팅

### 1. 이미지 푸시 실패
```bash
# ECR 로그인 재시도
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 634531197710.dkr.ecr.ap-northeast-2.amazonaws.com

# Docker 데몬 재시작
# Windows: Docker Desktop 재시작
# Linux: sudo systemctl restart docker
```

### 2. 태스크 실패
```bash
# 실패한 태스크 로그 확인
aws logs filter-log-events \
  --log-group-name /ecs/database-fastapi-app \
  --region ap-northeast-2 \
  --query "events[*].message" \
  --output text

# 태스크 중지 이유 확인
aws ecs describe-tasks \
  --cluster database-api-cluster \
  --tasks [TASK_ARN] \
  --region ap-northeast-2 \
  --query "tasks[0].stoppedReason"
```

### 3. 헬스체크 실패
```bash
# 헬스체크 엔드포인트 로그 확인
aws logs filter-log-events \
  --log-group-name /ecs/database-fastapi-app \
  --filter-pattern "/health" \
  --region ap-northeast-2 \
  --query "events[*].message" \
  --output text
```

### 4. 메모리/CPU 부족
```bash
# Task Definition에서 리소스 증가
# memory: "2048" → "4096"
# cpu: "1024" → "2048"
```

---

## 📊 모니터링

### CloudWatch 대시보드
1. AWS Console → CloudWatch → Dashboards
2. 다음 메트릭 추가:
   - ECS Service CPU Utilization
   - ECS Service Memory Utilization
   - Target Response Time
   - HTTP 4xx/5xx Errors

### 알람 설정
```bash
# CPU 사용률 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "ECS-CPU-High" \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=database-api-service Name=ClusterName,Value=database-api-cluster
```

---

## 📝 베스트 프랙티스

### 1. 버전 태그 규칙
- Production: `v1`, `v2`, `v3`, ...
- Staging: `staging-v1`, `staging-v2`, ...
- Development: `dev-latest`, `dev-YYYYMMDD`

### 2. 블루/그린 배포
- ECS는 기본적으로 롤링 업데이트 수행
- 새 태스크가 헬시 상태가 되면 이전 태스크 종료
- `minimumHealthyPercent: 100`으로 무중단 배포

### 3. 환경변수 관리
- 민감한 정보는 AWS Systems Manager Parameter Store 사용
- 환경별로 다른 파라미터 경로 사용
  - Production: `/database-api/prod/*`
  - Staging: `/database-api/staging/*`

### 4. 배포 전 체크리스트
- [ ] 로컬 테스트 완료
- [ ] 코드 리뷰 완료
- [ ] 환경변수 확인
- [ ] 데이터베이스 마이그레이션 필요 여부 확인
- [ ] 롤백 계획 수립

### 5. 배포 후 체크리스트
- [ ] 헬스체크 통과 확인
- [ ] 로그 에러 확인
- [ ] API 엔드포인트 테스트
- [ ] 성능 메트릭 확인
- [ ] 사용자 피드백 모니터링

---

## 📞 지원 및 문의

문제 발생 시:
1. CloudWatch Logs 확인
2. ECS 서비스 이벤트 확인
3. GitHub Issues 생성
4. 팀 슬랙 채널 문의

---

*최종 업데이트: 2025-08-20*