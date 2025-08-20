# 📊 AWS 배포 현황 (2025-08-20)

## 🎯 Overview
FastAPI 애플리케이션이 AWS ECS/Fargate에 성공적으로 배포되어 운영 중입니다.

## 📦 현재 배포된 리소스

### 1. ECS/Fargate
- **Cluster**: `database-api-cluster`
- **Service**: `database-api-service`
- **Task Definition**: `database-fastapi-app:8`
- **현재 실행 Tasks**: 2개
- **Container**: `database-fastapi-app`
- **Docker Image**: `634531197710.dkr.ecr.ap-northeast-2.amazonaws.com/database-fastapi-app:v4`
- **CPU/Memory**: 1024 CPU units / 2048 MB
- **Network Mode**: awsvpc
- **Execute Command**: ✅ 활성화됨

### 2. RDS PostgreSQL
- **Instance ID**: `database-api-db`
- **Endpoint**: `database-api-db.c1eg2quewkk0.ap-northeast-2.rds.amazonaws.com`
- **Port**: 5432
- **Database Name**: `postgres` (기본 DB 사용 중)
- **Username**: `dbadmin`
- **Instance Class**: `db.t3.micro`
- **Storage**: 20GB (gp3)
- **Extensions**: 
  - ✅ pgvector 설치됨
- **Tables Created**: 
  - branches
  - employee_info
  - customers
  - products
  - sales_records
  - interaction_logs
  - assignment_map
  - customer_monthly_status
  - documents
  - alembic_version
  - table_descriptions

### 3. OpenSearch (EC2)
- **Type**: EC2 인스턴스에 Docker로 배포
- **EC2 Public IP**: `54.180.116.251`
- **Endpoint**: `ec2-54-180-116-251.ap-northeast-2.compute.amazonaws.com:9200`
- **Username**: `admin`
- **Instance Type**: `t3.medium`

### 4. S3
- **Bucket Name**: `database-api-files`
- **Region**: `ap-northeast-2`
- **Versioning**: Enabled
- **Encryption**: AES256

### 5. IAM Roles
- **Task Execution Role**: `ecsTaskExecutionRole`
  - AmazonECSTaskExecutionRolePolicy
  - AmazonSSMReadOnlyAccess
- **Task Role**: `ecsTaskRole`
  - AmazonSSMManagedInstanceCore
  - ECSExecuteCommandPolicy (Custom)

### 6. Parameter Store
모든 환경 변수가 Systems Manager Parameter Store에 저장됨:
```
/database-api/postgres/host
/database-api/postgres/port
/database-api/postgres/user
/database-api/postgres/password
/database-api/postgres/db (값: postgres)
/database-api/opensearch/external-host
/database-api/opensearch/external-port
/database-api/opensearch/user
/database-api/opensearch/password
/database-api/s3/access-key
/database-api/s3/secret-key
/database-api/s3/bucket-name
/database-api/s3/region
/database-api/jwt/secret-key
/database-api/openai/api-key
```

### 7. CloudWatch
- **Log Group**: `/ecs/database-fastapi-app`
- **Log Retention**: 7 days

### 8. Networking
- **VPC**: Default VPC 사용 중
- **Subnets**: 
  - subnet-081a21af830c04af7
  - subnet-0f8c75d06964b14e4
  - subnet-04f463b03237beb28
  - subnet-0e34d32e17cccb8c0
- **Security Group**: `sg-097fa8c4739022f67`
- **Public IP Assignment**: ENABLED (Task마다 동적 할당)

## ⚠️ 현재 문제점 및 개선 필요사항

### 1. **No Load Balancer**
- Task IP가 재시작마다 변경됨
- 현재 접속 방법: Task의 Public IP 직접 사용
- 문제: 배포/재시작 시 IP 변경으로 접속 불가

### 2. **No Auto Scaling**
- 고정된 Task 수 (2개)
- 트래픽 증가 시 수동 스케일링 필요

### 3. **No Domain/SSL**
- HTTP only (포트 8000)
- 도메인 없음

