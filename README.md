<<<<<<< HEAD
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



## 지원 에이전트<br/>
<br/>
1. employee_agent: 직원 실적 분석, 인사 정보, 조직도 관련 업무<br/>
2. client_agent: 거래처 분석, 고객 데이터 분석, 매출 분석<br/>
3. db_agent: 데이터베이스 검색, 문서 검색, 정보 조회<br/>
4. docs_agent: 문서 자동생성, 규정 위반 여부 분석, 컴플라이언스 검토<br/>
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
    │ 
    ├── services/ # agent 관리
    │   ├── router_agent/
    │   │   ├── router_agent.py
    │   │   ├── state_graph_router.py
    │   │   └── memory_store_sqlite.py # 대화 저장/조회 기능
    │   │
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

=======
# 📊 Employee Agent 상세 분석 보고서

## 📁 폴더 구조 개요
```
backend/app/services/employee_agent/
├── __init__.py                 # 모듈 진입점 및 export 관리
├── employee_agent.py           # 메인 에이전트 (LangGraph 워크플로우)
├── db_manager.py              # 데이터베이스 관리 및 쿼리 처리
├── query_analyzer.py          # 자연어 쿼리 분석 및 파라미터 추출
└── calculation_tools.py       # 고급 통계 분석 도구
```

## 🔄 시스템 아키텍처 및 데이터 흐름

```
사용자 쿼리
    ↓
[employee_agent.py] ← LangGraph StateGraph 워크플로우
    ↓
┌─────────────────┐
│ 1. Query Analysis│ ← [query_analyzer.py]
└─────────────────┘
    ↓
┌─────────────────┐
│ 2. Data Loading │ ← [db_manager.py]
└─────────────────┘
    ↓
┌─────────────────┐
│ 3. Analysis     │ ← [calculation_tools.py]
└─────────────────┘
    ↓
┌─────────────────┐
│ 4. Report Gen   │ ← OpenAI GPT-4o
└─────────────────┘
    ↓
최종 분석 결과
```

---

## 📄 파일별 상세 분석

### 1. `__init__.py` - 모듈 진입점
**역할**: 패키지 초기화 및 외부 접근 인터페이스 제공

**주요 기능**:
- 모든 핵심 클래스를 `__all__`로 export
- 모듈 설명 및 새로운 기능 목록 문서화
- `analyze_employee_query` 함수를 직접 import 가능하게 함

**코드 구조**:
```python
from .employee_agent import EnhancedEmployeeAgent, analyze_employee_query
from .db_manager import EmployeeDBManager
from .query_analyzer import EmployeeQueryAnalyzer  
from .calculation_tools import PerformanceCalculationTools
```

---

### 2. `employee_agent.py` - 메인 에이전트 (598줄)
**역할**: LangGraph 기반 워크플로우 오케스트레이션 및 전체 프로세스 관리

#### 🏗️ 핵심 클래스: `EnhancedEmployeeAgent`

#### 📊 상태 관리: `AnalysisState` (TypedDict)
```python
class AnalysisState(TypedDict):
    query: str                    # 원본 사용자 쿼리
    query_analysis: Optional[Dict] # 쿼리 분석 결과
    employee_name: Optional[str]   # 추출된 직원명
    start_period: Optional[str]    # 시작 기간 (YYYYMM)
    end_period: Optional[str]      # 종료 기간 (YYYYMM)
    analysis_type: Optional[str]   # 분석 유형
    performance_data: Optional[Dict] # 실적 데이터
    target_data: Optional[Dict]    # 목표 데이터
    analysis_results: Optional[Dict] # 분석 결과
    report: Optional[str]          # 최종 보고서
    error: Optional[str]           # 오류 메시지
```

#### 🔄 LangGraph 워크플로우 (4단계)

**1. `_analyze_query_node` - 쿼리 분석 노드**
- **입력**: 사용자 원본 쿼리
- **처리**: `EmployeeQueryAnalyzer.get_enhanced_analysis()` 호출
- **출력**: 직원명, 기간, 분석유형 추출
- **예외처리**: 추출 실패 시 기본값 설정 (최수아, 202312~202403)

**연관 관계**:
```python
query_analysis = self.query_analyzer.get_enhanced_analysis(query)
```

