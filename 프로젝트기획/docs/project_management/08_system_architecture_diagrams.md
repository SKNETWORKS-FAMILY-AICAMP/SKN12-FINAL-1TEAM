# 🏗️ 시스템 아키텍처 다이어그램 (System Architecture Diagrams)

## 📋 문서 개요

### 1.1 목적
의료업계 영업/관리용 QA 챗봇 시스템의 LangGraph 중심 아키텍처 시각화

### 1.2 범위
- 전체 시스템 아키텍처 다이어그램
- 상세 데이터 플로우 다이어그램  
- 기술 스택 및 인프라 구성 다이어그램
- 실제 요청 처리 플로우 다이어그램

### 1.3 LangGraph 역할
**LangGraph StateGraph = 전체 QA 시스템의 오케스트레이터**
- 복잡한 워크플로우 관리
- 10개 마이크로서비스 조율
- 상태 기반 데이터 전달
- 병렬 처리 및 조건부 라우팅
- AI 모델들과의 완벽한 통합

## 🏗️ 1. 상세 시스템 아키텍처

```mermaid
graph LR
    subgraph "📱 Frontend Layer"
        FE[React 18 + TypeScript<br/>Material-UI<br/>Redux Toolkit]
    end
    
    subgraph "🚪 API Gateway Layer"
        GW[Django Gateway<br/>Port 8000<br/>JWT Auth + CORS]
    end
    
    subgraph "🔄 LANGGRAPH STATEFULWORKFLOW"
        direction TB
        
        subgraph "🧠 AI Processing Pipeline"
            LG1[LangGraph Node 1<br/>Intent Classification<br/>OpenAI GPT-3.5]
            LG2[LangGraph Node 2<br/>Memory Load<br/>Redis + Memory DB]
            LG3[LangGraph Node 3<br/>Service Router<br/>Conditional Logic]
        end
        
        subgraph "⚡ Microservices Layer (병렬 실행)"
            MS1[Integrated Search<br/>Port 8001]
            MS2[Performance Analytics<br/>Port 8002]
            MS3[Client Analysis<br/>Port 8003]
            MS4[Document Automation<br/>Port 8004]
            MS5[Conversation Analysis<br/>Port 8005]
            MS6[Data Wiki<br/>Port 8006]
            MS7[News Recommendation<br/>Port 8007]
            MS8[🔧 ML Performance<br/>Port 8008]
            MS9[Memory Management<br/>Port 8009]
        end
        
        subgraph "💾 Data Storage Layer"
            subgraph "SQLite Databases"
                DB1[main.db]
                DB2[users.db]
                DB3[sales.db]
                DB4[clients.db]
                DB5[news.db]
                DB6[cache.db]
                DB7[🧠 ml.db]
                DB8[memory.db]
            end
            
            subgraph "Memory System"
                RD1[Redis DB0<br/>세션 관리]
                RD2[Redis DB1<br/>대화 컨텍스트]
                RD3[Redis DB2<br/>임시 계산]
                RD4[Redis DB3<br/>사용자 선호도]
            end
            
            subgraph "File System"
                FS1[documents/]
                FS2[uploads/]
                FS3[conversations/]
                FS4[wiki/]
                FS5[memory/]
            end
            
            subgraph "Vector & ML Storage"
                VDB[FAISS Vector DB<br/>indices/embeddings/metadata]
                MLF[🧠 MLflow Server<br/>Port 5000<br/>models/experiments]
            end
            
            subgraph "External APIs"
                NAPI[네이버 API<br/>뉴스 데이터]
            end
        end
        
        subgraph "🤖 AI Integration Layer"
            LG4[LangGraph Node 4<br/>Data Processing<br/>Feature Engineering]
            LG5[LangGraph Node 5<br/>AI Processing<br/>BGE + OpenAI]
            LG6[LangGraph Node 6<br/>Result Collection<br/>State Management]
        end
        
        subgraph "🎯 Final Processing"
            LG7[LangGraph Node 7<br/>Result Fusion<br/>OpenAI GPT-3.5]
            LG8[LangGraph Node 8<br/>Final Generation<br/>OpenAI GPT-4]
            LG9[LangGraph Node 9<br/>Memory Update<br/>Learning & Storage]
        end
    end
    
    subgraph "📤 Output Layer"
        OUT[JSON Response<br/>최종 답변]
    end
    
    FE --> GW
    GW --> LG1
    LG1 --> LG2
    LG2 --> LG3
    
    LG3 --> MS1
    LG3 --> MS2
    LG3 --> MS3
    LG3 --> MS4
    LG3 --> MS5
    LG3 --> MS6
    LG3 --> MS7
    LG3 --> MS8
    LG3 --> MS9
    
    MS1 --> DB1
    MS1 --> FS1
    MS1 --> VDB
    MS2 --> DB3
    MS2 --> DB6
    MS3 --> DB4
    MS4 --> FS1
    MS4 --> FS2
    MS5 --> DB8
    MS5 --> FS3
    MS6 --> FS4
    MS6 --> VDB
    MS7 --> DB5
    MS7 --> NAPI
    MS8 --> DB7
    MS8 --> MLF
    MS9 --> RD1
    MS9 --> RD2
    MS9 --> RD3
    MS9 --> RD4
    MS9 --> DB8
    
    DB1 --> LG4
    DB3 --> LG4
    DB4 --> LG4
    DB5 --> LG4
    DB6 --> LG4
    DB7 --> LG4
    DB8 --> LG4
    FS1 --> LG5
    FS2 --> LG5
    FS3 --> LG5
    FS4 --> LG5
    VDB --> LG5
    MLF --> LG5
    NAPI --> LG4
    
    LG4 --> LG6
    LG5 --> LG6
    LG6 --> LG7
    LG7 --> LG8
    LG8 --> LG9
    LG9 --> OUT
    
    style LG1 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG2 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style LG3 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style LG5 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG6 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style LG7 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG8 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG9 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style MS8 fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style DB7 fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style MLF fill:#e1f5fe,stroke:#01579b,stroke-width:2px
```

