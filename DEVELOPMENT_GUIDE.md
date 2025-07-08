# 🛠️ Narutalk 개발 가이드

## 📋 **개발 환경 설정**

### 1. 초기 설정
```bash
# 저장소 클론
git clone [repository-url]
cd Narutalk

# 자동 설치
install.bat

# 수동 설치
.\.venv\Scripts\activate
pip install -r requirements/development.txt
npm install
python manage.py migrate
```

## 🎯 **새 기능 추가 방법**

### 📱 **Django 백엔드 기능 추가**

#### 1. 새로운 앱 생성
```bash
# 새 Django 앱 생성
python manage.py startapp new_feature

# apps/ 디렉토리로 이동
mv new_feature apps/

# settings에 추가
# config/settings/base.py의 INSTALLED_APPS에 'apps.new_feature' 추가
```

#### 2. 모델 정의 (apps/new_feature/models.py)
```python
from django.db import models
from apps.authentication.models import User

class NewModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'new_model'
```

#### 3. API 직렬화기 (apps/new_feature/serializers.py)
```python
from rest_framework import serializers
from .models import NewModel

class NewModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewModel
        fields = '__all__'
```

#### 4. API 뷰 (apps/new_feature/views.py)
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import NewModel
from .serializers import NewModelSerializer

class NewModelViewSet(viewsets.ModelViewSet):
    queryset = NewModel.objects.all()
    serializer_class = NewModelSerializer
    permission_classes = [IsAuthenticated]
```

#### 5. URL 라우팅
```python
# apps/new_feature/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewModelViewSet

router = DefaultRouter()
router.register(r'items', NewModelViewSet)

urlpatterns = [
    path('api/new-feature/', include(router.urls)),
]

# config/urls.py에 추가
path('', include('apps.new_feature.urls')),
```

#### 6. 마이그레이션
```bash
python manage.py makemigrations new_feature
python manage.py migrate
```

### ⚛️ **React 프론트엔드 기능 추가**

#### 1. 새 Redux 슬라이스 (src/store/slices/newFeatureSlice.ts)
```typescript
import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface NewFeatureState {
  items: any[]
  loading: boolean
  error: string | null
}

const initialState: NewFeatureState = {
  items: [],
  loading: false,
  error: null
}

const newFeatureSlice = createSlice({
  name: 'newFeature',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setItems: (state, action: PayloadAction<any[]>) => {
      state.items = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    }
  }
})

