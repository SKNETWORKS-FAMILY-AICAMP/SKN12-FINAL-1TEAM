@echo off
echo 🚀 NaruTalk AI 챗봇 가상환경 활성화 중...
echo.

REM 가상환경 활성화
call .\venv\Scripts\activate.bat

echo ✅ 가상환경이 활성화되었습니다!
echo 📁 현재 경로: %CD%
echo 🐍 Python 버전 확인:
python --version
echo.

echo 📦 주요 패키지 설치 상태:
pip list | findstr /i "fastapi langgraph openai python-docx"
echo.

echo 🎯 사용 가능한 명령어:
echo   - 백엔드 실행: python .\backend\app\main.py
echo   - 전체 실행: python run_server.py
echo   - 패키지 설치: pip install -r requirements.txt
echo.

REM 배치 파일이 종료되지 않도록 cmd 실행
cmd /k 