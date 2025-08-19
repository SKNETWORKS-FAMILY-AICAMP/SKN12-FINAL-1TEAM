#!/bin/bash

# AWS Systems Manager Parameter Store 설정 스크립트
# 사용법: ./setup-parameter-store.sh

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# .env.aws 파일 확인
if [ ! -f ".env.aws" ]; then
    echo -e "${RED}❌ .env.aws 파일이 없습니다!${NC}"
    echo "   .env.aws.example을 복사하여 .env.aws를 생성하세요:"
    echo "   cp .env.aws.example .env.aws"
    exit 1
fi

# .env.aws 파일 로드
source .env.aws

echo -e "${GREEN}🔐 AWS Systems Manager Parameter Store 설정 시작...${NC}"
echo "  Region: $AWS_REGION"

# Parameter 생성 함수
create_parameter() {
    local name=$1
    local value=$2
    local type=${3:-"String"}
    local description=${4:-"Database API parameter"}
    
    echo -n "  Creating $name... "
    
    # Windows Git Bash 호환성을 위해 AWS CLI를 직접 호출
    if [ -z "$value" ]; then
        echo -e "${RED}✗ (empty value)${NC}"
        return 1
    fi
    
    # Windows Git Bash에서는 PowerShell 사용
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows 환경에서는 PowerShell 사용
        if powershell -Command "aws ssm put-parameter --name '$name' --value '$value' --type '$type' --region '$AWS_REGION' --overwrite" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠ (already exists or update failed)${NC}"
        fi
    else
        # Linux/Mac 환경
        if aws ssm put-parameter \
            --name "$name" \
            --value "$value" \
            --type "$type" \
            --description "$description" \
            --region "$AWS_REGION" \
            --overwrite \
            --output text > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠ (already exists or update failed)${NC}"
        fi
    fi
}

echo -e "\n${YELLOW}📝 PostgreSQL Parameters${NC}"
create_parameter "/database-api/postgres/host" "$POSTGRES_HOST" "String" "RDS PostgreSQL endpoint"
create_parameter "/database-api/postgres/port" "$POSTGRES_PORT" "String" "PostgreSQL port"
create_parameter "/database-api/postgres/user" "$POSTGRES_USER" "String" "PostgreSQL username"
create_parameter "/database-api/postgres/password" "$POSTGRES_PASSWORD" "SecureString" "PostgreSQL password"
create_parameter "/database-api/postgres/db" "$POSTGRES_DB" "String" "PostgreSQL database name"

echo -e "\n${YELLOW}🔍 OpenSearch Parameters (External)${NC}"
create_parameter "/database-api/opensearch/external-host" "$OPENSEARCH_HOST" "String" "External OpenSearch endpoint"
create_parameter "/database-api/opensearch/external-port" "$OPENSEARCH_PORT" "String" "External OpenSearch port"
create_parameter "/database-api/opensearch/user" "$OPENSEARCH_USER" "String" "OpenSearch username"
create_parameter "/database-api/opensearch/password" "$OPENSEARCH_INITIAL_ADMIN_PASSWORD" "SecureString" "OpenSearch password"

echo -e "\n${YELLOW}📦 S3 Parameters${NC}"
create_parameter "/database-api/s3/access-key" "$AWS_S3_ACCESS_KEY_ID" "SecureString" "S3 access key"
create_parameter "/database-api/s3/secret-key" "$AWS_S3_SECRET_ACCESS_KEY" "SecureString" "S3 secret key"
create_parameter "/database-api/s3/bucket-name" "$AWS_S3_BUCKET_NAME" "String" "S3 bucket name"
create_parameter "/database-api/s3/region" "$AWS_S3_REGION" "String" "S3 region"

echo -e "\n${YELLOW}🔑 Application Parameters${NC}"
create_parameter "/database-api/jwt/secret-key" "$JWT_SECRET_KEY" "SecureString" "JWT secret key"
create_parameter "/database-api/openai/api-key" "$OPENAI_API_KEY" "SecureString" "OpenAI API key"

echo -e "\n${GREEN}✅ Parameter Store 설정 완료!${NC}"

# Parameter 목록 확인
echo -e "\n${YELLOW}📋 생성된 Parameters:${NC}"
aws ssm describe-parameters \
    --region "$AWS_REGION" \
    --query "Parameters[?contains(Name, 'database-api')].Name" \
    --output text | tr '\t' '\n' | sort

echo -e "\n${GREEN}🎉 모든 설정이 완료되었습니다!${NC}"
echo "   Task Definition에서 이 parameters를 사용할 수 있습니다."