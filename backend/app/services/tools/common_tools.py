from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Annotated
import requests
import json
from dotenv import load_dotenv

load_dotenv()

@tool
def check_policy_violation(content: Annotated[str, "작성된 문서 본문"]) -> str:
    """작성된 문서 내용이 회사 규정을 위반하는지 LLM과 OpenSearch를 통해 검사합니다."""
    
    try:
        # 1단계: LLM을 사용해 규정 확인이 필요한 문구 추출
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """
사용자가 입력한 텍스트에서 회사 규정 확인이 필요해 보이는 문구들을 추출해주세요.

규정 확인이 필요한 내용:
- 금전적 지급, 비용 처리 관련
- 개인정보 처리 관련
- 외부 업체와의 계약이나 협력 관련
- 보안이나 기밀 정보 관련
- 의료기관이나 의료진과의 관계 관련
- 제품 홍보나 마케팅 활동 관련
- 접대나 선물 제공 관련

추출된 문구들을 JSON 리스트 형태로 반환해주세요.
예시: ["5만원 상당의 식사 제공", "개인정보 수집 및 활용", "의료진 대상 교육 세미나"]

만약 규정 확인이 필요한 문구가 없다면 빈 리스트 []를 반환해주세요.
            """),
            ("human", "{content}")
        ])
        
        response = llm.invoke(extraction_prompt.format_messages(content=content))
        extracted_text = response.content.strip()
        
        print(f"📋 LLM 문구 추출 결과: {extracted_text}")
        
        # JSON 파싱
        try:
            if extracted_text.startswith('[') and extracted_text.endswith(']'):
                policy_phrases = json.loads(extracted_text)
            else:
                # JSON 형태가 아닌 경우 빈 리스트로 처리
                policy_phrases = []
        except json.JSONDecodeError:
            print("⚠️ JSON 파싱 실패, 빈 리스트로 처리")
            policy_phrases = []
        
        if not policy_phrases:
            print("✅ 규정 확인이 필요한 문구가 발견되지 않았습니다.")
            return "OK"
        
        print(f"🔍 추출된 규정 확인 대상 문구: {policy_phrases}")
        
        # 2단계: FastAPI를 통해 각 문구별로 유사한 규정 정보 검색
        violations = []
        fastapi_url = "http://localhost:8010/qa/question"
        
        for phrase in policy_phrases:
            try:
                # FastAPI 호출 - 올바른 페이로드 형식 사용
                payload = {
                    "question": phrase,
                    "top_k": 5,
                    "include_summary": True,
                    "include_sources": True
                }
                
                response = requests.post(
                    fastapi_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    api_result = response.json()
                    if api_result.get('success', False):
                        search_results = api_result.get('search_results', [])
                        print(f"📊 '{phrase}' 검색 결과: {len(search_results)}개")
                        
                        # 3단계: LLM을 사용해 추출된 규정 정보와 비교하여 위반 여부 판단
                        violation_result = _check_phrase_against_regulations(phrase, search_results, llm)
                        if violation_result != "OK":
                            violations.append(f"{phrase}: {violation_result}")
                    else:
                        print(f"⚠️ API 응답 실패 ({phrase}): {api_result}")
                        violations.append(f"{phrase}: API 응답 오류")
                        
                else:
                    print(f"⚠️ FastAPI 호출 실패 ({phrase}): {response.status_code}")
                    violations.append(f"{phrase}: 규정 검색 실패 (HTTP {response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ API 호출 오류 ({phrase}): {e}")
                violations.append(f"{phrase}: 네트워크 오류로 규정 확인 불가")
            except Exception as e:
                print(f"⚠️ 처리 중 오류 ({phrase}): {e}")
                violations.append(f"{phrase}: 처리 오류 - {str(e)}")
        
        # 최종 결과 반환
        if violations:
            return " | ".join(violations)
        else:
            return "OK"
            
    except Exception as e:
        print(f"❌ 규정 검사 중 오류 발생: {e}")
        return f"규정 검사 오류: {str(e)}"

def _check_phrase_against_regulations(phrase: str, search_results: list, llm: ChatOpenAI) -> str:
    """추출된 문구를 규정 정보와 비교하여 위반 여부를 판단합니다."""
    
    try:
        if not search_results:
            return "관련 규정 정보를 찾을 수 없습니다"
        
        # 상위 3개 결과만 사용 (너무 많은 정보 방지)
        top_results = search_results[:3]
        regulations_text = "\n\n".join([
            f"규정 {i+1} (점수: {result.get('score', 0):.2f}):\n{result.get('source', {}).get('content', '')}" 
            for i, result in enumerate(top_results)
        ])
        
        validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """
다음 문구가 제공된 회사 규정을 위반하는지 분석해주세요.

분석 기준:
1. 명확한 규정 위반이 있는지 확인
2. 잠재적 위험이나 주의가 필요한 사항이 있는지 확인
3. 규정에 명시되지 않았더라도 일반적인 컴플라이언스 관점에서 문제가 될 수 있는지 확인

응답 형식:
- 위반이나 문제가 없으면: "OK"
- 문제가 있으면: 구체적인 위반 내용이나 위험 사항을 간단히 설명
            """),
            ("human", "확인할 문구: {phrase}\n\n관련 규정 정보:\n{regulations}")
        ])
        
        response = llm.invoke(validation_prompt.format_messages(
            phrase=phrase, 
            regulations=regulations_text
        ))
        
        result = response.content.strip()
        print(f"🔍 '{phrase}' 규정 검사 결과: {result[:100]}{'...' if len(result) > 100 else ''}")
        
        return result
        
    except Exception as e:
        print(f"⚠️ 규정 비교 중 오류: {e}")
        return f"규정 비교 오류: {str(e)}"

