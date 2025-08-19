│ │ AWS ECR과 Fargate 배포 계획                                                                                                │ │
│ │                                                                                                                            │ │
│ │ 📊 현재 상황 분석                                                                                                          │ │
│ │                                                                                                                            │ │
│ │ - Docker Compose로 로컬에서 실행 중                                                                                        │ │
│ │ - FastAPI 앱, PostgreSQL, OpenSearch, MinIO가 컨테이너로 구성                                                              │ │
│ │ - 이미 ECR 배포 스크립트와 가이드 존재                                                                                     │ │
│ │                                                                                                                            │ │
│ │ 🏗️ 배포 아키텍처 (하이브리드 구성)                                                                                         │ │
│ │                                                                                                                            │ │
│ │ ┌────────────────────────────────────────────────────┐                                                                     │ │
│ │ │                   AWS Cloud                        │        온프레미스/기존 인프라                                        │ │
│ │ ├────────────────────────────────────────────────────┤        ┌──────────────────┐                                        │ │
│ │ │  ┌─────────────┐              ┌──────────┐        │◄───────┤   OpenSearch     │                                         │ │
│ │ │  │   AWS RDS   │              │  AWS S3  │        │        │    Cluster       │                                         │ │
│ │ │  │ (PostgreSQL)│              │ (MinIO)  │        │        │  (Docker/EC2)    │                                         │ │
│ │ │  └──────┬──────┘              └────┬─────┘        │        └──────────────────┘                                         │ │
│ │ │         │                          │              │                                                                      │ │
│ │ │  ┌──────┴──────────────────────────┴─────┐        │                                                                      │ │
│ │ │  │            AWS Fargate (ECS)          │        │                                                                      │ │
│ │ │  │         ┌─────────────────────┐       │        │                                                                      │ │
│ │ │  │         │  FastAPI Container  │       │        │                                                                      │ │
│ │ │  │         │   (from ECR Image)  │       │        │                                                                      │ │
│ │ │  │         └─────────────────────┘       │        │                                                                      │ │
│ │ │  └─────────────────────────────────────────┘      │                                                                      │ │
│ │ └────────────────────────────────────────────────────┘                                                                     │ │
│ │                                                                                                                            │ │
│ │ 📝 단계별 배포 계획                                                                                                        │ │
│ │                                                                                                                            │ │
│ │ Phase 1: AWS 인프라 준비 (1-2일)                                                                                           │ │
│ │                                                                                                                            │ │
│ │ 1.1 AWS 계정 및 권한 설정                                                                                                  │ │
│ │                                                                                                                            │ │
│ │ - IAM 사용자 생성 (ECR, ECS, RDS, S3, OpenSearch 권한)                                                                     │ │
│ │ - Access Key/Secret Key 생성                                                                                               │ │
│ │ - AWS CLI 설정: aws configure                                                                                              │ │
│ │                                                                                                                            │ │
│ │ 1.2 VPC 및 네트워크 설정                                                                                                   │ │
│ │                                                                                                                            │ │
│ │ - VPC 생성 또는 기본 VPC 사용                                                                                              │ │
│ │ - 서브넷 구성 (퍼블릭/프라이빗)                                                                                            │ │
│ │ - 보안 그룹 생성:                                                                                                          │ │
│ │   - RDS 보안 그룹 (5432 포트)                                                                                              │ │
│ │   - OpenSearch 보안 그룹 (443 포트)                                                                                        │ │
│ │   - Fargate 보안 그룹 (8000 포트)                                                                                          │ │
│ │                                                                                                                            │ │
│ │ Phase 2: 데이터 서비스 구축 (2-3일)                                                                                        │ │
│ │                                                                                                                            │ │
│ │ 2.1 RDS PostgreSQL 설정                                                                                                    │ │
│ │                                                                                                                            │ │
│ │ # RDS 인스턴스 생성 (db.t3.micro)                                                                                          │ │
│ │ # pgvector 확장 활성화 필요                                                                                                │ │
│ │ # 백업 및 스냅샷 설정                                                                                                      │ │
│ │                                                                                                                            │ │
│ │ 2.2 AWS OpenSearch Service 설정                                                                                            │ │
│ │                                                                                                                            │ │
│ │ # OpenSearch 도메인 생성 (m6g.large.search)                                                                                │ │
│ │ # 한국어 분석기 설정                                                                                                       │ │
│ │ # 인덱스 마이그레이션                                                                                                      │ │
│ │                                                                                                                            │ │
│ │ 2.3 S3 버킷 설정 (MinIO 대체)                                                                                              │ │
│ │                                                                                                                            │ │
│ │ # S3 버킷 생성                                                                                                             │ │
│ │ # 버전 관리 활성화                                                                                                         │ │
│ │ # 암호화 설정                                                                                                              │ │
│ │                                                                                                                            │ │
│ │ Phase 3: 컨테이너 이미지 준비 (1일)                                                                                        │ │
│ │                                                                                                                            │ │
│ │ 3.1 Dockerfile 최적화                                                                                                      │ │
│ │                                                                                                                            │ │
│ │ - 프로덕션용 환경 변수 설정                                                                                                │ │
│ │ - 헬스체크 확인                                                                                                            │ │
│ │ - 보안 강화                                                                                                                │ │
│ │                                                                                                                            │ │
│ │ 3.2 ECR 저장소 생성 및 이미지 푸시                                                                                         │ │
│ │                                                                                                                            │ │
│ │ # ECR 저장소 생성                                                                                                          │ │
│ │ aws ecr create-repository --repository-name database-fastapi-app                                                           │ │
│ │                                                                                                                            │ │
│ │ # 이미지 빌드 및 푸시                                                                                                      │ │
│ │ ./docker/aws/deploy-ecr.sh [AWS_ACCOUNT_ID] ap-northeast-2                                                                 │ │
│ │                                                                                                                            │ │
│ │ Phase 4: ECS/Fargate 배포 (1-2일)                                                                                          │ │
│ │                                                                                                                            │ │
│ │ 4.1 ECS 클러스터 생성                                                                                                      │ │
│ │                                                                                                                            │ │
│ │ aws ecs create-cluster --cluster-name database-api-cluster                                                                 │ │
│ │                                                                                                                            │ │
│ │ 4.2 Task Definition 생성                                                                                                   │ │
│ │                                                                                                                            │ │
│ │ - CPU: 512 (0.5 vCPU)                                                                                                      │ │
│ │ - Memory: 1024 (1GB)                                                                                                       │ │
│ │ - 환경 변수 설정 (AWS Systems Manager Parameter Store 사용 권장)                                                           │ │
│ │                                                                                                                            │ │
│ │ 4.3 ECS Service 생성                                                                                                       │ │
│ │                                                                                                                            │ │
│ │ - 원하는 태스크 수: 2 (고가용성)                                                                                           │ │
│ │ - Auto Scaling 설정                                                                                                        │ │
│ │ - Load Balancer 연결                                                                                                       │ │
│ │                                                                                                                            │ │
│ │ 4.4 Application Load Balancer 설정                                                                                         │ │
│ │                                                                                                                            │ │
│ │ - 타겟 그룹 생성                                                                                                           │ │
│ │ - 헬스체크 경로: /health                                                                                                   │ │
│ │ - SSL 인증서 적용                                                                                                          │ │
│ │                                                                                                                            │ │
│ │ Phase 5: 데이터 마이그레이션 (1-2일)                                                                                       │ │
│ │                                                                                                                            │ │
│ │ 5.1 PostgreSQL 데이터 마이그레이션                                                                                         │ │
│ │                                                                                                                            │ │
│ │ # 로컬 데이터 백업                                                                                                         │ │
│ │ pg_dump -h localhost -U postgres database_api > backup.sql                                                                 │ │
│ │                                                                                                                            │ │
│ │ # RDS로 복원                                                                                                               │ │
│ │ psql -h [RDS_ENDPOINT] -U postgres database_api < backup.sql                                                               │ │
│ │                                                                                                                            │ │
│ │ 5.2 OpenSearch 인덱스 마이그레이션                                                                                         │ │
│ │                                                                                                                            │ │
│ │ - 기존 인덱스 export                                                                                                       │ │
│ │ - AWS OpenSearch로 import                                                                                                  │ │
│ │                                                                                                                            │ │
│ │ 5.3 MinIO → S3 파일 마이그레이션                                                                                           │ │
│ │                                                                                                                            │ │
│ │ - 기존 파일 다운로드                                                                                                       │ │
│ │ - S3 버킷으로 업로드                                                                                                       │ │
│ │                                                                                                                            │ │
│ │ Phase 6: 테스트 및 검증 (1일)                                                                                              │ │
│ │                                                                                                                            │ │
│ │ 6.1 연결 테스트                                                                                                            │ │
│ │                                                                                                                            │ │
│ │ - RDS 연결 확인                                                                                                            │ │
│ │ - OpenSearch 연결 확인                                                                                                     │ │
│ │ - S3 접근 확인                                                                                                             │ │
│ │                                                                                                                            │ │
│ │ 6.2 API 테스트                                                                                                             │ │
│ │                                                                                                                            │ │
│ │ - 모든 엔드포인트 테스트                                                                                                   │ │
│ │ - 성능 테스트                                                                                                              │ │
│ │ - 부하 테스트                                                                                                              │ │
│ │                                                                                                                            │ │
│ │ Phase 7: 프로덕션 전환 (1일)                                                                                               │ │
│ │                                                                                                                            │ │
│ │ 7.1 DNS 설정                                                                                                               │ │
│ │                                                                                                                            │ │
│ │ - Route 53 또는 외부 DNS 설정                                                                                              │ │
│ │ - SSL 인증서 적용                                                                                                          │ │
│ │                                                                                                                            │ │
│ │ 7.2 모니터링 설정                                                                                                          │ │
│ │                                                                                                                            │ │
│ │ - CloudWatch 대시보드                                                                                                      │ │
│ │ - 알람 설정                                                                                                                │ │
│ │ - 로그 수집                                                                                                                │ │
│ │                                                                                                                            │ │
│ │ 💰 예상 비용 (월) - OpenSearch 제외                                                                                        │ │
│ │                                                                                                                            │ │
│ │ | 서비스            | 스펙                       | 예상 비용      |                                                        │ │
│ │ |----------------|--------------------------|------------|                                                                 │ │
│ │ | ECS Fargate    | 0.5 vCPU, 1GB Memory × 2 | $30-40     |                                                                 │ │
│ │ | RDS PostgreSQL | db.t3.micro              | $20-30     |                                                                 │ │
│ │ | S3             | 10GB 스토리지                | $5-10      |                                                             │ │
│ │ | ALB            | 기본                       | $20-25     |                                                               │ │
│ │ | 총계             |                          | $75-105/월  |                                                              │ │
│ │                                                                                                                            │ │
│ │ * OpenSearch는 기존 인프라 사용으로 추가 비용 없음                                                                         │ │
│ │                                                                                                                            │ │
│ │ 📋 필요한 작업 파일                                                                                                        │ │
│ │                                                                                                                            │ │
│ │ 1. 환경 변수 파일 (.env.aws)                                                                                               │ │
│ │   - RDS, OpenSearch, S3 연결 정보                                                                                          │ │
│ │   - JWT, OpenAI API 키                                                                                                     │ │
│ │ 2. Task Definition (task-definition.json)                                                                                  │ │
│ │   - 컨테이너 설정                                                                                                          │ │
│ │   - 환경 변수                                                                                                              │ │
│ │   - 리소스 할당                                                                                                            │ │
│ │ 3. 배포 스크립트 업데이트                                                                                                  │ │
│ │   - deploy-ecr.sh 실행 준비                                                                                                │ │
│ │   - ECS 서비스 업데이트 스크립트                                                                                           │ │
│ │                                                                                                                            │ │
│ │ ⚠️ 주의사항                                                                                                                │ │
│ │                                                                                                                            │ │
│ │ 1. 보안                                                                                                                    │ │
│ │   - 환경 변수는 Parameter Store 사용                                                                                       │ │
│ │   - 보안 그룹 최소 권한 원칙                                                                                               │ │
│ │   - VPC 엔드포인트 고려                                                                                                    │ │
│ │ 2. 비용 최적화                                                                                                             │ │
│ │   - Reserved Instance 고려                                                                                                 │ │
│ │   - Auto Scaling 적절히 설정                                                                                               │ │
│ │   - 불필요한 리소스 정리                                                                                                   │ │
│ │ 3. 데이터 백업                                                                                                             │ │
│ │   - RDS 자동 백업 설정                                                                                                     │ │
│ │   - S3 버전 관리                                                                                                           │ │
│ │   - 재해 복구 계획     