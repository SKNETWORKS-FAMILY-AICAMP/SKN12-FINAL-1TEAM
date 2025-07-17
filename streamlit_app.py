import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import requests

st.set_page_config(page_title="RouterAgent 성능테스트", page_icon="🤖")
st.title("🤖 GPT-4o 기반 4분류 라우팅 성능 테스트")

# 테스트용 (선택)
st.caption(f"🔑 OPENAI KEY 시작: {os.getenv('OPENAI_API_KEY')[:10] if os.getenv('OPENAI_API_KEY') else '❌ 미등록'}")


st.markdown("질문을 입력하면, GPT-4o가 적절한 에이전트로 분류합니다.")

# 사용자 입력
query = st.text_area("질문을 입력하세요", height=120, placeholder="예: 김철수 직원의 실적을 보여줘")


# 실행 버튼
if st.button("질문 처리"):
    if not query.strip():
        st.warning("❗ 질문을 입력해주세요.")
    else:
        endpoint = "http://localhost:8000/api/v1/route/graph"

        with st.spinner("에이전트 분류 중..."):
            try:
                response = requests.post(endpoint, json={"query": query})
                if response.status_code == 200:
                    data = response.json()

                    st.success("✅ 라우팅 결과")

                    st.markdown(f"**🧠 선택된 에이전트:** `{data['selected_agent']}`")
                    st.markdown(f"**🔍 분류 근거:** `{data['classification_result']}`")
                    st.markdown(f"**📤 최종 응답:** {data['final_response']}")
                    st.markdown(f"**🔁 시도 횟수:** `{data['routing_attempts']}`")

                    if data.get("error_message"):
                        st.warning(f"⚠️ 오류 메시지: {data['error_message']}")

                else:
                    st.error(f"❌ 요청 실패: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"❌ 연결 실패: {str(e)}")
