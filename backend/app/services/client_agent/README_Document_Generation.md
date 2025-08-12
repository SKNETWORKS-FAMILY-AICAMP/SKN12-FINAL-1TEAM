# 거래처 분석 보고서 문서 생성 기능

이 문서는 `client_agent.py`에 추가된 문서 생성 기능에 대한 설명입니다.

## 기능 개요

레포트 분석 결과를 다음 두 가지 형식의 문서로 자동 생성할 수 있습니다:

1. **Word 문서 (.docx)** - 비즈니스 보고서용
2. **HTML 문서 (.html)** - 웹 브라우저에서 확인 가능

## 설치된 라이브러리

```bash
pip install python-docx>=0.8.11 jinja2>=3.1.0
```

## 주요 기능

### 1. Word 문서 생성 (`generate_word_document`)

- **구조화된 보고서**: 목차, 섹션별 페이지 나누기
- **테이블 포함**: 등급 요약, 주요 지표 테이블
- **스타일링**: 한글 폰트(맑은 고딕) 적용
- **프로페셔널한 레이아웃**: 비즈니스 보고서에 적합

### 2. HTML 문서 생성 (`generate_html_document`)

- **반응형 디자인**: 모바일/데스크톱 모두 지원
- **색상 코딩**: 등급별 색상 구분 (A=초록, B=연초록, C=노랑, D=연빨강, E=빨강)
- **인쇄 최적화**: CSS 미디어 쿼리로 인쇄 시 최적화
- **모던한 UI**: 깔끔하고 읽기 쉬운 디자인

### 3. 통합 문서 생성 (`generate_documents`)

- **한 번에 두 형식 생성**: Word와 HTML 동시 생성
- **자동 파일명**: 거래처명과 타임스탬프 포함
- **디렉토리 관리**: 지정된 폴더에 자동 저장

## 사용법

### 기본 사용법

```python
from client_agent import ClientAgent, run_full_pipeline

# 1. 전체 파이프라인 실행 (문서 생성 포함)
result = await run_full_pipeline(
    agent=agent,
    company_name="거래처001",
    start_month=202401,
    end_month=202412,
    generate_docs=True,  # 문서 생성 활성화
    output_dir="./reports"  # 출력 디렉토리 지정
)

# 결과 확인
report_state = result["report_state"]
documents = result["documents"]

print(f"Word 문서: {documents['word']}")
print(f"HTML 문서: {documents['html']}")
```

### 개별 문서 생성

```python
# Word 문서만 생성
word_path = agent.generate_word_document(report_state, "custom_name.docx")

# HTML 문서만 생성
html_path = agent.generate_html_document(report_state, "custom_name.html")

# 두 문서 모두 생성
doc_results = agent.generate_documents(report_state, "./output_folder")
```

## 생성되는 문서 구조

### Word 문서 구조
1. **제목 페이지**: 보고서 제목, 거래처명, 생성일
2. **목차**: 섹션별 목차
3. **등급 분석 결과**: 등급 요약 테이블, 주요 지표, 상세 분석
4. **동일 등급 비교 분석**: 경쟁사 비교 결과
5. **성장성 분석**: 매출/예산 추이 분석
6. **영업 전략 제안**: 구체적인 전략 제안
7. **종합 분석**: 전체 요약 및 결론

### HTML 문서 구조
- **반응형 헤더**: 제목, 거래처명, 생성일
- **색상 코딩된 테이블**: 등급별 색상 구분
- **섹션별 구분**: 명확한 섹션 구분
- **인쇄 최적화**: 인쇄 시 깔끔한 레이아웃

## 파일명 규칙

생성되는 파일명은 다음 형식을 따릅니다:
```
거래처분석보고서_{거래처명}_{YYYYMMDD_HHMMSS}.{확장자}
```

예시:
- `거래처분석보고서_거래처001_20241201_143022.docx`
- `거래처분석보고서_거래처001_20241201_143022.html`

## 테스트

문서 생성 기능을 테스트하려면:

```bash
python test_document_generation.py
```

이 스크립트는:
1. 샘플 데이터로 개별 문서 생성 테스트
2. 실제 데이터가 있는 경우 전체 파이프라인 테스트

## 주의사항

1. **한글 폰트**: Word 문서는 '맑은 고딕' 폰트를 사용합니다.
2. **파일 권한**: 출력 디렉토리에 쓰기 권한이 필요합니다.
3. **메모리 사용**: 대용량 데이터의 경우 메모리 사용량에 주의하세요.
4. **네트워크**: HTML 문서는 로컬에서 생성되므로 인터넷 연결이 필요하지 않습니다.

## 커스터마이징

### Word 문서 스타일 변경

`_add_heading_with_style` 메서드에서 폰트 크기와 스타일을 수정할 수 있습니다:

```python
def _add_heading_with_style(self, document, text, level=1):
    heading = document.add_heading(text, level=level)
    for run in heading.runs:
        run.font.name = '맑은 고딕'  # 폰트 변경
        run.font.size = Pt(16 if level == 1 else 14 if level == 2 else 12)  # 크기 변경
        run.font.bold = True
    return heading
```

### HTML 문서 스타일 변경

HTML 템플릿의 CSS 부분을 수정하여 색상과 레이아웃을 변경할 수 있습니다.

## 문제 해결

### 일반적인 오류

1. **폰트 오류**: 시스템에 '맑은 고딕' 폰트가 없는 경우 다른 폰트로 변경
2. **권한 오류**: 출력 디렉토리에 쓰기 권한 확인
3. **메모리 부족**: 대용량 데이터 처리 시 배치 처리 고려

### 로그 확인

```python
import logging
logging.basicConfig(level=logging.INFO)
```

로그를 통해 문서 생성 과정을 모니터링할 수 있습니다. 