**2. `_load_data_node` - 데이터 로딩 노드**
- **입력**: 분석 파라미터 (직원명, 기간)
- **처리**: 
  - `db_manager.get_performance_summary()` - 실적 데이터 로드
  - `db_manager.get_target_vs_performance()` - 목표 대비 실적
  - `db_manager.analyze_performance_trend()` - 트렌드 분석
- **출력**: 구조화된 성과 데이터
- **예외처리**: 데이터 없을 시 대체 직원 데이터로 재시도

**연관 관계**:
```python
performance_summary = self.db_manager.get_performance_summary(
    employee_name, start_period, end_period
)
```

**3. `_perform_analysis_node` - 고급 분석 노드**
- **입력**: 로드된 실적/목표 데이터
- **처리**: `PerformanceCalculationTools`의 다양한 분석 함수 호출
  - 트렌드 분석: `calculate_trend_analysis()`
  - 분산 분석: `calculate_variance_analysis()`
  - 계절성 분석: `calculate_seasonal_analysis()`
  - 파레토 분석: `calculate_pareto_analysis()`
  - 예측 분석: `calculate_forecast()`
- **출력**: 종합 분석 결과 딕셔너리

**연관 관계**:
```python
trend_calc = self.calc_tools.calculate_trend_analysis(monthly_amounts)
variance_analysis = self.calc_tools.calculate_variance_analysis(monthly_amounts)
```

**4. `_generate_report_node` - 보고서 생성 노드**
- **입력**: 모든 분석 결과
- **처리**: 
  - OpenAI GPT-4o를 활용한 지능형 보고서 생성
  - LLM 실패 시 기본 보고서 생성으로 폴백
- **출력**: 자연어 형태의 전문 분석 보고서

#### 🎯 핵심 메서드들

**`_generate_comprehensive_evaluation()` - 종합 평가 시스템**
- **기능**: 100점 만점 기준 종합 점수 계산
- **평가 항목**:
  - 목표 달성률 (40점): 120%+ → 40점, 100%+ → 35점
  - 트렌드 (30점): 강한상승 → 30점, 상승 → 30점
  - 안정성 (20점): CV 기반 변동성 평가
  - 집중도 (10점): 파레토 효율성 기반
- **등급 체계**: S(90+), A(80+), B(70+), C(60+), D(60-)

**`_generate_intelligent_report()` - LLM 보고서 생성**
- **모델**: GPT-4o-mini
- **프롬프트**: 구조화된 데이터를 전문적 보고서로 변환
- **폴백**: LLM 실패 시 `_generate_basic_report()` 호출

#### 🔌 외부 인터페이스

**`analyze_employee_performance()` - 메인 분석 함수**
- **입력**: 자연어 쿼리
- **반환**: 표준화된 분석 결과 딕셔너리
- **numpy 타입 방지**: 모든 숫자를 Python 기본 타입으로 변환

**`analyze_employee_query()` - 비동기 래퍼 함수**
- **역할**: API에서 호출하는 전역 함수
- **전역 인스턴스**: `enhanced_agent` 사용

---

### 3. `db_manager.py` - 데이터베이스 관리 (332줄)
**역할**: SQLite 데이터베이스 연결, 쿼리 실행, 데이터 변환

#### 🏗️ 핵심 클래스: `EmployeeDBManager`

#### 📊 데이터베이스 구조
```python
# 실적 데이터베이스: performance_swest_sua.sqlite
sales_performance 테이블:
- 담당자 (직원명)
- 품목 (제품명)
- ID (거래처명)
- 202312, 202401, 202402, 202403... (월별 실적 컬럼)

# 목표 데이터베이스: joonpharma_target.sqlite  
monthly_target 테이블:
- 지점, 담당자, 년월, 목표
```

#### 🔧 핵심 메서드들

**`__init__()` - 경로 설정 및 DB 파일 확인**
- **경로 로직**: 5단계 parent 디렉토리 탐색
- **대안 경로**: 현재 작업 디렉토리 기준 재시도
- **디버깅**: 상세한 경로 로그 출력

**`get_connection()` - DB 연결 관리**
- **입력**: db_type ("performance" | "target")
- **반환**: sqlite3.Connection
- **예외처리**: 파일 존재 확인 후 연결

**`get_available_employees()` - 직원 목록 조회**
```sql
SELECT DISTINCT 담당자 FROM sales_performance WHERE 담당자 IS NOT NULL
```

