#!/usr/bin/env python3
"""
docs_agent 상호작용 방식 사용 예시

이 파일은 새로운 상호작용 방식으로 docs_agent를 사용하는 방법을 보여줍니다.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
SESSION_ID = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def print_response(title, response_data):
    """응답을 보기 좋게 출력"""
    print(f"\n{'='*50}")
    print(f"📋 {title}")
    print('='*50)
    print(json.dumps(response_data, indent=2, ensure_ascii=False))
    print('='*50)

def test_interactive_docs():
    """상호작용 문서 작성 테스트"""
    
    print(f"🚀 docs_agent 상호작용 테스트 시작")
    print(f"📝 세션 ID: {SESSION_ID}")
    
    # 1단계: 초기 문서 분류 요청
    print(f"\n1️⃣ 단계 1: 초기 문서 분류 요청")
    initial_request = {
        "session_id": SESSION_ID,
        "user_input": "영업방문 결과보고서를 작성해주세요",
        "is_initial": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/docs/interactive",
            json=initial_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_response("초기 분류 결과", result)
            
            if result.get("stage") == "waiting_input":
                template = result.get("template", "")
                print(f"\n📝 제공된 템플릿:")
                print(f"```\n{template}\n```")
                
                # 2단계: 세션 상태 확인
                print(f"\n2️⃣ 단계 2: 세션 상태 확인")
                status_response = requests.get(f"{BASE_URL}/api/docs/status/{SESSION_ID}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print_response("세션 상태", status_data)
                
                # 3단계: 사용자 정보 입력 (문서 작성)
                print(f"\n3️⃣ 단계 3: 사용자 정보 입력")
                user_input = """
【기본 정보】
- 방문 제목: 신약 소개 및 영업 협의
- Client(고객사명): 서울대학교병원
- 담당자: 김의사
- 방문 Site: 서울대학교병원 본관
- 담당자 소속: 내과
- 연락처: 02-1234-5678
- 영업제공자: 좋은제약 김영업
- 방문자: 김영업, 이과장
- 방문자 소속: 좋은제약 영업팀

【내용】
- 고객사 개요: 국내 최대 규모 종합병원, 월 환자 수 10,000명
- 프로젝트 개요: 신약 도입 검토 프로젝트
- 방문 및 협의내용: 
  * 신약 효능 및 안전성 설명
  * 기존 약물 대비 장점 소개  
  * 도입 일정 및 조건 협의
- 향후계획 및 일정:
  * 1주 후 임상시험 자료 제공
  * 2주 후 약사위원회 검토 예정
  * 1개월 후 최종 결정
- 협조사항 및 공유사항:
  * 경쟁사 동향 모니터링 필요
  * 타 병원 도입 사례 준비
                """
                
                followup_request = {
                    "session_id": SESSION_ID,
                    "user_input": user_input.strip(),
                    "is_initial": False
                }
                
                followup_response = requests.post(
                    f"{BASE_URL}/api/docs/interactive",
                    json=followup_request,
                    timeout=30
                )
                
                if followup_response.status_code == 200:
                    final_result = followup_response.json()
                    print_response("최종 문서 작성 결과", final_result)
                    
                    if final_result.get("stage") == "completed":
                        document = final_result.get("document", {})
                        print(f"\n📄 생성된 문서:")
                        print(json.dumps(document, indent=2, ensure_ascii=False))
                        
                        # 4단계: 최종 세션 상태 확인
                        print(f"\n4️⃣ 단계 4: 최종 세션 상태 확인")
                        final_status = requests.get(f"{BASE_URL}/api/docs/status/{SESSION_ID}")
                        if final_status.status_code == 200:
                            print_response("최종 세션 상태", final_status.json())
                    else:
                        print(f"❌ 문서 작성 실패: {final_result.get('message')}")
                else:
                    print(f"❌ 후속 요청 실패: {followup_response.status_code}")
                    print(followup_response.text)
            else:
                print(f"❌ 예상과 다른 상태: {result.get('stage')}")
        else:
            print(f"❌ 초기 요청 실패: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
    
    # 5단계: 세션 리셋 (선택사항)
    print(f"\n5️⃣ 단계 5: 세션 리셋")
    try:
        reset_response = requests.post(f"{BASE_URL}/api/docs/reset/{SESSION_ID}")
        if reset_response.status_code == 200:
            print_response("세션 리셋 결과", reset_response.json())
        else:
            print(f"⚠️ 세션 리셋 실패: {reset_response.status_code}")
    except Exception as e:
        print(f"⚠️ 세션 리셋 오류: {str(e)}")

def test_error_handling():
    """오류 처리 테스트"""
    print(f"\n🧪 오류 처리 테스트")
    
    # 잘못된 세션으로 후속 입력 시도
    invalid_request = {
        "session_id": "invalid_session",
        "user_input": "잘못된 세션에서의 입력",
        "is_initial": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/docs/interactive",
            json=invalid_request,
            timeout=10
        )
        print_response("잘못된 세션 테스트", response.json())
    except Exception as e:
        print(f"❌ 오류 처리 테스트 실패: {str(e)}")

if __name__ == "__main__":
    print("📚 docs_agent 상호작용 방식 테스트")
    print("="*60)
    print("🔧 사전 조건:")
    print("  1. 백엔드 서버가 http://localhost:8000에서 실행 중이어야 합니다")
    print("  2. OPENAI_API_KEY가 설정되어 있어야 합니다")
    print("="*60)
    
    # 서버 연결 확인
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ 서버 연결 확인됨")
            
            # 메인 테스트 실행
            test_interactive_docs()
            
            # 오류 처리 테스트
            test_error_handling()
            
            print(f"\n🎉 테스트 완료!")
        else:
            print(f"❌ 서버 응답 오류: {health_response.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        print("백엔드 서버를 먼저 실행해주세요: python backend/app/main.py") 