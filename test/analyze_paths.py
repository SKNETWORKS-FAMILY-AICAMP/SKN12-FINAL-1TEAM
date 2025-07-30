"""
경로 문제 분석 스크립트
"""
import sys
import os
from pathlib import Path

print("=== Python 경로 분석 ===")
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"스크립트 위치: {__file__}")
print(f"Python 실행 파일: {sys.executable}")
print(f"\nsys.path:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

# 다양한 실행 방식 테스트
print("\n=== 실행 방식별 경로 설정 방법 ===")
print("1. python backend/app/main.py")
print("   - backend/app이 최상위가 됨")
print("   - sys.path에 backend 추가 필요")
print("\n2. cd backend && python app/main.py")
print("   - app이 최상위가 됨")
print("   - sys.path에 현재 디렉토리(backend) 추가 필요")
print("\n3. python -m backend.app.main")
print("   - backend가 패키지로 인식됨")
print("   - 상대 경로 import 가능")

# 권장 방법
print("\n=== 권장 해결 방법 ===")
print("main.py에서:")
print("1. __file__ 기준으로 경로 계산")
print("2. sys.path에 필요한 경로 추가")
print("3. 절대 import 사용")