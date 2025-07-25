import requests
import json

# API 서버 URL
BASE_URL = "http://localhost:8000"

def test_classify_and_write():
    """분류 및 작성 API 테스트"""
    
    # 1단계: 문서 분류 테스트
    print("1단계: 문서 분류 테스트")
    print("=" * 50)
    
    classify_data = {
        "user_input": "제품설명회 시행 결과서를 작성해줘"
    }
    
    response = requests.post(f"{BASE_URL}/api/docs/classify", json=classify_data)
    print(f"분류 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        classify_result = response.json()
        print("분류 결과:")
        print(json.dumps(classify_result, indent=2, ensure_ascii=False))
        
        if classify_result["success"]:
            state = classify_result["state"]
            
            # 2단계: 문서 작성 테스트
            print("\n2단계: 문서 작성 테스트")
            print("=" * 50)
            
            write_data = {
                "state": state,
                "user_input": """
25년 7월 17일에 텐텐이란 제품의 제품설명회를 할거야, 장소는 엔코아이고 시행목적은 제품 홍보야, 설명회 주요내용은 제품의 효능과 사회적이슈와 앞으로의 방향성이야, 예산사용은 8만원이고, 메뉴는 치킨, 주류는 소주1병, 맥주 4병 마셨어, 인당금액은 2만원이야. 직원들중 참석 인원은 영업팀의 김도윤, 허한결이고, 의료 전문가는 서울아산병원 손현성, 단국대병원 손영식 이야
"""
            }
            
            response = requests.post(f"{BASE_URL}/api/docs/write", json=write_data)
            print(f"작성 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                write_result = response.json()
                print("작성 결과:")
                print(json.dumps(write_result, indent=2, ensure_ascii=False))
            else:
                print(f"작성 요청 실패: {response.text}")
        else:
            print(f"분류 실패: {classify_result['error']}")
    else:
        print(f"분류 요청 실패: {response.text}")

if __name__ == "__main__":
    test_classify_and_write()