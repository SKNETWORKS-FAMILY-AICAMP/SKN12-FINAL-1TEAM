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
 <b>김도윤</b><br/><span style="font-size:14px;"> P M </sub>
</td>
<td align="center">
 <img src="./team/2.png" width="120px"><br/>
 <b>손현성</b><br/><span style="font-size:14px;">백앤드/인프라 </sub>
</td>
<td align="center">
 <img src="./team/3.png" width="120px"><br/>
 <b>이용규</b><br/><span style="font-size:14px;">QC </sub>
</td>
<td align="center">
 <img src="./team/6.png" width="120px"><br/>
 <b>최문영</b><br/><span style="font-size:14px;">프론트 </sub>
</td>
<td align="center">
 <img src="./team/5.png" width="120px"><br/>
 <b>허한결</b><br/><span style="font-size:14px;">데이터베이스구축 </sub>
</td>
</tr>
</table>
  </p>
</div>
<h1>📚 STACKS</h1>

<!-- Backend & Language -->
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)

<!-- Database & Search -->
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![OpenSearch](https://img.shields.io/badge/OpenSearch-005EB8?style=for-the-badge&logo=opensearch&logoColor=white)

<!-- AI & LLM -->
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-000000?style=for-the-badge&logo=langgraph&logoColor=white)
![HuggingFace](https://img.shields.io/badge/🤗_Hugging_Face-FFD21E?style=for-the-badge&logoColor=black)
![KURE](https://img.shields.io/badge/KURE--v1-FF6B6B?style=for-the-badge&logo=huggingface&logoColor=white)
![BGE Reranker](https://img.shields.io/badge/BGE_Reranker--v2--m3-4ECDC4?style=for-the-badge&logo=huggingface&logoColor=white)

<!-- DevOps & Deploy -->
![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
![RunPod](https://img.shields.io/badge/RunPod-FFAFCC?style=for-the-badge&logo=runpod&logoColor=black)

<!-- Crawling & OAuth -->
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)

<!-- Collaboration -->
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)

</div>



## 🤖 지원 에이전트<br/>
<br/>
1. **employee_agent**: 직원 실적 분석, 인사 정보, 조직도 관련 업무<br/>
2. **client_agent**: 거래처 분석, 고객 데이터 분석, 매출 분석<br/>
3. **db_agent**: 데이터베이스 검색, 문서 검색, 정보 조회<br/>
4. **docs_agent**: 문서 자동생성, 규정 위반 여부 분석, 컴플라이언스 검토<br/>
<br/><br/>
</div>
</table>
에이전트 흐름도<br/>        
<img src="./team/11.png" style="width:100%; max-width:1000px;">
<img src="./team/12.png" style="width:100%; max-width:1000px;">
<img src="./team/13.png" style="width:100%; max-width:1000px;">
<img src="./team/14.png" style="width:100%; max-width:1000px;">
<img src="./team/15.png" style="width:100%; max-width:1000px;">
<img src="./team/16.png" style="width:100%; max-width:1000px;">

## 📂 **프로젝트 구조**<br/>
```
backend/
└── app/
    ├── main.py # FastAPI 실행
    │
    ├── api/ # API 관리
    │   ├── router_api.py
    │   ├── client_api.py
    │   ├── docs_api.py
    │   ├── employee_api.py
    │   └── search_api.py
    ├── services/ # agent 관리
    │   ├── router_agent/
    │   │   ├── router_agent.py
    │   │   ├── state_graph_router.py
    │   │   └── memory_store_sqlite.py # 대화 저장/조회 기능
    │   ├── client_agent/
    │   ├── employee_agent/
    │   ├── docs_agent/
    │   └── search_agent/

database/
└── history/
    └── memory.sqlite

frontend/
└── react
```