## 🔧 2. 상세 데이터 플로우 (포트 번호 포함)

```mermaid
graph LR
    subgraph "📥 INPUT"
        USER[사용자 질의<br/>HTTP Request]
    end
    
    subgraph "🔄 LANGGRAPH STATEFULWORKFLOW ENGINE"
        direction TB
        
        subgraph "🚪 Gateway & Auth"
            DG[Django Gateway<br/>:8000<br/>JWT + CORS + Rate Limiting]
        end
        
        subgraph "🧠 AI Pipeline Stage 1"
            LG1[LangGraph Node: Intent<br/>OpenAI GPT-3.5-turbo<br/>temperature=0.1]
            LG2[LangGraph Node: Memory<br/>Redis Session Load<br/>Context Retrieval]
            LG3[LangGraph Node: Router<br/>Conditional Logic<br/>Service Selection]
        end
        
        subgraph "⚡ Parallel Microservices"
            direction TB
            MS1[Integrated Search<br/>:8001<br/>FAISS + BGE + OpenAI]
            MS2[Performance Analytics<br/>:8002<br/>Pandas + Chart.js]
            MS3[Client Analysis<br/>:8003<br/>Scikit-learn + ML]
            MS4[Document Automation<br/>:8004<br/>OpenAI + Template]
            MS5[Conversation Analysis<br/>:8005<br/>Sentiment + NLP]
            MS6[Data Wiki<br/>:8006<br/>Knowledge Graph]
            MS7[News Recommendation<br/>:8007<br/>Naver API + Filter]
            MS8[🔧 ML Performance<br/>:8008<br/>XGBoost + Prophet]
            MS9[Memory Management<br/>:8009<br/>Redis + SQLite Sync]
        end
        
        subgraph "💾 Storage Infrastructure"
            subgraph "Primary Databases"
                DB1[main.db<br/>App Config]
                DB2[users.db<br/>User Profiles]
                DB3[sales.db<br/>Performance Data]
                DB4[clients.db<br/>Client Records]
                DB5[news.db<br/>News Articles]
                DB6[cache.db<br/>Query Cache]
                DB7[🧠 ml.db<br/>Model Metadata]
                DB8[memory.db<br/>Conversation History]
            end
            
            subgraph "Memory Layer"
                RD1[Redis :6379 DB0<br/>Session Management<br/>TTL: 30min]
                RD2[Redis :6379 DB1<br/>Conversation Context<br/>TTL: 2hours]
                RD3[Redis :6379 DB2<br/>Temp Calculations<br/>TTL: 1hour]
                RD4[Redis :6379 DB3<br/>User Preferences<br/>TTL: 24hours]
            end
            
            subgraph "File Storage"
                FS1[documents/<br/>PDF, DOCX, TXT]
                FS2[uploads/<br/>User Files]
                FS3[conversations/<br/>Chat Logs]
                FS4[wiki/<br/>Knowledge Base]
                FS5[memory/<br/>Backup Files]
            end
            
            subgraph "Vector & ML"
                VDB[FAISS Vector DB<br/>1M+ embeddings<br/>KURE-v1 model]
                MLF[🧠 MLflow Server<br/>:5000<br/>Model Registry<br/>Experiment Tracking]
            end
            
            subgraph "External APIs"
                NAPI[네이버 Search API<br/>Real-time News<br/>Rate Limit: 1000/day]
                OAPI[OpenAI API<br/>GPT-3.5/4<br/>Rate Limit: 60/min]
            end
        end
        
        subgraph "🤖 AI Processing Stage 2"
            LG4[LangGraph Node: Data Proc<br/>Feature Engineering<br/>Data Validation]
            LG5[LangGraph Node: AI Proc<br/>BGE Reranking<br/>OpenAI Enhancement]
            LG6[LangGraph Node: Collection<br/>State Aggregation<br/>Result Merging]
        end
        
        subgraph "🎯 Final Generation"
            LG7[LangGraph Node: Fusion<br/>OpenAI GPT-3.5<br/>Result Integration]
            LG8[LangGraph Node: Generation<br/>OpenAI GPT-4<br/>Final Answer]
            LG9[LangGraph Node: Memory<br/>Learning Update<br/>Pattern Storage]
        end
    end
    
    subgraph "📤 OUTPUT"
        RESP[JSON Response<br/>+ Metadata<br/>+ Confidence Score]
    end
    
    USER --> DG
    DG --> LG1
    LG1 --> LG2
    LG2 --> LG3
    
    LG3 --> MS1
    LG3 --> MS2
    LG3 --> MS3
    LG3 --> MS4
    LG3 --> MS5
    LG3 --> MS6
    LG3 --> MS7
    LG3 --> MS8
    LG3 --> MS9
    
    MS1 -.-> DB1
    MS1 -.-> FS1
    MS1 -.-> VDB
    MS2 -.-> DB3
    MS2 -.-> DB6
    MS3 -.-> DB4
    MS4 -.-> FS1
    MS4 -.-> FS2
    MS5 -.-> DB8
    MS5 -.-> FS3
    MS6 -.-> FS4
    MS6 -.-> VDB
    MS7 -.-> DB5
    MS7 -.-> NAPI
    MS8 -.-> DB7
    MS8 -.-> MLF
    MS9 -.-> RD1
    MS9 -.-> RD2
    MS9 -.-> RD3
    MS9 -.-> RD4
    MS9 -.-> DB8
    
    DB1 --> LG4
    DB3 --> LG4
    DB4 --> LG4
    DB5 --> LG4
    DB6 --> LG4
    DB7 --> LG4
    DB8 --> LG4
    FS1 --> LG5
    FS2 --> LG5
    FS3 --> LG5
    FS4 --> LG5
    VDB --> LG5
    MLF --> LG5
    NAPI --> LG4
    
    LG1 -.-> OAPI
    LG5 -.-> OAPI
    LG7 -.-> OAPI
    LG8 -.-> OAPI
    
    LG4 --> LG6
    LG5 --> LG6
    LG6 --> LG7
    LG7 --> LG8
    LG8 --> LG9
    LG9 --> RESP
    
    style LG1 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG2 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style LG3 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style LG5 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG6 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style LG7 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG8 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style LG9 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style MS8 fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style DB7 fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style MLF fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style OAPI fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
```

