#!/bin/bash

# EC2에 OpenSearch 설치 스크립트
set -e

REGION=${1:-"ap-northeast-2"}
KEY_NAME=${2:-"your-key-pair"}  # EC2 키페어 이름
INSTANCE_TYPE=${3:-"t3.medium"}

echo "🖥️ EC2에 OpenSearch 설치 시작..."

# 1. 보안 그룹 생성
echo "🔒 보안 그룹 생성..."
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name opensearch-ec2-sg \
    --description "Security group for OpenSearch EC2" \
    --region $REGION \
    --query 'GroupId' \
    --output text)

# SSH (22), OpenSearch (9200, 9600) 포트 열기
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --ip-permissions \
        IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0}]' \
        IpProtocol=tcp,FromPort=9200,ToPort=9200,IpRanges='[{CidrIp=0.0.0.0/0}]' \
        IpProtocol=tcp,FromPort=9600,ToPort=9600,IpRanges='[{CidrIp=0.0.0.0/0}]' \
    --region $REGION

# 2. User Data 스크립트 생성 (EC2 시작 시 자동 실행)
cat > user-data.sh << 'EOF'
#!/bin/bash
# Docker 설치
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# OpenSearch 실행
docker run -d \
    --name opensearch \
    -p 9200:9200 \
    -p 9600:9600 \
    -e "discovery.type=single-node" \
    -e "plugins.security.disabled=true" \
    -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
    --restart unless-stopped \
    opensearchproject/opensearch:2.13.0

# 상태 확인
sleep 30
curl -X GET "localhost:9200"
EOF

# 3. EC2 인스턴스 시작
echo "🚀 EC2 인스턴스 시작..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c1c30571ee7c2bce \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-groups opensearch-ec2-sg \
    --user-data file://user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=opensearch-server}]' \
    --region $REGION \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "  인스턴스 ID: $INSTANCE_ID"
echo "  ⏳ 인스턴스 시작 대기 중..."

# 인스턴스가 running 상태가 될 때까지 대기
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# 4. 공개 IP 확인
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "✅ EC2 OpenSearch 서버 준비 완료!"
echo "🔍 OpenSearch URL: http://$PUBLIC_IP:9200"
echo "🖥️ SSH 접속: ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "📝 다음 단계:"
echo "1. 2-3분 후 OpenSearch가 완전히 시작됩니다"
echo "2. curl http://$PUBLIC_IP:9200 으로 확인"
echo "3. .env.aws 파일에서 OPENSEARCH_HOST=$PUBLIC_IP 로 변경"
echo "4. setup-parameter-store.sh 실행"
echo "5. database-api-service 재시작"

# 정리
rm -f user-data.sh