**`get_performance_summary()` - 실적 요약 생성**
- **핵심 로직**:
  1. 월별 컬럼 추출 (6자리 숫자: 202312, 202401...)
  2. 분석 기간 필터링 (start_period ~ end_period)
  3. 총 실적 계산 및 월별/제품별/거래처별 집계
  4. numpy 타입을 Python 기본 타입으로 변환

**연관 관계**:
```python
# employee_agent.py에서 호출
performance_summary = self.db_manager.get_performance_summary(
    employee_name, start_period, end_period
)
```

**`analyze_performance_trend()` - 트렌드 분석**
- **입력**: 직원명, 분석 기간
- **분석 로직**:
  - 최근 2개월 vs 초기 2개월 평균 비교
  - 상승/하락/안정 분류
  - 월별 실적 배열 반환

**`get_target_vs_performance()` - 목표 대비 실적 분석**
- **핵심 기능**:
  - 실적 데이터와 목표 데이터 결합
  - 달성률 계산 및 등급 부여
  - 목표 데이터 없을 시 실적의 80%를 가상 목표로 설정

**평가 기준**:
```python
if achievement_rate >= 120: evaluation = "매우 우수", grade = "A+"
elif achievement_rate >= 100: evaluation = "우수", grade = "A"
elif achievement_rate >= 80: evaluation = "양호", grade = "B"
elif achievement_rate >= 60: evaluation = "보통", grade = "C"
else: evaluation = "개선 필요", grade = "D"
```

#### 🔍 데이터 타입 변환 처리
모든 메서드에서 **numpy 타입을 Python 기본 타입으로 변환**:
```python
total_performance = int(total_performance)  # numpy.int64 → int
achievement_rate = float(achievement_rate)  # numpy.float64 → float
is_not_na = bool(pd.notna(row[month]))     # numpy.bool_ → bool
```

---

### 4. `query_analyzer.py` - 쿼리 분석 (272줄)
**역할**: 자연어 쿼리를 구조화된 파라미터로 변환

#### 🏗️ 핵심 클래스: `EmployeeQueryAnalyzer`

#### 📝 분석 대상 정보
```python
# 추출 정보
- employee_name: 직원명 (최수아, 조시현)
- start_period, end_period: 분석 기간 (YYYYMM 형식)
- analysis_type: 분석 유형 (종합분석, 트렌드분석 등)
- specific_requests: 특정 요청사항 배열
- confidence: 분석 신뢰도 (0.0~1.0)
```

#### 🔧 핵심 메서드들

**`analyze_query()` - 기본 쿼리 분석**
- **직원명 추출**: 패턴 매칭과 알려진 이름 리스트 조합
```python
name_patterns = [
    r'(\w+)\s*(?:씨|님|직원|담당자)의?\s*실적',
    r'(\w+)\s*(?:씨|님|직원|담당자)\s*분석',
]
```

- **기간 추출**: 다양한 날짜 표현 패턴 처리
```python
period_patterns = {
    r'(\d{4})년\s*(\d{1,2})월': 'YYYYMM',
    r'지난\s*(\d+)\s*개월': 'LAST_N_MONTHS',
    r'작년': 'LAST_YEAR',
    r'올해': 'THIS_YEAR'
}
```

- **분석 유형 분류**: 키워드 기반 분류
```python
analysis_keywords = {
    "트렌드": ["트렌드", "추세", "변화", "흐름"],
    "목표달성": ["목표", "달성", "성과", "평가"],
    "제품분석": ["제품", "품목", "상품", "아이템"]
}
```

**`analyze_with_llm()` - LLM 기반 고급 분석**
- **모델**: GPT-3.5-turbo
- **프롬프트**: JSON 형태로 정보 추출 요청
- **신뢰도**: 0.9 (높은 신뢰도로 설정)

**`get_enhanced_analysis()` - 하이브리드 분석**
- **로직**: 기본 분석과 LLM 분석 중 신뢰도 높은 결과 선택
- **폴백**: LLM 실패 시 기본 분석 결과 사용

**연관 관계**:
```python
# employee_agent.py에서 호출
query_analysis = self.query_analyzer.get_enhanced_analysis(query)
```

#### 🎯 기본값 설정 로직
```python
def _set_defaults(self, analysis_result):
    if not analysis_result["employee_name"]:
        analysis_result["employee_name"] = "최수아"  # 기본 직원
    
    if not analysis_result["start_period"]:
        analysis_result["start_period"] = "202312"  # 실제 데이터 기간
        analysis_result["end_period"] = "202403"
```

