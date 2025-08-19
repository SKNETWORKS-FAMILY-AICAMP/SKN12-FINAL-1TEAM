# 🚀 AWS 배포 Quick Start Guide

빠르게 AWS ECR/Fargate로 배포하기 위한 가이드입니다.

## 📋 전제 조건
- AWS 계정
- AWS CLI 설치 및 설정 완료
- Docker 설치 완료
- 충분한 IAM 권한

## 🎯 10분 안에 배포하기 (외부 OpenSearch 사용)

### 1️⃣ 환경 설정 (2분)
```bash
cd docker/aws

# 환경 변수 설정
cp .env.aws.example .env.aws
# .env.aws 파일을 편집하여 실제 값 입력

# AWS 계정 ID 확인
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"
```

### 2️⃣ AWS 리소스 생성 (5분)

#### RDS PostgreSQL (미리 생성 필요)
```bash
# RDS는 생성에 10-15분 소요되므로 먼저 시작
aws rds create-db-instance \
    --db-instance-identifier database-api-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username postgres \
    --master-user-password YourPassword123! \
    --allocated-storage 20
```

#### S3 버킷
```bash
aws s3 mb s3://database-api-files-$AWS_ACCOUNT_ID
```

#### OpenSearch 설정
```bash
# 기존 OpenSearch 클러스터 사용 (외부/온프레미스)
# .env.aws 파일에 OpenSearch 서버의 외부 IP/도메인 설정 필요
# 예: OPENSEARCH_HOST=your-opensearch-server.com
#     OPENSEARCH_PORT=9200
```

### 3️⃣ 애플리케이션 배포 (3분)

```bash
# 스크립트 실행 권한 부여
chmod +x deploy-ecr.sh deploy-ecs.sh setup-parameter-store.sh

# Parameter Store 설정
./setup-parameter-store.sh

# ECR에 이미지 푸시 & ECS 배포
./deploy-ecs.sh $AWS_ACCOUNT_ID ap-northeast-2
```

### 4️⃣ 배포 확인
```bash
# 서비스 상태 확인
aws ecs describe-services \
    --cluster database-api-cluster \
    --services database-api-service \
    --query 'services[0].runningCount'

# 실행 중인 태스크의 공개 IP 확인
TASK_ARN=$(aws ecs list-tasks --cluster database-api-cluster --service-name database-api-service --query 'taskArns[0]' --output text)
ENI_ID=$(aws ecs describe-tasks --cluster database-api-cluster --tasks $TASK_ARN --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo "🎉 API URL: http://$PUBLIC_IP:8000"
echo "📚 API Docs: http://$PUBLIC_IP:8000/docs"
```

## 🧹 정리 (필요시)

```bash
# 모든 리소스 삭제
aws ecs update-service --cluster database-api-cluster --service database-api-service --desired-count 0
aws ecs delete-service --cluster database-api-cluster --service database-api-service
aws ecs delete-cluster --cluster database-api-cluster
aws ecr delete-repository --repository-name database-fastapi-app --force
aws rds delete-db-instance --db-instance-identifier database-api-db --skip-final-snapshot
aws s3 rb s3://database-api-files-$AWS_ACCOUNT_ID --force
```

## ⚠️ 주의사항

1. **비용**: 
   - RDS: ~$15/월 (db.t3.micro)
   - Fargate: ~$30/월 (2 tasks)
   - S3: ~$5/월
   - 총: ~$50/월 (OpenSearch 제외)

2. **보안**:
   - 프로덕션 환경에서는 퍼블릭 IP 대신 ALB 사용
   - 보안 그룹 규칙 최소화
   - Parameter Store 사용 권장
   - OpenSearch 서버 방화벽 설정 필수

3. **데이터베이스**:
   - RDS 생성 후 pgvector 확장 설치 필요
   - 초기 마이그레이션 실행 필요

4. **OpenSearch**:
   - 외부 OpenSearch 서버가 준비되어 있어야 함
   - Fargate에서 접근 가능한 IP/도메인 필요

## 🆘 문제 해결

### 컨테이너가 시작하지 않음
```bash
# 로그 확인
aws logs tail /ecs/database-fastapi-app --follow
```

### 데이터베이스 연결 실패
```bash
# RDS 엔드포인트 확인
aws rds describe-db-instances --db-instance-identifier database-api-db --query 'DBInstances[0].Endpoint.Address'
```

### 메모리 부족
```bash
# Task Definition에서 memory를 2048로 증가
```

## 📞 지원
- [상세 배포 가이드](./DEPLOYMENT_GUIDE.md)
- [AWS 마이그레이션 가이드](./MIGRATION_GUIDE.md)