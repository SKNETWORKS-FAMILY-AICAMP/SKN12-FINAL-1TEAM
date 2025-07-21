## 제약영업사원 업무효율을 위한 문서검색 및 업무자동화 AI partner - llm기반 QA 챗봇 - Phase 1
### "LLM을 활용한 사내 문서 검색 및 업무지원형 디지털 비서 시스템"
##### 내 생각을 이해하고, 내 일을 함께하는 디지털 분신- 나루톡 <br/>
##### 모든 문서와 대화를 하나로 연결하는 스마트 허브 챗봇 - 나투록 <br/>
###### 나루톡 ( 모든 기능의 허브라는 뜻의 순우리말 '나룻터' 와 대화를 주고받는 talk의 합성어로,사용자의 모든 생각과 행동을 연결해주는 디지털 분신 챗봇 )

---

</div>


## 👥 팀 소개

<table>
  <tr>
    <td align="center">
      <img src="./team/1.png" width="120px"><br/>
      <b>김도윤</b><br/><span style="font-size:14px;">시스템 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/2.png" width="120px"><br/>
      <b>손현성</b><br/><span style="font-size:14px;">백앤드/인프라팀장</sub>
    </td>
    <td align="center">
      <img src="./team/3.png" width="120px"><br/>
      <b>이용규</b><br/><span style="font-size:14px;">QC 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/4.png" width="120px"><br/>
      <b>최문영</b><br/><span style="font-size:14px;">프론트 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/5.png" width="120px"><br/>
      <b>허한결</b><br/><span style="font-size:14px;">DB 팀장</sub>
    </td>
  </tr>
</table>
## 📂 **프로젝트 구조**
## 🚀 주요 기능

### 🎯 4가지 라우터 시스템
- **데이터베이스 자동 업데이트 및 검색**: 문서 기반 질문 답변
- **직원 실적 분석 및 보고서 작성**: 임베딩 기반 문서 검색
- **서류 자동화 및 규정 검토**: 직원 데이터베이스 조회
- **거래처 실적 분석 및 등급 분류**: 일반적인 대화 처리

### 💡 핵심 기술
- **프론트엔드**: ReACT
- **백엔드**: Django, FastAPI, Python 3.11.7
- **LLM**: OpenAI Gpt-4o
- **임베딩 모델** : snowflake-arctic-embed-l-v2.0-ko
- **리랭커 모델** : dragonkue/bge-reranker-v2-m3-ko
- **라우터**: LangGraph 0.5
- **데이터베이스**: 오픈서치, PostgreSQL

## 📁 프로젝트 구조
