@echo off
chcp 65001 > nul
title Narutalk 의료업계 QA 챗봇 시스템

echo.
echo ========================================
echo 🏥 Narutalk 의료업계 QA 챗봇 시스템
echo ========================================
echo.

REM 현재 디렉토리 확인
echo 📍 현재 디렉토리: %CD%
echo.

REM 가상환경 확인
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 가상환경이 없습니다. 먼저 가상환경을 생성하세요.
    echo    python -m venv .venv
    pause
    exit /b 1
)

REM Node.js 확인
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js가 설치되지 않았습니다.
    pause
    exit /b 1
)

REM node_modules 확인 및 설치
if not exist "node_modules" (
    echo 📦 Node.js 의존성을 설치합니다...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ npm install 실패
        pause
        exit /b 1
    )
)

echo 🔄 가상환경을 활성화합니다...
call .venv\Scripts\activate.bat

echo.
echo 🌐 Django 백엔드를 시작합니다 (포트 8000)...
start "Django Backend" cmd /c ".venv\Scripts\python.exe manage.py runserver --noreload"

echo ⚡ FastAPI 검색 서비스를 시작합니다 (포트 8001)...
start "FastAPI Service" cmd /c "cd service_8001_search && ..\..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001"

echo ⚛️ React 프론트엔드를 시작합니다 (포트 5173)...
start "React Frontend" cmd /c "npx vite --host 0.0.0.0 --port 5173"

echo.
echo ========================================
echo 🎉 Narutalk 시스템이 시작되었습니다!
echo 📱 접속 URL:
echo   - 메인 웹사이트: http://localhost:5173
echo   - Django API: http://localhost:8000
echo   - FastAPI 서비스: http://localhost:8001
echo ========================================
echo.
echo 🛑 각 서비스는 별도 창에서 실행됩니다.
echo 🛑 종료하려면 각 창을 닫으세요.
echo.
pause 