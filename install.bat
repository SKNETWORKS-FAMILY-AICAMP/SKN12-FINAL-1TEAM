@echo off
chcp 65001 > nul
title Narutalk 시스템 설치 스크립트

echo.
echo ====================================================
echo 🏥 Narutalk 의료업계 QA 챗봇 시스템 설치
echo ====================================================
echo.

REM 현재 디렉토리 확인
echo 📍 현재 디렉토리: %CD%
echo.

REM Python 버전 확인
echo 🐍 Python 버전 확인...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo    Python 3.10 이상을 설치해주세요.
    pause
    exit /b 1
)

REM Node.js 버전 확인
echo 🟢 Node.js 버전 확인...
node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js가 설치되지 않았습니다.
    echo    Node.js 18 이상을 설치해주세요.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo 📦 패키지 설치 시작
echo ====================================================
echo.

REM 가상환경 생성
if not exist ".venv" (
    echo 🔧 가상환경을 생성합니다...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ 가상환경 생성 실패
        pause
        exit /b 1
    )
)

REM 가상환경 활성화
echo 🔄 가상환경을 활성화합니다...
call .venv\Scripts\activate.bat

REM pip 업그레이드
echo 📈 pip을 업그레이드합니다...
python -m pip install --upgrade pip

REM Python 패키지 설치
echo 🐍 Python 패키지를 설치합니다...
pip install -r requirements/development.txt
if %errorlevel% neq 0 (
    echo ❌ Python 패키지 설치 실패
    echo 🔄 기본 패키지만 설치를 시도합니다...
    pip install -r requirements/base.txt
    if %errorlevel% neq 0 (
        echo ❌ 기본 패키지 설치도 실패
        pause
        exit /b 1
    )
)

REM Node.js 패키지 설치
echo 🟢 Node.js 패키지를 설치합니다...
npm install
if %errorlevel% neq 0 (
    echo ❌ Node.js 패키지 설치 실패
    pause
    exit /b 1
)

echo.
echo ====================================================
echo 🗄️ 데이터베이스 설정
echo ====================================================
echo.

REM 데이터베이스 마이그레이션
echo 🔄 데이터베이스 마이그레이션을 실행합니다...
python manage.py makemigrations
python manage.py migrate
if %errorlevel% neq 0 (
    echo ❌ 데이터베이스 마이그레이션 실패
    pause
    exit /b 1
)

REM 정적 파일 수집
echo 📁 정적 파일을 수집합니다...
python manage.py collectstatic --noinput
if %errorlevel% neq 0 (
    echo ⚠️  정적 파일 수집 실패 (무시하고 계속)
)

echo.
echo ====================================================
echo 🎉 설치 완료!
echo ====================================================
echo.
echo ✅ 모든 패키지가 성공적으로 설치되었습니다!
echo.
echo 🚀 실행 방법:
echo   1. 자동 실행: start_narutalk.bat
echo   2. PowerShell: powershell -ExecutionPolicy Bypass -File start_narutalk.ps1
echo   3. Python: python run_narutalk.py
echo.
echo 🌐 접속 주소:
echo   - 메인 웹사이트: http://localhost:3000
echo   - Django 관리자: http://localhost:8000/admin
echo   - FastAPI 문서: http://localhost:8001/docs
echo.
pause 