"""
Narutalk 실행파일(.exe) 빌드 스크립트
PyInstaller를 사용하여 run_narutalk.py를 실행파일로 변환합니다.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_pyinstaller():
    """PyInstaller 설치"""
    print("📦 PyInstaller를 설치합니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller 설치 완료")
        return True
    except subprocess.CalledProcessError:
        print("❌ PyInstaller 설치 실패")
        return False

def build_exe():
    """실행파일 빌드"""
    print("🔨 실행파일을 빌드합니다...")
    
    # 빌드 명령어
    cmd = [
        "pyinstaller",
        "--onefile",              # 단일 실행파일
        "--windowed",            # 콘솔 창 숨기기 (선택사항)
        "--name=Narutalk",       # 실행파일 이름
        "--icon=icon.ico",       # 아이콘 파일 (있을 경우)
        "--add-data=.venv;.venv", # 가상환경 포함
        "--hidden-import=uvicorn",
        "--hidden-import=django",
        "--hidden-import=subprocess",
        "run_narutalk.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ 실행파일 빌드 완료!")
        print("📁 빌드된 파일: dist/Narutalk.exe")
        return True
    except subprocess.CalledProcessError:
        print("❌ 빌드 실패")
        return False

def main():
    print("🏥 Narutalk 실행파일 빌드 도구")
    print("=" * 50)
    
    # PyInstaller 설치
    if not install_pyinstaller():
        return 1
    
    # 실행파일 빌드
    if not build_exe():
        return 1
    
    print("\n🎉 빌드가 완료되었습니다!")
    print("📋 사용법:")
    print("  1. dist/Narutalk.exe 파일을 실행")
    print("  2. 또는 명령줄에서: ./dist/Narutalk.exe")
    print("\n⚠️  주의사항:")
    print("  - 실행파일은 여전히 가상환경이 필요합니다")
    print("  - Node.js는 별도로 설치되어 있어야 합니다")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 