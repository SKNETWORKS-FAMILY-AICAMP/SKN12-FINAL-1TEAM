# ===== 프로덕션 빌드 (임시 주석 처리) =====
# # Stage 1: Build stage
# FROM node:20-alpine AS builder

# # 작업 디렉토리 설정
# WORKDIR /app

# # package.json과 package-lock.json 복사
# COPY package*.json ./

# # 의존성 설치
# RUN npm ci --only=production

# # 소스 코드 복사
# COPY . .

# # React 앱 빌드
# RUN npm run build

# # Stage 2: Production stage
# FROM nginx:alpine

# # 빌드된 파일을 nginx 정적 파일 디렉토리로 복사
# COPY --from=builder /app/build /usr/share/nginx/html

# # nginx 설정 - 모든 API 요청을 backend:8000으로 프록시
# RUN echo 'server { \
#     listen 80; \
#     server_name localhost; \
#     root /usr/share/nginx/html; \
#     index index.html; \
#     \
#     location / { \
#         try_files $uri $uri/ /index.html; \
#     } \
#     \
#     # 모든 API 요청을 백엔드로 프록시 \
#     location ~ ^/(api|user|admin|documents|qa|search) { \
#         proxy_pass http://backend:8000; \
#         proxy_set_header Host $host; \
#         proxy_set_header X-Real-IP $remote_addr; \
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
#         proxy_set_header X-Forwarded-Proto $scheme; \
#     } \
# }' > /etc/nginx/conf.d/default.conf

# # 포트 노출
# EXPOSE 80

# # nginx 실행
# CMD ["nginx", "-g", "daemon off;"]

# ===== 개발 모드 (임시 설정) =====
FROM node:20-alpine

# 작업 디렉토리 설정
WORKDIR /app

# package.json 복사 및 의존성 설치
COPY package*.json ./
RUN npm install

# 포트 노출
EXPOSE 3000

# 개발 서버 실행
CMD ["npm", "start"]