## 🏗️ 3. 기술 스택 및 인프라 구성

```mermaid
graph LR
    subgraph "🌐 Client Layer"
        WEB[React 18 + TypeScript<br/>Vite + Material-UI<br/>Redux Toolkit]
        MOBILE[Mobile App<br/>React Native<br/>Future Enhancement]
    end
    
    subgraph "🛡️ Security & Gateway"
        LB[Load Balancer<br/>Nginx + SSL<br/>Rate Limiting]
        GW[Django Gateway<br/>JWT + CORS<br/>Request Routing]
        AUTH[Auth Service<br/>User Management<br/>Session Control]
    end
    
    subgraph "🔄 LANGGRAPH ORCHESTRATION LAYER"
        direction TB
        
        subgraph "🧠 Core AI Pipeline"
            INTENT[Intent Node<br/>OpenAI GPT-3.5-turbo<br/>Classification Logic]
            MEMORY[Memory Node<br/>Redis + SQLite<br/>Context Management]
            ROUTER[Router Node<br/>Conditional Logic<br/>Service Selection]
        end
        
        subgraph "📊 Business Logic Services"
            direction TB
            
            subgraph "Data Services"
                SEARCH[Search Service<br/>FAISS + OpenAI<br/>Hybrid Search]
                PERF[Performance Service<br/>Pandas + NumPy<br/>Data Analysis]
                CLIENT[Client Service<br/>Scikit-learn<br/>Classification]
            end
            
            subgraph "Content Services"
                DOC[Document Service<br/>OpenAI + Templates<br/>Generation Engine]
                CONV[Conversation Service<br/>NLP + Sentiment<br/>Analysis Engine]
                WIKI[Wiki Service<br/>Knowledge Graph<br/>Semantic Search]
            end
            
            subgraph "Integration Services"
                NEWS[News Service<br/>Naver API<br/>Content Filtering]
                ML[🔧 ML Service<br/>XGBoost + Prophet<br/>MLflow Integration]
                MEM[Memory Service<br/>Redis Sync<br/>Pattern Learning]
            end
        end
        
        subgraph "💾 Data Infrastructure"
            direction TB
            
            subgraph "Primary Storage"
                SQLITE[SQLite Cluster<br/>8 Databases<br/>ACID Compliance]
                REDIS[Redis Cluster<br/>4 Databases<br/>In-Memory Cache]
                FILES[File System<br/>Documents + Uploads<br/>Backup System]
            end
            
            subgraph "AI Storage"
                FAISS[FAISS Vector DB<br/>1M+ Embeddings<br/>KURE-v1 Model]
                MLFLOW[🧠 MLflow Server<br/>Model Registry<br/>Experiment Tracking]
                MODELS[Model Storage<br/>Trained Models<br/>Version Control]
            end
            
            subgraph "External Integration"
                NAVER[Naver Search API<br/>Real-time News<br/>Content Aggregation]
                OPENAI[OpenAI API<br/>GPT-3.5/4 Models<br/>Rate Limited]
                KURE[KURE-v1 Embedding<br/>Korean Language<br/>Semantic Understanding]
            end
        end
        
        subgraph "🎯 AI Processing Pipeline"
            PROC[Data Processing<br/>Feature Engineering<br/>Validation]
            ENHANCE[AI Enhancement<br/>BGE Reranking<br/>OpenAI Processing]
            COLLECT[Result Collection<br/>State Management<br/>Data Aggregation]
            FUSION[Result Fusion<br/>OpenAI Integration<br/>Context Merging]
            GENERATE[Final Generation<br/>GPT-4 Processing<br/>Quality Assurance]
            SAVE[Memory Update<br/>Learning Storage<br/>Pattern Recognition]
        end
    end
    
    subgraph "📈 Monitoring & Analytics"
        METRICS[Prometheus<br/>System Metrics<br/>Performance Monitoring]
        LOGS[ELK Stack<br/>Centralized Logging<br/>Error Tracking]
        GRAFANA[Grafana Dashboard<br/>Real-time Visualization<br/>Alerting System]
    end
    
    subgraph "🔧 DevOps & Deployment"
        DOCKER[Docker Containers<br/>Microservice Isolation<br/>Resource Management]
        COMPOSE[Docker Compose<br/>Local Development<br/>Service Orchestration]
        GITHUB[GitHub Actions<br/>CI/CD Pipeline<br/>Automated Testing]
    end
    
    WEB --> LB
    MOBILE --> LB
    LB --> GW
    GW --> AUTH
    AUTH --> INTENT
    
    INTENT --> MEMORY
    MEMORY --> ROUTER
    
    ROUTER --> SEARCH
    ROUTER --> PERF
    ROUTER --> CLIENT
    ROUTER --> DOC
    ROUTER --> CONV
    ROUTER --> WIKI
    ROUTER --> NEWS
    ROUTER --> ML
    ROUTER --> MEM
    
    SEARCH --> SQLITE
    SEARCH --> FAISS
    PERF --> SQLITE
    CLIENT --> SQLITE
    DOC --> FILES
    CONV --> SQLITE
    WIKI --> FILES
    WIKI --> FAISS
    NEWS --> NAVER
    ML --> MLFLOW
    ML --> MODELS
    MEM --> REDIS
    MEM --> SQLITE
    
    SQLITE --> PROC
    REDIS --> PROC
    FILES --> ENHANCE
    FAISS --> ENHANCE
    MLFLOW --> ENHANCE
    NAVER --> PROC
    
    PROC --> COLLECT
    ENHANCE --> COLLECT
    COLLECT --> FUSION
    FUSION --> GENERATE
    GENERATE --> SAVE
    
    INTENT -.-> OPENAI
    ENHANCE -.-> OPENAI
    FUSION -.-> OPENAI
    GENERATE -.-> OPENAI
    SEARCH -.-> KURE
    WIKI -.-> KURE
    
    INTENT --> METRICS
    MEMORY --> METRICS
    ROUTER --> METRICS
    SEARCH --> LOGS
    PERF --> LOGS
    CLIENT --> LOGS
    DOC --> LOGS
    CONV --> LOGS
    WIKI --> LOGS
    NEWS --> LOGS
    ML --> LOGS
    MEM --> LOGS
    
    METRICS --> GRAFANA
    LOGS --> GRAFANA
    
    style INTENT fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style MEMORY fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style ROUTER fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style ENHANCE fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style COLLECT fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style FUSION fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style GENERATE fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style SAVE fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style ML fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style MLFLOW fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style MODELS fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style OPENAI fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
```

