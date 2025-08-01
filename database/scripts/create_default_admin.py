#!/usr/bin/env python3
"""
기본 관리자 계정 생성 스크립트
"""

import requests
import json
import sys

def create_default_admin():
    """기본 관리자 계정을 생성합니다."""
    
    # API 엔드포인트
    url = "http://localhost:8010/admin/init-admin"
    
    # 기본 관리자 정보
    admin_data = {
        "email": "admin@goodpharm.com",
        "username": "admin",
        "password": "admin123",
        "name": "시스템 관리자",
        "role": "admin"
    }
    
    try:
        print("기본 관리자 계정을 생성하는 중...")
        
        response = requests.post(
            url,
            json=admin_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 기본 관리자 계정이 성공적으로 생성되었습니다!")
            print(f"이메일: {result.get('email')}")
            print(f"이름: {result.get('name')}")
            print(f"역할: {result.get('role')}")
            print("\n로그인 정보:")
            print(f"이메일: admin@goodpharm.com")
            print(f"비밀번호: admin123")
            return True
        else:
            error_data = response.json()
            if "관리자 계정이 이미 존재합니다" in error_data.get("detail", ""):
                print("ℹ️ 관리자 계정이 이미 존재합니다.")
                print("로그인 정보:")
                print(f"이메일: admin@goodpharm.com")
                print(f"비밀번호: admin123")
                return True
            else:
                print(f"❌ 관리자 계정 생성 실패: {error_data.get('detail', '알 수 없는 오류')}")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_default_admin()
    sys.exit(0 if success else 1) 