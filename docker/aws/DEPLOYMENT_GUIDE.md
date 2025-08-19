# AWS ECR/Fargate 배포 가이드

## 📚 목차
1. [사전 준비사항](#-사전-준비사항)
2. [AWS 인프라 구축](#-aws-인프라-구축)
3. [애플리케이션 배포](#-애플리케이션-배포)
4. [배포 후 설정](#-배포-후-설정)
5. [모니터링 및 운영](#-모니터링-및-운영)
6. [트러블슈팅](#-트러블슈팅)

---

## 🔧 사전 준비사항

### 1. AWS CLI 설치 및 설정
```bash
# AWS CLI 설치 (Windows)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# AWS CLI 설치 (Mac/Linux)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# AWS 계정 설정
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: ap-northeast-2
# Default output format: json
```

### 2. Docker 설치 확인
```bash
docker --version
docker-compose --version
```

### 3. 필요한 IAM 권한
- AmazonEC2ContainerRegistryFullAccess
- AmazonECS_FullAccess
- AmazonRDSFullAccess
- AmazonS3FullAccess
- IAMFullAccess (Role 생성용)
- ~~AmazonOpenSearchServiceFullAccess~~ (외부 OpenSearch 사용 시 불필요)

---

## 🏗️ AWS 인프라 구축

### Step 1: RDS PostgreSQL 생성

```bash
# 1. 보안 그룹 생성
aws ec2 create-security-group \
    --group-name database-api-rds-sg \
    --description "Security group for RDS PostgreSQL"

# 2. 포트 5432 열기
aws ec2 authorize-security-group-ingress \
    --group-name database-api-rds-sg \
    --protocol tcp \
    --port 5432 \
    --cidr 0.0.0.0/0

# 3. RDS 인스턴스 생성
aws rds create-db-instance \
    --db-instance-identifier database-api-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.7 \
    --master-username dbadmin \
    --master-user-password YourStrongPassword123! \
    --allocated-storage 20 \
    --storage-type gp3 \
    --backup-retention-period 7 \
    --storage-encrypted
```

✅ 생성 상태 확인
```bash
# RDS 인스턴스 상태 확인
aws rds describe-db-instances --db-instance-identifier database-api-db --query 'DBInstances[0].DBInstanceStatus'

# 생성 완료 대기 (10-15분 소요)
aws rds wait db-instance-available --db-instance-identifier database-api-db
```

⚠️ **중요**: RDS 생성 후 pgvector 확장을 활성화해야 합니다:
```sql
-- RDS 접속 후 실행
CREATE EXTENSION IF NOT EXISTS vector;
```

### Step 2: OpenSearch 설정 (EC2 배포)

**EC2에 OpenSearch 배포 (권장):**

OpenSearch는 메모리 집약적 애플리케이션으로 EC2가 더 적합합니다.
자세한 내용은 [OPENSEARCH_EC2_GUIDE.md](./OPENSEARCH_EC2_GUIDE.md)를 참조하세요.

```bash
# 빠른 배포 (deploy-opensearch-ec2.sh 사용)
cd docker/aws
chmod +x deploy-opensearch-ec2.sh
./deploy-opensearch-ec2.sh ap-northeast-2 opensearch-key t3.medium

# 배포 완료 후 .env.aws 파일에서 OPENSEARCH_HOST를 EC2 공개 IP로 업데이트
```

**기존 OpenSearch를 사용하는 경우:**
1. Docker Compose로 실행 중인 OpenSearch
2. 온프레미스 서버의 OpenSearch
3. AWS OpenSearch Service (비용이 높음, ~$50-100/월)

### Step 3: S3 버킷 생성

```bash
# S3 버킷 생성
aws s3 mb s3://database-api-files --region ap-northeast-2

# 버전 관리 활성화
aws s3api put-bucket-versioning \
    --bucket database-api-files \
    --versioning-configuration Status=Enabled

# 암호화 설정
aws s3api put-bucket-encryption \
    --bucket database-api-files \
    --server-side-encryption-configuration '{
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
    }'
```

### Step 4: IAM 역할 생성

```bash
# ECS Task Execution Role 생성
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# 정책 연결
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Parameter Store 접근 권한 추가 (중요!)
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess

# ECS Task Role 생성 (애플리케이션용)
aws iam create-role \
    --role-name ecsTaskRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'
```

---

## 🚀 애플리케이션 배포

### Step 1: 환경 변수 설정

```bash
# 1. 환경 변수 파일 복사
cd docker/aws
cp .env.aws.example .env.aws

# 2. .env.aws 파일 편집
# 실제 AWS 리소스 정보로 업데이트
# OpenSearch는 외부 서버의 IP/도메인 입력

# 3. Parameter Store 설정
chmod +x setup-parameter-store.sh
./setup-parameter-store.sh

# Windows 환경에서 실행 시 주의사항:
# - Git Bash 사용 권장
# - 특수문자가 포함된 값은 따옴표로 감싸기
```

### Step 2: ECR에 이미지 푸시

```bash
# ECR 배포 스크립트 실행
chmod +x deploy-ecr.sh
./deploy-ecr.sh YOUR_ACCOUNT_ID ap-northeast-2

# 또는 수동으로 실행
# 1. ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
    docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com

# 2. 이미지 빌드 (프로덕션용)
docker build -f ../database-fastapi-app-production.Dockerfile -t database-fastapi-app:latest ../..

# 3. 태그 설정
docker tag database-fastapi-app:latest \
    YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/database-fastapi-app:latest

# 4. 푸시
docker push YOUR_ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/database-fastapi-app:latest
```

### Step 3: ECS/Fargate 배포

```bash
# Task Definition 수정 (YOUR_ACCOUNT_ID 치환)
sed -i "s/YOUR_ACCOUNT_ID/실제계정ID/g" task-definition.json

# ECS 배포 스크립트 실행
chmod +x deploy-ecs.sh
./deploy-ecs.sh YOUR_ACCOUNT_ID ap-northeast-2

# 배포 상태 확인
aws ecs describe-services \
    --cluster database-api-cluster \
    --services database-api-service \
    --region ap-northeast-2
```

---

## ⚙️ 배포 후 설정

### 1. 데이터베이스 마이그레이션

```bash
# ECS 태스크에서 직접 실행
aws ecs execute-command \
    --cluster database-api-cluster \
    --task TASK_ARN \
    --container database-fastapi-app \
    --interactive \
    --command "alembic upgrade head"
```

### 2. 벡터 데이터베이스 초기화

```bash
# 벡터 DB 초기화
aws ecs execute-command \
    --cluster database-api-cluster \
    --task TASK_ARN \
    --container database-fastapi-app \
    --interactive \
    --command "python /app/app/scripts/init_vector_db.py"
```

### 3. Application Load Balancer 설정 (선택사항)

```bash
# ALB 생성
aws elbv2 create-load-balancer \
    --name database-api-alb \
    --subnets subnet-xxx subnet-yyy \
    --security-groups sg-xxx

# 타겟 그룹 생성
aws elbv2 create-target-group \
    --name database-api-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxx \
    --target-type ip \
    --health-check-path /health
```

### 4. 도메인 연결 (선택사항)

```bash
# Route 53에서 A 레코드 생성
# ALB DNS 이름을 도메인에 연결
```

---

## 📊 모니터링 및 운영

### CloudWatch 로그 확인

```bash
# 실시간 로그 확인
aws logs tail /ecs/database-fastapi-app --follow --region ap-northeast-2

# 특정 시간 범위 로그 조회
aws logs filter-log-events \
    --log-group-name /ecs/database-fastapi-app \
    --start-time 1234567890000 \
    --end-time 1234567899999
```

### ECS 서비스 스케일링

```bash
# 태스크 수 조정
aws ecs update-service \
    --cluster database-api-cluster \
    --service database-api-service \
    --desired-count 3
```

### Auto Scaling 설정

```bash
# Auto Scaling 타겟 등록
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/database-api-cluster/database-api-service \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 1 \
    --max-capacity 10

# CPU 기반 스케일링 정책
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/database-api-cluster/database-api-service \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name cpu-scaling-policy \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        }
    }'
```

---

## 🔧 트러블슈팅

### 1. 컨테이너가 시작되지 않는 경우

```bash
# 태스크 상태 확인
aws ecs describe-tasks \
    --cluster database-api-cluster \
    --tasks TASK_ARN \
    --region ap-northeast-2

# 중지 이유 확인
aws ecs describe-tasks \
    --cluster database-api-cluster \
    --tasks TASK_ARN \
    --query 'tasks[0].stoppedReason' \
    --region ap-northeast-2
```

**일반적인 원인:**
- Parameter Store 값 누락: 모든 환경 변수가 Parameter Store에 있는지 확인
- IAM 권한 부족: ecsTaskExecutionRole에 AmazonSSMReadOnlyAccess 정책 추가
- 로그 그룹 없음: CloudWatch 로그 그룹 생성 필요

### 2. 데이터베이스 연결 실패

- RDS 보안 그룹 확인
- VPC 설정 확인
- 환경 변수 확인

### 3. 메모리 부족

```bash
# Task Definition 메모리 증가
# memory: "1024" → "2048"
# cpu: "512" → "1024"
```

### 4. 권한 오류

- IAM 역할 정책 확인
- Parameter Store 접근 권한 확인

### 5. Windows 환경 특이사항

**CloudWatch 로그 확인 시 오류:**
```bash
# Windows Git Bash에서 경로 문제 발생 시
# PowerShell 사용 또는 따옴표로 경로 감싸기
aws logs tail "/ecs/database-fastapi-app" --region ap-northeast-2
```

**Parameter Store 설정 실패:**
```bash
# Windows에서는 PowerShell 사용
powershell -Command "aws ssm put-parameter --name '/database-api/param-name' --value 'value' --type 'String' --region ap-northeast-2"
```

---

## 💰 비용 최적화

### 1. Fargate Spot 사용

```json
{
  "capacityProviderStrategy": [
    {
      "capacityProvider": "FARGATE_SPOT",
      "weight": 4
    },
    {
      "capacityProvider": "FARGATE",
      "weight": 1
    }
  ]
}
```

### 2. Reserved Instance 구매

- RDS Reserved Instance: 1년 약정 시 ~40% 할인
- EC2 Reserved Instance (OpenSearch용): 1년 약정 시 ~40% 할인

### 3. S3 수명 주기 정책

```bash
aws s3api put-bucket-lifecycle-configuration \
    --bucket database-api-files \
    --lifecycle-configuration '{
        "Rules": [{
            "Id": "archive-old-files",
            "Status": "Enabled",
            "Transitions": [{
                "Days": 30,
                "StorageClass": "STANDARD_IA"
            }]
        }]
    }'
```

---

## 📝 체크리스트

### 준비 단계
- [ ] AWS CLI 설치 및 설정
- [ ] Docker 설치 확인
- [ ] AWS 계정 및 IAM 권한 확인

### 인프라 구축
- [ ] IAM 역할 생성 (ecsTaskExecutionRole, ecsTaskRole)
- [ ] IAM 역할에 AmazonSSMReadOnlyAccess 정책 추가
- [ ] RDS PostgreSQL 생성
- [ ] RDS에 pgvector 확장 설치
- [ ] S3 버킷 생성
- [ ] OpenSearch EC2 배포 (또는 기존 OpenSearch 사용)

### 애플리케이션 배포
- [ ] .env.aws 파일 설정
- [ ] Parameter Store 값 설정 (setup-parameter-store.sh)
- [ ] ECR 레포지토리 생성
- [ ] Docker 이미지 빌드 및 ECR 푸시
- [ ] ECS 클러스터 생성
- [ ] Task Definition 등록
- [ ] ECS Service 생성 및 시작

### 배포 후 확인
- [ ] ECS 태스크 실행 상태 확인
- [ ] 애플리케이션 헬스체크 (/health)
- [ ] API 문서 접속 확인 (/docs)
- [ ] CloudWatch 로그 확인
- [ ] 데이터베이스 마이그레이션 (필요시)

### 선택 사항
- [ ] Auto Scaling 설정
- [ ] Application Load Balancer 설정
- [ ] 도메인 연결 (Route 53)
- [ ] 모니터링 대시보드 설정

---

## 🆘 지원

### 문제 해결 순서:

1. **ECS 태스크 상태 확인**
   ```bash
   aws ecs describe-services --cluster database-api-cluster --services database-api-service --region ap-northeast-2
   ```

2. **CloudWatch 로그 확인**
   ```bash
   # Windows: PowerShell 사용
   aws logs tail "/ecs/database-fastapi-app" --region ap-northeast-2
   ```

3. **Parameter Store 값 확인**
   ```bash
   aws ssm describe-parameters --region ap-northeast-2 --query "Parameters[?contains(Name, 'database-api')]"
   ```

4. **관련 문서 참조**
   - [OPENSEARCH_EC2_GUIDE.md](./OPENSEARCH_EC2_GUIDE.md) - OpenSearch EC2 배포
   - [QUICK_START.md](./QUICK_START.md) - 빠른 시작 가이드
   - [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - 마이그레이션 가이드

### 예상 총 비용:
- **RDS PostgreSQL (db.t3.micro)**: ~$15/월
- **EC2 OpenSearch (t3.medium)**: ~$30/월
- **ECS Fargate (2 tasks)**: ~$30/월
- **S3 및 데이터 전송**: ~$5/월
- **총**: ~$80/월