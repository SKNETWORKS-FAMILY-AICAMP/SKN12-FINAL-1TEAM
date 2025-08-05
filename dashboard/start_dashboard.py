#!/usr/bin/env python3
"""
대시보드 시작 스크립트
필요한 환경을 확인하고 대시보드를 시작합니다.
"""

import subprocess
import sys
import requests
import time
from pathlib import Path

# API 기본 URL
API_BASE_URL = "http://localhost:8010"

def check_python_version():
    """Python 버전 확인"""
    print("🐍 Python 버전 확인...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8 이상이 필요합니다. 현재 버전: {version.major}.{version.minor}")
        return False
    print(f"✅ Python 버전 확인됨: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """의존성 확인"""
    print("📦 의존성 확인...")
    required_packages = [
        "streamlit",
        "pandas", 
        "requests",
        "plotly",
        "numpy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (설치 필요)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 다음 패키지들을 설치해주세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_api_server():
    """API 서버 연결 확인"""
    print("🔍 API 서버 연결 확인...")
    try:
        response = requests.get(f"{API_BASE_URL}/ping", timeout=5)
        if response.status_code == 200:
            print("✅ API 서버 연결 성공")
            return True
        else:
            print(f"❌ API 서버 응답 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API 서버 연결 실패: {e}")
        print("   FastAPI 서버가 실행 중인지 확인해주세요.")
        print(f"   예상 URL: {API_BASE_URL}")
        return False

def install_dependencies():
    """의존성 설치"""
    print("📦 의존성 설치 중...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 의존성 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 의존성 설치 실패: {e}")
        return False

def start_dashboard():
    """대시보드 시작"""
    print("🚀 Streamlit 대시보드 시작...")
    try:
        # Streamlit 실행
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py", "--server.port", "8501"])
    except KeyboardInterrupt:
        print("\n👋 대시보드를 종료합니다.")
    except Exception as e:
        print(f"❌ 대시보드 시작 실패: {e}")

def main():
    """메인 함수"""
    print("🚀 시스템 통합 대시보드 시작")
    print("=" * 50)
    
    # 1. Python 버전 확인
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # 2. 의존성 확인 및 설치
    if not check_dependencies():
        print("\n📦 의존성을 설치하시겠습니까? (y/n): ", end="")
        choice = input().strip().lower()
        if choice in ['y', 'yes', '예']:
            if not install_dependencies():
                sys.exit(1)
        else:
            print("❌ 의존성이 설치되지 않았습니다.")
            sys.exit(1)
    
    print()
    
    # 3. API 서버 확인
    if not check_api_server():
        print("\n❌ API 서버에 연결할 수 없습니다.")
        print("   다음 단계를 확인해주세요:")
        print("   1. Docker 컨테이너가 실행 중인지 확인")
        print("   2. FastAPI 서버가 포트 8010에서 실행 중인지 확인")
        print("   3. 네트워크 연결 상태 확인")
        sys.exit(1)
    
    print()
    print("✅ 모든 사전 조건이 충족되었습니다!")
    print("🚀 대시보드를 시작합니다...")
    print("   브라우저에서 http://localhost:8501 로 접속하세요.")
    print("   Ctrl+C로 대시보드를 종료할 수 있습니다.")
    print()
    
    # 4. 대시보드 시작
    start_dashboard()

if __name__ == "__main__":
    main() 