### 4. **No Health Check Monitoring**
- CloudWatch 로그만 확인 가능
- 알람 설정 없음

## 🚀 다음 단계 구현 필요 항목

### 1. Application Load Balancer (ALB)
```bash
# 필요한 정보
- VPC ID: (Default VPC)
- Subnets: 위 4개 서브넷
- Security Group: 새로 생성 필요 (포트 80/443 허용)
- Target Group: ECS Service 연결
- Health Check Path: /health
```

### 2. Auto Scaling
```bash
# 설정 필요 항목
- Min Tasks: 1
- Max Tasks: 10
- Target CPU: 70%
- Target Memory: 80%
- Scale-in Cooldown: 300초
- Scale-out Cooldown: 60초
```

### 3. Route 53 (Optional)
```bash
# 도메인 연결 시
- Hosted Zone 생성
- A Record → ALB DNS
- SSL 인증서 (ACM)
```

### 4. CloudWatch Alarms
```bash
# 모니터링 항목
- Task 실행 실패
- CPU/Memory 사용률
- API 응답 시간
- 5xx 에러율
```

## 📝 현재 API 접속 방법

### 1. 현재 Task IP 확인
```bash
# Task ARN 확인
aws ecs list-tasks \
  --cluster database-api-cluster \
  --service database-api-service \
  --region ap-northeast-2

# Public IP 확인
aws ecs describe-tasks \
  --cluster database-api-cluster \
  --tasks [TASK_ARN] \
  --region ap-northeast-2 \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value|[0]' \
  --output text | xargs -I {} \
aws ec2 describe-network-interfaces \
  --network-interface-ids {} \
  --region ap-northeast-2 \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text
```

### 2. API 테스트
```bash
# 예시 (IP는 변경됨)
curl http://[PUBLIC_IP]:8000/health
curl http://[PUBLIC_IP]:8000/docs
```

## 💰 현재 예상 비용
- **ECS Fargate**: ~$30/월 (2 tasks)
- **RDS PostgreSQL**: ~$15/월 (db.t3.micro)
- **EC2 OpenSearch**: ~$30/월 (t3.medium)
- **S3 & Data Transfer**: ~$5/월
- **총**: ~$80/월

## 🔧 즉시 구현 가능한 개선사항

### Priority 1: ALB 설정 (필수)
- 고정 엔드포인트 제공
- 자동 헬스체크
- 여러 Task로 트래픽 분산

### Priority 2: Auto Scaling (권장)
- 트래픽 기반 자동 스케일링
- 비용 최적화

### Priority 3: Monitoring (권장)
- CloudWatch 대시보드
- 알람 설정

## 📌 중요 정보

### AWS Account
- **Account ID**: 634531197710
- **Region**: ap-northeast-2 (Seoul)

### 주요 ARN
- **ECS Cluster**: arn:aws:ecs:ap-northeast-2:634531197710:cluster/database-api-cluster
- **ECS Service**: arn:aws:ecs:ap-northeast-2:634531197710:service/database-api-cluster/database-api-service
- **Task Definition**: arn:aws:ecs:ap-northeast-2:634531197710:task-definition/database-fastapi-app:8
- **ECR Repository**: 634531197710.dkr.ecr.ap-northeast-2.amazonaws.com/database-fastapi-app

### 환경 변수 파일
- **Local**: `docker/aws/.env.aws`
- **Parameter Store**: `/database-api/*` prefix

## 🎯 Quick Commands

### 서비스 재시작
```bash
aws ecs update-service \
  --cluster database-api-cluster \
  --service database-api-service \
  --force-new-deployment \
  --region ap-northeast-2
```

### 로그 확인
```bash
aws logs tail /ecs/database-fastapi-app \
  --follow \
  --region ap-northeast-2
```

### Task 수 조정
```bash
aws ecs update-service \
  --cluster database-api-cluster \
  --service database-api-service \
  --desired-count 3 \
  --region ap-northeast-2
```

---
*Last Updated: 2025-08-20 17:00 KST*
*Status: ✅ Running (Without ALB)*