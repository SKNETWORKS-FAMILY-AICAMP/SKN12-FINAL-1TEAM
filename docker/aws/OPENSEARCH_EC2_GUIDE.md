# OpenSearch EC2 배포 가이드

## 📋 목차
1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [EC2 인스턴스 생성](#ec2-인스턴스-생성)
4. [OpenSearch 설치](#opensearch-설치)
5. [환경 설정](#환경-설정)
6. [모니터링 및 관리](#모니터링-및-관리)
7. [트러블슈팅](#트러블슈팅)
8. [비용 정보](#비용-정보)

---

## 개요

이 가이드는 AWS EC2에 OpenSearch를 배포하는 과정을 설명합니다. ECS/Fargate 대신 EC2를 선택한 이유는:
- OpenSearch는 메모리 집약적 애플리케이션으로 Fargate보다 EC2가 더 적합
- 비용 효율적 (t3.medium: ~$30/월)
- 더 안정적이고 예측 가능한 성능

## 사전 준비

### 필요한 도구
- AWS CLI 설치 및 설정 완료
- SSH 클라이언트 (Windows: Git Bash 또는 PuTTY)

### IAM 권한
- EC2FullAccess
- 또는 최소 권한:
  - ec2:RunInstances
  - ec2:CreateKeyPair
  - ec2:CreateSecurityGroup
  - ec2:AuthorizeSecurityGroupIngress

## EC2 인스턴스 생성

### 1. 키페어 생성

```bash
# 키페어 생성
aws ec2 create-key-pair \
    --key-name opensearch-key \
    --region ap-northeast-2 \
    --query 'KeyMaterial' \
    --output text > opensearch-key.pem

# 권한 설정 (Linux/Mac/Git Bash)
chmod 400 opensearch-key.pem
```

### 2. 보안 그룹 생성

```bash
# 보안 그룹 생성
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name opensearch-ec2-sg \
    --description "Security group for OpenSearch EC2" \
    --region ap-northeast-2 \
    --query 'GroupId' \
    --output text)

# 필요한 포트 열기
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --ip-permissions \
        IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0}]' \
        IpProtocol=tcp,FromPort=9200,ToPort=9200,IpRanges='[{CidrIp=0.0.0.0/0}]' \
        IpProtocol=tcp,FromPort=9600,ToPort=9600,IpRanges='[{CidrIp=0.0.0.0/0}]' \
    --region ap-northeast-2
```

### 3. EC2 인스턴스 시작

```bash
# 최신 Amazon Linux 2 AMI ID 확인
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
    --region ap-northeast-2 \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

# EC2 인스턴스 생성
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t3.medium \
    --key-name opensearch-key \
    --security-groups opensearch-ec2-sg \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=opensearch-server}]' \
    --region ap-northeast-2 \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance ID: $INSTANCE_ID"

# 인스턴스 시작 대기
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region ap-northeast-2

# 공개 IP 확인
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region ap-northeast-2 \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "OpenSearch Server IP: $PUBLIC_IP"
```

## OpenSearch 설치

### SSH 접속 및 Docker 설치

```bash
# SSH 접속
ssh -i opensearch-key.pem ec2-user@$PUBLIC_IP

# Docker 설치
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# 재접속 필요 (docker 그룹 적용)
exit
ssh -i opensearch-key.pem ec2-user@$PUBLIC_IP
```

### OpenSearch 컨테이너 실행

```bash
# OpenSearch 실행 (보안 플러그인 비활성화)
docker run -d \
    --name opensearch \
    -p 9200:9200 \
    -p 9600:9600 \
    -e "discovery.type=single-node" \
    -e "DISABLE_SECURITY_PLUGIN=true" \
    -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
    --restart unless-stopped \
    opensearchproject/opensearch:2.13.0

# 상태 확인
docker ps
docker logs opensearch

# OpenSearch 접속 테스트
curl -X GET "localhost:9200"
```

### 자동 배포 스크립트

`deploy-opensearch-ec2.sh` 스크립트를 사용하면 위 과정을 자동화할 수 있습니다:

```bash
cd docker/aws
chmod +x deploy-opensearch-ec2.sh
./deploy-opensearch-ec2.sh ap-northeast-2 opensearch-key t3.medium
```

## 환경 설정

### 1. .env.aws 파일 업데이트

```bash
# OpenSearch EC2 서버의 공개 IP로 변경
OPENSEARCH_HOST=54.180.116.251  # 실제 EC2 공개 IP
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_INITIAL_ADMIN_PASSWORD=YourPassword
```

### 2. Parameter Store 업데이트

```bash
cd docker/aws
./setup-parameter-store.sh
```

### 3. ECS 서비스 재배포

```bash
aws ecs update-service \
    --cluster database-api-cluster \
    --service database-api-service \
    --force-new-deployment \
    --region ap-northeast-2
```

## 모니터링 및 관리

### 상태 확인

```bash
# OpenSearch 상태
curl http://$PUBLIC_IP:9200

# 클러스터 상태
curl http://$PUBLIC_IP:9200/_cluster/health

# 노드 정보
curl http://$PUBLIC_IP:9200/_nodes
```

### Docker 컨테이너 관리

```bash
# SSH 접속
ssh -i opensearch-key.pem ec2-user@$PUBLIC_IP

# 컨테이너 상태
docker ps

# 로그 확인
docker logs opensearch --tail 100 -f

# 컨테이너 재시작
docker restart opensearch

# 컨테이너 중지/시작
docker stop opensearch
docker start opensearch
```

### EC2 인스턴스 관리

```bash
# 인스턴스 중지 (비용 절감)
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region ap-northeast-2

# 인스턴스 시작
aws ec2 start-instances --instance-ids $INSTANCE_ID --region ap-northeast-2

# 인스턴스 재부팅
aws ec2 reboot-instances --instance-ids $INSTANCE_ID --region ap-northeast-2
```

## 트러블슈팅

### 1. OpenSearch가 시작되지 않는 경우

**문제**: 보안 플러그인 관련 오류
```
ERROR: setting [plugins.security.disabled] already set
```

**해결**: 환경 변수 중복 제거
```bash
docker stop opensearch && docker rm opensearch
docker run -d \
    --name opensearch \
    -p 9200:9200 \
    -p 9600:9600 \
    -e "discovery.type=single-node" \
    -e "DISABLE_SECURITY_PLUGIN=true" \
    -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
    --restart unless-stopped \
    opensearchproject/opensearch:2.13.0
```

### 2. 메모리 부족

**문제**: OutOfMemoryError

**해결**: Java 힙 메모리 조정
```bash
# t3.medium (4GB RAM)의 경우
-e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g"
```

### 3. 포트 접속 불가

**문제**: 외부에서 9200 포트 접속 불가

**해결**: 보안 그룹 확인
```bash
# 보안 그룹 규칙 확인
aws ec2 describe-security-groups \
    --group-names opensearch-ec2-sg \
    --region ap-northeast-2
```

### 4. EC2 인스턴스 IP 변경

EC2를 중지/시작하면 공개 IP가 변경됩니다.

**해결**: Elastic IP 할당 (선택사항)
```bash
# Elastic IP 할당
ALLOCATION_ID=$(aws ec2 allocate-address --region ap-northeast-2 --query 'AllocationId' --output text)

# EC2에 연결
aws ec2 associate-address \
    --instance-id $INSTANCE_ID \
    --allocation-id $ALLOCATION_ID \
    --region ap-northeast-2
```

## 비용 정보

### 예상 월 비용
- **EC2 t3.medium**: ~$30/월 (온디맨드)
- **EBS 스토리지 (8GB)**: ~$1/월
- **데이터 전송**: 사용량에 따라 변동

### 비용 절감 방법

1. **Reserved Instance**: 1년 약정 시 ~40% 할인
2. **Spot Instance**: ~70% 할인 (중단 가능성 있음)
3. **사용하지 않을 때 중지**: 
   ```bash
   aws ec2 stop-instances --instance-ids $INSTANCE_ID --region ap-northeast-2
   ```
4. **더 작은 인스턴스 타입**: t3.small (~$15/월) - 테스트 환경용

## 보안 강화 (선택사항)

### 1. IP 화이트리스트

```bash
# 특정 IP만 허용
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 9200 \
    --cidr YOUR_IP/32
```

### 2. OpenSearch 보안 플러그인 활성화

```bash
docker run -d \
    --name opensearch \
    -p 9200:9200 \
    -e "discovery.type=single-node" \
    -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=StrongPassword123!" \
    opensearchproject/opensearch:2.13.0
```

### 3. HTTPS 설정

TLS/SSL 인증서를 설정하여 HTTPS 통신 활성화

## 백업 및 복구

### 스냅샷 생성

```bash
# EC2 인스턴스 스냅샷
aws ec2 create-snapshot \
    --volume-id $(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' --output text) \
    --description "OpenSearch backup" \
    --region ap-northeast-2
```

### Docker 볼륨 백업

```bash
# SSH 접속 후
docker run --rm -v opensearch:/data -v $(pwd):/backup alpine tar czf /backup/opensearch-backup.tar.gz /data
```

## 정리

EC2 및 관련 리소스 삭제:

```bash
# EC2 인스턴스 종료
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region ap-northeast-2

# 보안 그룹 삭제 (인스턴스 종료 후)
aws ec2 delete-security-group --group-id $SECURITY_GROUP_ID --region ap-northeast-2

# 키페어 삭제
aws ec2 delete-key-pair --key-name opensearch-key --region ap-northeast-2
rm -f opensearch-key.pem
```

---

## 요약

EC2에 OpenSearch를 배포하는 것은 Fargate보다 더 안정적이고 비용 효율적입니다. 
주요 장점:
- ✅ 안정적인 성능
- ✅ 비용 효율적 (~$30/월)
- ✅ SSH 접속으로 직접 관리 가능
- ✅ Docker 컨테이너로 쉬운 업그레이드

주의사항:
- ⚠️ EC2 중지/시작 시 IP 변경 (Elastic IP로 해결 가능)
- ⚠️ 수동 관리 필요 (자동 스케일링 없음)
- ⚠️ 보안 설정 중요