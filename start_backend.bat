@echo off
echo ========================================
echo   백엔드 서버 시작 스크립트
echo ========================================
echo.

cd backend

REM Python 환경 확인
echo Python 버전 확인:
python --version
echo.

REM 필요한 패키지 설치 확인
echo 필요한 패키지 확인 중...
pip show fastapi uvicorn langchain-openai langgraph > nul 2>&1
if %errorlevel% neq 0 (
    echo 필요한 패키지가 없습니다. 설치를 시작합니다...
    pip install fastapi uvicorn langchain-openai langgraph python-dotenv
) else (
    echo 패키지가 이미 설치되어 있습니다.
)
echo.

REM 환경 변수 확인
echo 환경 변수 확인:
if exist .env (
    echo .env 파일이 있습니다.
) else (
    echo [경고] .env 파일이 없습니다!
    echo OPENAI_API_KEY를 설정해야 합니다.
)
echo.

REM 서버 시작
echo 백엔드 서버를 시작합니다...
echo URL: http://localhost:8000
echo API 문서: http://localhost:8000/docs
echo.
echo Ctrl+C로 종료할 수 있습니다.
echo ========================================
echo.

python app/main.py