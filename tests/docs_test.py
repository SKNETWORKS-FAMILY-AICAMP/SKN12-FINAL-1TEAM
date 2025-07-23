import requests
import json

def test_docs_only():
    print("🧪 docs_agent 단독 테스트")
    
    BASE_URL = 'http://localhost:8000'
    
    # 1. docs_agent API 직접 호출
    print("\n1️⃣ docs API 직접 호출 테스트")
    try:
        response = requests.post(f'{BASE_URL}/api/docs/classify',
                               json={
                                   "text": "영업 보고서를 작성해주세요",
                                   "file_type": "auto"
                               },
                               timeout=10)
        result = response.json()
        print(f"   HTTP 상태: {response.status_code}")
        print(f"   응답: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   ❌ 직접 호출 실패: {str(e)}")
    
    # 2. router를 통한 docs_agent 호출
    print("\n2️⃣ router를 통한 docs_agent 호출 테스트")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router',
                               json={'query': '영업 보고서를 작성해주세요'},
                               timeout=15)
        result = response.json()
        print(f"   HTTP 상태: {response.status_code}")
        print(f"   분류된 에이전트: {result.get('agent')}")
        print(f"   성공 여부: {result.get('success')}")
        if result.get('error'):
            print(f"   ❌ 오류: {result.get('error')}")
        if result.get('response'):
            print(f"   📄 응답: {result.get('response')[:200]}...")
    except Exception as e:
        print(f"   ❌ 라우터 호출 실패: {str(e)}")

if __name__ == "__main__":
    test_docs_only() 