export const { setLoading, setItems, setError } = newFeatureSlice.actions
export default newFeatureSlice.reducer
```

#### 2. 컴포넌트 생성 (src/components/NewFeature/NewFeatureComponent.tsx)
```typescript
import React, { useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '../../store'
import { setItems, setLoading } from '../../store/slices/newFeatureSlice'

const NewFeatureComponent: React.FC = () => {
  const dispatch = useDispatch()
  const { items, loading } = useSelector((state: RootState) => state.newFeature)

  useEffect(() => {
    // API 호출 로직
    fetchData()
  }, [])

  const fetchData = async () => {
    dispatch(setLoading(true))
    try {
      const response = await fetch('/api/new-feature/items/')
      const data = await response.json()
      dispatch(setItems(data))
    } catch (error) {
      console.error('Error:', error)
    } finally {
      dispatch(setLoading(false))
    }
  }

  return (
    <div>
      {loading ? <div>로딩 중...</div> : <div>{/* 데이터 렌더링 */}</div>}
    </div>
  )
}

export default NewFeatureComponent
```

#### 3. 스토어에 슬라이스 추가 (src/store/index.ts)
```typescript
import newFeatureReducer from './slices/newFeatureSlice'

export const store = configureStore({
  reducer: {
    // 기존 리듀서들...
    newFeature: newFeatureReducer
  }
})
```

### 🤖 **AI 기능 확장**

#### 1. 새 노드 추가 (langgraph_orchestrator/qa_agent/utils/nodes.py)
```python
def new_ai_node(state):
    """새로운 AI 처리 노드"""
    user_input = state.get("user_input", "")
    
    # AI 처리 로직
    response = process_with_ai(user_input)
    
    return {
        "ai_response": response,
        "processed": True
    }
```

#### 2. 도구 추가 (langgraph_orchestrator/qa_agent/utils/tools.py)
```python
from langchain.tools import tool

@tool
def new_search_tool(query: str) -> str:
    """새로운 검색 도구"""
    # 검색 로직 구현
    return search_results
```

### ⚡ **FastAPI 마이크로서비스 추가**

#### 1. 새 서비스 생성
```bash
mkdir service_8002_analysis
cd service_8002_analysis
```

#### 2. FastAPI 앱 구성 (service_8002_analysis/main.py)
```python
from fastapi import FastAPI
from .routes import router

app = FastAPI(title="Analysis Service")
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

## 📊 **데이터베이스 관리**

### 모델 수정 및 마이그레이션
```bash
# 모델 변경 후
python manage.py makemigrations
python manage.py migrate

# 특정 앱만 마이그레이션
python manage.py makemigrations app_name
python manage.py migrate app_name

# 마이그레이션 되돌리기
python manage.py migrate app_name migration_name
```

### 테스트 데이터 생성
```python
# management/commands/create_test_data.py
from django.core.management.base import BaseCommand
from apps.authentication.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 테스트 사용자 생성
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
```

## 🧪 **테스트 작성**

### Django 테스트
```python
# apps/new_feature/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class NewFeatureTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_item(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/new-feature/items/', {
            'title': 'Test Item'
        })
        self.assertEqual(response.status_code, 201)
```

### React 테스트
```typescript
// src/components/NewFeature/__tests__/NewFeatureComponent.test.tsx
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { store } from '../../../store'
import NewFeatureComponent from '../NewFeatureComponent'

test('renders new feature component', () => {
  render(
    <Provider store={store}>
      <NewFeatureComponent />
    </Provider>
  )
  expect(screen.getByText(/새 기능/i)).toBeInTheDocument()
})
```

## 🚀 **배포 준비**

### 환경별 설정
```python
# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# 프로덕션 데이터베이스 설정
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}
```

### Docker 설정
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements/production.txt .
RUN pip install -r production.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application"]
```

## 📝 **코딩 규칙**

### Python (Django/FastAPI)
```python
# 클래스명: PascalCase
class UserProfile:
    pass

# 함수명, 변수명: snake_case
def get_user_data():
    user_id = 123
    
# 상수: UPPER_CASE
MAX_FILE_SIZE = 10 * 1024 * 1024
```

### TypeScript (React)
```typescript
// 컴포넌트명: PascalCase
const UserProfile: React.FC = () => {}

// 함수명, 변수명: camelCase
const getUserData = () => {
  const userId = 123
}

// 상수: UPPER_CASE
const MAX_FILE_SIZE = 10 * 1024 * 1024
```

## 🔄 **Git 워크플로우**

### 브랜치 전략
```bash
main         # 프로덕션 코드
├── develop  # 개발 통합 브랜치
│   ├── feature/user-management
│   ├── feature/chat-enhancement
│   └── feature/ai-optimization
├── hotfix/critical-bug-fix
└── release/v1.0.0
```

### 커밋 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드/패키지 관련

예시:
feat(auth): JWT 토큰 갱신 기능 추가
fix(chat): WebSocket 연결 끊김 문제 해결
```

## 📊 **성능 모니터링**

### 로깅 설정
```python
# config/settings/base.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🔧 **문제 해결**

### 일반적인 이슈들
1. **포트 충돌**: `netstat -ano | findstr :8000`
2. **패키지 충돌**: `pip install --force-reinstall`
3. **마이그레이션 오류**: `python manage.py migrate --fake`
4. **React 빌드 오류**: `npm cache clean --force`

### 디버깅 도구
```python
# Django 디버깅
import pdb; pdb.set_trace()

# React 디버깅
console.log('Debug:', data)
debugger;
```

이 가이드를 따라하면 Narutalk 시스템을 효율적으로 확장하고 유지보수할 수 있습니다. 