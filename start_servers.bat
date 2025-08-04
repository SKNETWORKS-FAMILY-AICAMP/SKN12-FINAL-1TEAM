@echo off
echo ========================================
echo   전체 시스템 시작 스크립트
echo ========================================
echo.

REM 백엔드 서버 시작
echo [1/2] 백엔드 서버 시작 중...
cd backend
start cmd /k "title Backend Server - Port 8000 && python app/main.py"
echo 백엔드 서버가 포트 8000에서 시작되었습니다.
echo.

REM 2초 대기
timeout /t 2 /nobreak > nul

REM 프론트엔드 서버 시작
echo [2/2] 프론트엔드 서버 시작 중...
cd ../frontend
start cmd /k "title Frontend Server - Port 3000 && npm start"
echo 프론트엔드 서버가 포트 3000에서 시작되었습니다.
echo.

echo ========================================
echo   모든 서버가 시작되었습니다!
echo ========================================
echo.
echo 백엔드: http://localhost:8000
echo 백엔드 API 문서: http://localhost:8000/docs
echo 프론트엔드: http://localhost:3000
echo.
echo 종료하려면 각 터미널 창을 닫으세요.
echo.
pause