## 🔄 4. 실제 요청 처리 플로우 (Step-by-Step)

```mermaid
graph LR
    subgraph "📥 Request Input"
        REQ[User Query<br/>ABC 회사 실적 분석해줘]
    end
    
    subgraph "🔄 LANGGRAPH STATE MANAGEMENT"
        direction TB
        
        subgraph "Step 1: Initial Processing"
            S1A[Django Gateway<br/>Port 8000<br/>✓ JWT Validation<br/>✓ Rate Limiting<br/>✓ CORS Check]
            S1B[LangGraph Init<br/>QAState 생성<br/>session_id 할당<br/>query 저장]
        end
        
        subgraph "Step 2: AI Classification"
            S2A[OpenAI GPT-3.5 Call<br/>temperature=0.1<br/>max_tokens=100<br/>Intent Classification]
            S2B[State Update<br/>intent: performance_analysis<br/>confidence: 0.95<br/>timestamp 기록]
        end
        
        subgraph "Step 3: Memory Loading"
            S3A[Redis Session Load<br/>DB0: session_data<br/>DB1: conversation_context<br/>DB2: temp_calculations]
            S3B[Memory DB Query<br/>user_profile 조회<br/>conversation_history 조회<br/>learned_patterns 조회]
            S3C[State Update<br/>user_context 추가<br/>previous_conversations 추가<br/>preferences 설정]
        end
        
        subgraph "Step 4: Service Selection"
            S4A[Router Logic<br/>intent=performance_analysis<br/>→ Performance Service 선택<br/>→ Client Service 선택]
            S4B[Parallel Execution<br/>Performance Analytics:8002<br/>Client Analysis:8003<br/>동시 실행]
        end
        
        subgraph "Step 5: Data Processing"
            S5A[Performance Service<br/>sales.db 쿼리<br/>ABC 회사 데이터 추출<br/>Pandas 데이터 처리]
            S5B[Client Service<br/>clients.db 쿼리<br/>ABC 회사 정보 추출<br/>등급 분류 실행]
            S5C[State Update<br/>performance_data 추가<br/>client_data 추가<br/>processing_time 기록]
        end
        
        subgraph "Step 6: AI Enhancement"
            S6A[BGE Reranking<br/>검색 결과 재정렬<br/>relevance_score 계산]
            S6B[OpenAI Enhancement<br/>데이터 해석<br/>인사이트 추출]
            S6C[State Update<br/>enhanced_results 추가<br/>ai_insights 추가]
        end
        
        subgraph "Step 7: Result Integration"
            S7A[Data Fusion<br/>performance_data + client_data<br/>correlation 분석<br/>trend 계산]
            S7B[Context Integration<br/>previous_conversations 반영<br/>user_preferences 적용]
            S7C[State Update<br/>integrated_results 생성<br/>context_applied 표시]
        end
        
        subgraph "Step 8: Final Generation"
            S8A[OpenAI GPT-4 Call<br/>temperature=0.7<br/>max_tokens=1000<br/>Final Answer 생성]
            S8B[Quality Check<br/>answer_quality 검증<br/>completeness 확인<br/>accuracy 점검]
            S8C[State Update<br/>final_answer 설정<br/>quality_score 기록<br/>generation_time 기록]
        end
        
        subgraph "Step 9: Memory Update"
            S9A[Redis Update<br/>session_data 갱신<br/>conversation_context 저장<br/>temp_results 저장]
            S9B[Memory DB Update<br/>conversation_history 추가<br/>user_patterns 업데이트<br/>performance_metrics 저장]
            S9C[Learning Update<br/>successful_patterns 기록<br/>user_feedback 예상<br/>improvement_areas 식별]
        end
    end
    
    subgraph "📤 Response Output"
        RESP[JSON Response<br/>answer: ABC 회사 분석 결과<br/>confidence: 0.95<br/>processing_time: 3.2s<br/>sources: sales.db, clients.db]
    end
    
    REQ --> S1A
    S1A --> S1B
    S1B --> S2A
    S2A --> S2B
    S2B --> S3A
    S3A --> S3B
    S3B --> S3C
    S3C --> S4A
    S4A --> S4B
    S4B --> S5A
    S4B --> S5B
    S5A --> S5C
    S5B --> S5C
    S5C --> S6A
    S6A --> S6B
    S6B --> S6C
    S6C --> S7A
    S7A --> S7B
    S7B --> S7C
    S7C --> S8A
    S8A --> S8B
    S8B --> S8C
    S8C --> S9A
    S9A --> S9B
    S9B --> S9C
    S9C --> RESP
    
    style S1B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S2A fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style S2B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S3A fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S3B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S3C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S4A fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S5C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S6B fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style S6C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S7C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S8A fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style S8C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S9A fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S9B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style S9C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

## 📊 색상 코드 범례

### 🎨 컴포넌트 색상 구분
- **🟠 OpenAI 통합**: Intent Classification, AI Enhancement, Result Fusion, Final Generation
- **🟣 LangGraph State 관리**: Memory Load, Service Router, Result Collection, Memory Update
- **🔵 ML 관련**: ML Performance Service, MLflow, ML Database
- **🟢 데이터 저장소**: SQLite, Redis, File System, Vector DB
- **⚫ 기본 서비스**: 마이크로서비스들, Gateway, Frontend

## 🏗️ 시스템 구성 요약

### 📊 **핵심 컴포넌트**
- **Frontend**: React 18 + TypeScript + Material-UI
- **Gateway**: Django Gateway (:8000) + JWT Auth
- **Microservices**: 10개 FastAPI 서비스 (:8001-8009)
- **LangGraph**: StateGraph 워크플로우 오케스트레이션
- **AI Integration**: OpenAI GPT-3.5/4 + KURE-v1 + BGE
- **Storage**: SQLite(8개) + Redis(4개) + FAISS + MLflow
- **External**: 네이버 API + OpenAI API

### 🔄 **LangGraph 역할**
1. **상태 관리**: QAState를 통한 전체 데이터 흐름 제어
2. **워크플로우 제어**: 9단계 처리 과정 오케스트레이션
3. **병렬 처리**: 10개 마이크로서비스 동시 실행 관리
4. **조건부 라우팅**: Intent에 따른 적응적 서비스 선택
5. **AI 통합**: OpenAI 모델들과의 seamless 연동

### 🎯 **성능 및 확장성**
- **병렬 처리**: 독립적 서비스들의 동시 실행
- **메모리 최적화**: 숏텀(Redis) + 롱텀(Memory DB) 이중 구조
- **캐싱 전략**: 다층 캐시 시스템 (Redis + SQLite Cache)
- **모니터링**: Prometheus + Grafana + ELK Stack
- **CI/CD**: Docker + GitHub Actions

## 📝 문서 관리 정보

**파일명**: `08_system_architecture_diagrams.md`  
**생성일**: 2024-01-01  
**최종 수정일**: 2024-01-01  
**작성자**: AI Assistant  
**검토자**: System Architect  
**버전**: 1.0

### 📋 업데이트 이력
- **v1.0** (2024-01-01): 초기 아키텍처 다이어그램 생성
  - 상세 시스템 아키텍처 추가
  - 데이터 플로우 다이어그램 추가
  - 기술 스택 구성 다이어그램 추가
  - 요청 처리 플로우 다이어그램 추가

### 🔗 관련 문서
- [시스템설계서](./03_system_design.md)
- [API명세서](./05_api_specification.md)
- [데이터베이스설계서](./04_database_design.md)
- [기능명세서](./02_functional_specification.md)

---

**💡 참고사항**: 
- 모든 다이어그램은 Mermaid 형식으로 작성되어 GitHub, GitLab 등에서 자동 렌더링됩니다.
- 각 다이어그램은 독립적으로 복사하여 다른 문서에서도 사용할 수 있습니다.
- 시스템 변경 시 해당 다이어그램을 업데이트해주세요. 