---

### 5. `calculation_tools.py` - 통계 분석 도구 (462줄)
**역할**: 고급 통계 분석, 수학적 계산, 예측 분석

#### 🏗️ 핵심 클래스: `PerformanceCalculationTools`
**설계**: 모든 메서드가 `@staticmethod`로 구현된 유틸리티 클래스

#### 📊 제공하는 분석 기능들

**1. `calculate_achievement_rate()` - 달성률 계산**
```python
achievement_rate = (performance / target) * 100
# 120%+ → "매우 우수", 100%+ → "우수", 80%+ → "양호"
```

**2. `calculate_trend_analysis()` - 트렌드 분석**
- **알고리즘**: 선형 회귀 분석
- **계산 요소**:
  - 기울기(slope), 절편(intercept)
  - R² (결정계수) - 트렌드 신뢰도
  - 트렌드 분류: 강한상승, 상승, 안정, 하락, 강한하락

```python
# 선형 회귀 계산
slope = numerator / denominator
r_squared = 1 - (ss_res / ss_tot)

# 트렌드 분류 로직
if slope > y_mean * 0.05:  # 평균의 5% 이상 증가
    trend = "강한 상승"
elif slope > 0:
    trend = "상승"
```

**3. `calculate_variance_analysis()` - 분산 분석**
- **통계 지표**:
  - 분산(variance), 표준편차(std_deviation)
  - 변동계수(CV) = (표준편차/평균) × 100
- **안정성 평가**:
  - CV < 10%: "매우 안정"
  - CV < 20%: "안정"
  - CV ≥ 50%: "매우 불안정"

**4. `calculate_seasonal_analysis()` - 계절성 분석**
- **분석 과정**:
  1. 월별 평균 계산
  2. 계절성 지수 = 월별평균 / 전체평균
  3. 피크/저점 월 식별
  4. 계절성 존재 여부 판단 (최고-최저 차이가 평균의 20% 이상)

**5. `calculate_pareto_analysis()` - 파레토 분석 (80-20 법칙)**
- **핵심 로직**:
  - 항목들을 값 기준으로 내림차순 정렬
  - 누적 기여도 계산
  - 80% 지점 찾기 (파레토 포인트)
  - 상위 20% 항목 식별

**6. `calculate_forecast()` - 예측 분석**
- **예측 방법**: 이동평균 + 선형회귀 가중 평균
- **신뢰도 계산**:
  - 데이터 충분성: min(1.0, len(data)/12)
  - 트렌드 일관성: 1 - std(최근_변화율들)
  - 전체 신뢰도 = (데이터_신뢰도 + 트렌드_일관성) / 2

#### 🔧 numpy 타입 변환 처리
모든 계산 함수에서 **numpy 타입을 Python 기본 타입으로 변환**:
```python
# numpy scalar → Python 기본 타입
correlation = float(correlation_matrix[0, 1])
has_seasonality = bool((max_avg - min_avg) / overall_average > 0.2)
total_score = sum(score_components.values())  # int로 자동 변환
```

**연관 관계**:
```python
# employee_agent.py에서 호출
trend_calc = self.calc_tools.calculate_trend_analysis(monthly_amounts)
variance_analysis = self.calc_tools.calculate_variance_analysis(monthly_amounts)
seasonal_analysis = self.calc_tools.calculate_seasonal_analysis(monthly_data)
```

---

## 🔄 함수 간 연관성 맵

### 메인 워크플로우 체인
```
analyze_employee_query()                    # 전역 함수
    ↓
EnhancedEmployeeAgent.analyze_employee_performance()
    ↓
LangGraph.invoke() → 4단계 노드 실행
    ↓
1. _analyze_query_node()
    → EmployeeQueryAnalyzer.get_enhanced_analysis()
        → analyze_query() + analyze_with_llm()
    ↓
2. _load_data_node()  
    → EmployeeDBManager.get_performance_summary()
    → EmployeeDBManager.get_target_vs_performance()
    → EmployeeDBManager.analyze_performance_trend()
    ↓
3. _perform_analysis_node()
    → PerformanceCalculationTools.calculate_trend_analysis()
    → PerformanceCalculationTools.calculate_variance_analysis()
    → PerformanceCalculationTools.calculate_seasonal_analysis()
    → PerformanceCalculationTools.calculate_pareto_analysis()
    → PerformanceCalculationTools.calculate_forecast()
    ↓
4. _generate_report_node()
    → _generate_intelligent_report() (OpenAI GPT-4o)
    → _generate_basic_report() (폴백)
```

