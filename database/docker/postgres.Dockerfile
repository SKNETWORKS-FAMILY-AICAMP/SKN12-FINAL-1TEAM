FROM pgvector/pgvector:pg15

# 데이터베이스 초기화를 위한 스크립트를 이미지에 포함
# 컨테이너 최초 초기화 시 /docker-entrypoint-initdb.d 내의 스크립트들이 실행됩니다.
COPY docker/init-scripts/ /docker-entrypoint-initdb.d/


