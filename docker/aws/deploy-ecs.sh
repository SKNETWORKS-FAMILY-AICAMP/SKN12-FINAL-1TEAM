#!/bin/bash

# AWS ECS/Fargate 배포 스크립트
# 사용법: ./deploy-ecs.sh [AWS_ACCOUNT_ID] [REGION] [CLUSTER_NAME] [SERVICE_NAME]

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 기본값 설정
AWS_ACCOUNT_ID=${1:-"YOUR_ACCOUNT_ID"}
REGION=${2:-"ap-northeast-2"}
CLUSTER_NAME=${3:-"database-api-cluster"}
SERVICE_NAME=${4:-"database-api-service"}
TASK_FAMILY="database-fastapi-app"
REPOSITORY_NAME="database-fastapi-app"
IMAGE_TAG="latest"

echo -e "${GREEN}🚀 AWS ECS/Fargate 배포 시작...${NC}"
echo "📋 설정 정보:"
echo "  - AWS Account ID: $AWS_ACCOUNT_ID"
echo "  - Region: $REGION"
echo "  - Cluster: $CLUSTER_NAME"
echo "  - Service: $SERVICE_NAME"
echo "  - Task Family: $TASK_FAMILY"

# 1. ECR 이미지 빌드 및 푸시
echo -e "\n${YELLOW}📦 Step 1: ECR 이미지 빌드 및 푸시${NC}"
./deploy-ecr.sh $AWS_ACCOUNT_ID $REGION $REPOSITORY_NAME $IMAGE_TAG

# 2. Task Definition 업데이트
echo -e "\n${YELLOW}📝 Step 2: Task Definition 업데이트${NC}"

# Task Definition 파일에서 계정 ID 치환
sed "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-definition.json > task-definition-updated.json

# Task Definition 등록
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://task-definition-updated.json \
    --region $REGION \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "  ✅ Task Definition 등록 완료: $TASK_DEFINITION_ARN"

# 3. ECS 클러스터 확인/생성
echo -e "\n${YELLOW}🏗️ Step 3: ECS 클러스터 확인/생성${NC}"
if aws ecs describe-clusters --clusters $CLUSTER_NAME --region $REGION 2>/dev/null | grep -q "ACTIVE"; then
    echo "  ✅ 클러스터가 이미 존재합니다: $CLUSTER_NAME"
else
    echo "  📦 새 클러스터 생성 중..."
    aws ecs create-cluster \
        --cluster-name $CLUSTER_NAME \
        --region $REGION \
        --capacity-providers FARGATE FARGATE_SPOT \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
        --settings name=containerInsights,value=enabled
    echo "  ✅ 클러스터 생성 완료: $CLUSTER_NAME"
fi

# 4. ECS 서비스 확인/생성/업데이트
echo -e "\n${YELLOW}🔄 Step 4: ECS 서비스 배포${NC}"

# 서비스 존재 여부 확인
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION 2>/dev/null | grep -q "\"status\": \"ACTIVE\""; then
    echo "  🔄 기존 서비스 업데이트 중..."
    
    # 서비스 업데이트
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --region $REGION \
        --force-new-deployment \
        --desired-count 2
    
    echo "  ✅ 서비스 업데이트 완료"
else
    echo "  📦 새 서비스 생성 중..."
    
    # VPC 및 서브넷 정보 가져오기 (기본 VPC 사용)
    DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --region $REGION --query 'Vpcs[0].VpcId' --output text)
    SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DEFAULT_VPC" --region $REGION --query 'Subnets[?MapPublicIpOnLaunch==`true`].SubnetId' --output text | tr '\t' ',')
    
    # 보안 그룹 생성 (없는 경우)
    SECURITY_GROUP_NAME="database-api-fargate-sg"
    SECURITY_GROUP=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" --region $REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
    
    if [ "$SECURITY_GROUP" == "None" ] || [ -z "$SECURITY_GROUP" ]; then
        echo "  🔒 보안 그룹 생성 중..."
        SECURITY_GROUP=$(aws ec2 create-security-group \
            --group-name $SECURITY_GROUP_NAME \
            --description "Security group for Database API Fargate service" \
            --vpc-id $DEFAULT_VPC \
            --region $REGION \
            --query 'GroupId' \
            --output text)
        
        # 인바운드 규칙 추가 (8000 포트)
        aws ec2 authorize-security-group-ingress \
            --group-id $SECURITY_GROUP \
            --protocol tcp \
            --port 8000 \
            --cidr 0.0.0.0/0 \
            --region $REGION
    fi
    
    # 서비스 생성
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --desired-count 2 \
        --launch-type FARGATE \
        --region $REGION \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
        --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
        --enable-execute-command
    
    echo "  ✅ 서비스 생성 완료"
fi

# 5. 배포 상태 확인
echo -e "\n${YELLOW}📊 Step 5: 배포 상태 확인${NC}"
echo "  ⏳ 서비스 안정화 대기 중... (최대 5분)"

# 배포 완료 대기
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION 2>/dev/null || {
    echo -e "  ${YELLOW}⚠️ 서비스 안정화 대기 시간 초과. 수동으로 확인하세요.${NC}"
}

# 6. 서비스 정보 출력
echo -e "\n${GREEN}✅ 배포 완료!${NC}"
echo -e "\n📋 서비스 정보:"

# 실행 중인 태스크 정보
RUNNING_TASKS=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --region $REGION --query 'taskArns' --output json)
echo "  - 실행 중인 태스크: $(echo $RUNNING_TASKS | jq '. | length') 개"

# 태스크의 공개 IP 가져오기
if [ "$RUNNING_TASKS" != "[]" ]; then
    TASK_ARN=$(echo $RUNNING_TASKS | jq -r '.[0]')
    if [ ! -z "$TASK_ARN" ] && [ "$TASK_ARN" != "null" ]; then
        TASK_DETAILS=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $TASK_ARN --region $REGION)
        ENI_ID=$(echo $TASK_DETAILS | jq -r '.tasks[0].attachments[0].details[] | select(.name=="networkInterfaceId") | .value')
        
        if [ ! -z "$ENI_ID" ] && [ "$ENI_ID" != "null" ]; then
            PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region $REGION --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
            if [ ! -z "$PUBLIC_IP" ] && [ "$PUBLIC_IP" != "None" ]; then
                echo "  - 공개 IP: $PUBLIC_IP"
                echo "  - API URL: http://$PUBLIC_IP:8000"
                echo -e "\n${GREEN}🎉 애플리케이션에 접속하려면: http://$PUBLIC_IP:8000${NC}"
            fi
        fi
    fi
fi

# 7. 로그 확인 명령어 안내
echo -e "\n📝 로그 확인 명령어:"
echo "  aws logs tail /ecs/database-fastapi-app --follow --region $REGION"

# 8. 정리
rm -f task-definition-updated.json

echo -e "\n${GREEN}🚀 배포가 완료되었습니다!${NC}"