### 클래스 간 의존성
```
EnhancedEmployeeAgent
├── EmployeeDBManager (self.db_manager)
├── EmployeeQueryAnalyzer (self.query_analyzer)  
├── PerformanceCalculationTools (self.calc_tools)
└── StateGraph (self.graph)
```

### 데이터 변환 체인
```
원본 쿼리 (str)
    ↓ [query_analyzer]
쿼리 분석 결과 (Dict)
    ↓ [db_manager]  
SQLite 원시 데이터 (pandas.DataFrame)
    ↓ [db_manager]
구조화된 실적 데이터 (Dict)
    ↓ [calculation_tools]
통계 분석 결과 (Dict)
    ↓ [employee_agent]
종합 평가 및 점수 (Dict)
    ↓ [OpenAI GPT-4o]
자연어 보고서 (str)
```

---

## 🎯 핵심 기술적 특징

### 1. **LangGraph StateGraph 아키텍처**
- **상태 관리**: TypedDict 기반 명확한 상태 정의
- **노드 체인**: 4단계 순차 실행 (분석 → 로딩 → 계산 → 보고서)
- **오류 처리**: 각 노드에서 예외 발생 시 기본값으로 복구

### 2. **하이브리드 쿼리 분석**
- **기본 분석**: 정규표현식 패턴 매칭
- **LLM 분석**: GPT-3.5-turbo 기반 고급 분석
- **신뢰도 기반 선택**: 더 높은 신뢰도 결과 채택

### 3. **SQLite 기반 데이터 처리**
- **동적 컬럼 처리**: 월별 실적 컬럼 자동 감지
- **유연한 기간 필터링**: YYYYMM 형식 기간 범위 처리
- **타입 안정성**: pandas → Python 기본 타입 변환

### 4. **고급 통계 분석**
- **다차원 분석**: 트렌드, 분산, 계절성, 파레토, 예측
- **수학적 정확성**: 선형회귀, 상관분석, 변동계수 등
- **실무 적용성**: 80-20 법칙, 계절성 패턴 등 비즈니스 인사이트

### 5. **지능형 보고서 생성**
- **LLM 통합**: GPT-4o-mini 활용 전문 보고서 생성
- **구조화된 프롬프트**: 데이터 요약 → 전문 보고서 변환
- **폴백 메커니즘**: LLM 실패 시 템플릿 기반 보고서

### 6. **종합 평가 시스템**
- **100점 만점 체계**: 목표달성(40) + 트렌드(30) + 안정성(20) + 집중도(10)
- **등급 체계**: S급(90+) ~ D급(60-)
- **개선 방향 제시**: 낮은 점수 영역을 우선순위로 제시

---

## 🚀 확장 가능성

### 1. **새로운 분석 기법 추가**
- `calculation_tools.py`에 새로운 `@staticmethod` 추가
- `_perform_analysis_node()`에서 호출 로직 추가

### 2. **다양한 데이터 소스 지원**  
- `db_manager.py`에 새로운 데이터베이스 연결 메서드 추가
- 기존 인터페이스 유지하면서 백엔드만 변경

### 3. **실시간 분석**
- 현재는 배치 분석, 스트리밍 데이터 처리 가능
- LangGraph의 비동기 처리 활용

### 4. **다국어 지원**
- `query_analyzer.py`의 패턴을 다국어로 확장
- LLM 프롬프트 다국어 지원

---

## 📈 성능 최적화 포인트

### 1. **데이터베이스 최적화**
- 인덱스 추가: `담당자`, `년월` 컬럼
- 쿼리 최적화: JOIN 대신 별도 쿼리 사용

### 2. **메모리 효율성**
- pandas DataFrame 대신 딕셔너리 사용으로 메모리 절약
- numpy 타입 변환으로 JSON 직렬화 최적화

### 3. **캐싱 전략**
- 직원별 실적 데이터 캐싱
- LLM 분석 결과 캐싱 (동일 쿼리 재사용)

---

**분석 완료일**: 2024년 1월  
**분석 대상**: Employee Agent 모듈 (5개 파일, 총 1,599줄)  
**특징**: LangGraph + SQLite + 고급통계 + LLM 기반 하이브리드 분석 시스템 
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