@tool
def convert_structured_to_natural_text(structured_data: Annotated[str, "JSON 형태의 구조화된 데이터"]) -> str:
    """구조화된 데이터를 자연스러운 원문 형태로 변환합니다."""
    
    try:
        # JSON 파싱
        try:
            if isinstance(structured_data, str):
                import json
                data = json.loads(structured_data) if structured_data.startswith('{') else eval(structured_data)
            else:
                data = structured_data
        except (json.JSONDecodeError, SyntaxError) as e:
            return f"데이터 파싱 오류: {str(e)}"
        
        # LLM을 사용해 자연스러운 문장으로 변환
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        conversion_prompt = ChatPromptTemplate.from_messages([
            ("system", """
주어진 구조화된 데이터를 자연스러운 한국어 문장으로 변환해주세요.

변환 규칙:
1. 모든 정보를 빠짐없이 포함해야 합니다
2. 자연스럽고 읽기 쉬운 문장으로 작성해주세요
3. 구어체 형태로 변환해주세요 (예: ~이야, ~야, ~음, ~지)
4. 논리적인 순서로 정보를 배치해주세요
5. 날짜, 연락처, 사이트 등의 정확한 정보는 그대로 유지해주세요

예시 변환:
입력: {{"방문제목": "ABC병원 방문", "방문날짜": "240101", "Client": "ABC병원"}}
출력: 방문 제목은 ABC병원 방문이고 방문일은 240101이고 client는 ABC병원이야

한 문단으로 자연스럽게 연결된 문장을 작성해주세요.
            """),
            ("human", "다음 구조화된 데이터를 자연스러운 원문으로 변환해주세요:\n\n{data}")
        ])
        
        # 데이터를 문자열 형태로 변환
        data_str = str(data) if not isinstance(data, str) else data
        
        response = llm.invoke(conversion_prompt.format_messages(data=data_str))
        natural_text = response.content.strip()
        
        print(f"📝 구조화된 데이터 → 자연어 변환 완료")
        print(f"🔍 변환된 텍스트 길이: {len(natural_text)}자")
        
        return natural_text
        
    except Exception as e:
        print(f"❌ 데이터 변환 중 오류 발생: {e}")
        return f"데이터 변환 오류: {str(e)}"