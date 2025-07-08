@echo off
echo ================================
echo  🏥 Narutalk 시스템 실행 스크립트
echo ================================
echo.

echo 1. 가상환경 활성화 중...
call .venv\Scripts\activate

echo 2. Django 백엔드 실행 중...
start "Django Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python manage.py runserver"

echo 3. FastAPI 마이크로서비스 실행 중...
start "FastAPI Service" cmd /k "cd /d %~dp0\qa_chatbot_system\microservices\service_8001_search && %~dp0.venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8001"

echo.
echo ================================
echo  🚀 시스템 실행 완료!
echo ================================
echo  Django Backend: http://localhost:8000
echo  FastAPI Service: http://localhost:8001
echo  API 문서: http://localhost:8000/api/docs
echo.
echo  React 프론트엔드 실행을 위해서는:
echo  1. Node.js 설치 필요
echo  2. npm install
echo  3. npm run dev
echo ================================

pause 