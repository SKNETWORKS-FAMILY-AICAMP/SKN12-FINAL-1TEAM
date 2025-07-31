#!/usr/bin/env python3
"""
NaruTalk AI 챗봇 서버 실행 스크립트
<<<<<<< HEAD
가상환경에서 안정적으로 실행되도록 개선된 버전
=======
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
"""

import os
import sys
<<<<<<< HEAD
import uvicorn
from pathlib import Path

def setup_environment():
    """환경 설정"""
    # 경로 설정
    project_root = Path(__file__).parent
    backend_path = project_root / "backend"
    
    # sys.path 설정 (중복 방지)
    paths_to_add = [str(project_root), str(backend_path)]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # 환경 변수 설정
    os.environ.setdefault('PYTHONPATH', str(backend_path))
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    print(f"[INFO] 프로젝트 루트: {project_root}")
    print(f"[INFO] 백엔드 경로: {backend_path}")
    print("[OK] 환경 설정 완료")
    
    return project_root, backend_path

def check_virtual_environment():
    """가상환경 확인"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[OK] 가상환경에서 실행 중")
        print(f"[INFO] Python 경로: {sys.executable}")
        return True
    else:
        print("[WARNING] 가상환경이 활성화되지 않았습니다.")
        print("[TIP] 다음 명령어로 가상환경을 활성화하세요:")
        print("   Windows: .\\venv\\Scripts\\activate")
        print("   Linux/Mac: source venv/bin/activate")
        return False

def check_requirements():
    """필요한 의존성 확인 (개선된 버전)"""
    # 핵심 패키지만 확인
=======
import asyncio
import uvicorn
from pathlib import Path

# 경로 설정
project_root = Path(__file__).parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

def check_requirements():
    """필요한 의존성 확인"""
    # 패키지 이름: (pip 이름, import 이름)
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('langchain', 'langchain'),
<<<<<<< HEAD
        ('langgraph', 'langgraph'),
        ('openai', 'openai'),
        ('python-docx', 'docx')
=======
        ('langchain-core', 'langchain_core'),
        ('langchain-community', 'langchain_community'),
        ('langgraph', 'langgraph'),
        ('sentence-transformers', 'sentence_transformers'),
        ('chromadb', 'chromadb'),
        ('transformers', 'transformers'),
        ('torch', 'torch'),
        ('pytest', 'pytest')
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    ]
    
    missing_packages = []
    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
<<<<<<< HEAD
            print(f"[OK] {pip_name}")
        except ImportError:
            missing_packages.append(pip_name)
            print(f"[FAIL] {pip_name}")
    
    if missing_packages:
        print(f"\n❌ 누락된 패키지: {', '.join(missing_packages)}")
        print("설치 명령어: pip install -r requirements.txt")
        return False
    
    print("✅ 모든 필수 패키지가 설치되어 있습니다.")
=======
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("❌ 다음 패키지가 설치되지 않았습니다:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n설치 명령어:")
        print("pip install -r requirements.txt")
        return False
    
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    return True

def check_directories():
    """필요한 디렉토리 확인"""
<<<<<<< HEAD
    project_root = Path(__file__).parent
    essential_dirs = ["backend", "database"]
    
    missing_dirs = []
    for dir_name in essential_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ 디렉토리 존재")
        else:
            missing_dirs.append(dir_name)
            print(f"❌ {dir_name}/ 디렉토리 없음")
    
    if missing_dirs:
        print(f"❌ 필수 디렉토리 누락: {', '.join(missing_dirs)}")
        return False
    
    return True

def check_environment_variables():
    """환경변수 확인"""
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {openai_key[:10]}...")
    else:
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("💡 .env 파일에 OPENAI_API_KEY=your_key_here 를 추가하세요.")
    
    return bool(openai_key)

def test_import():
    """핵심 모듈 임포트 테스트"""
    try:
        # .env 파일 먼저 로드
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / "backend" / "app" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"[OK] .env 파일 로드: {env_path}")
        
        from backend.app.main import app
        print("[OK] FastAPI 앱 임포트 성공")
        return True
    except ImportError as e:
        print(f"[ERROR] FastAPI 앱 임포트 실패: {e}")
        return False

def main():
    """메인 함수 (개선된 버전)"""
    print("[START] NaruTalk AI 챗봇 시스템 시작")
    print("=" * 60)
    
    # 1. 환경 설정
    print("\n1️⃣ 환경 설정 중...")
    project_root, backend_path = setup_environment()
    
    # 2. 가상환경 확인
    print("\n2️⃣ 가상환경 확인 중...")
    venv_ok = check_virtual_environment()
    
    # 3. 디렉토리 확인
    print("\n3️⃣ 디렉토리 구조 확인 중...")
    dirs_ok = check_directories()
    if not dirs_ok:
        print("❌ 필수 디렉토리가 없어 실행을 중단합니다.")
        sys.exit(1)
    
    # 4. 의존성 확인
    print("\n4️⃣ 의존성 확인 중...")
    deps_ok = check_requirements()
    if not deps_ok:
        print("❌ 필수 패키지가 없어 실행을 중단합니다.")
        sys.exit(1)
    
    # 5. 환경변수 확인
    print("\n5️⃣ 환경변수 확인 중...")
    env_ok = check_environment_variables()
    
    # 6. 모듈 임포트 테스트
    print("\n6️⃣ 모듈 임포트 테스트 중...")
    import_ok = test_import()
    if not import_ok:
        print("❌ 모듈 임포트 실패로 실행을 중단합니다.")
        sys.exit(1)
    
    # 7. 서버 시작
    print("\n7️⃣ 서버 시작 중...")
    print("=" * 60)
    print("📌 서버 정보:")
    print("   🌐 주소: http://localhost:8000")
    print("   📚 API 문서: http://localhost:8000/docs") 
    print("   🔍 헬스 체크: http://localhost:8000/health")
    print("   ⏹️  중지: Ctrl+C")
    print("=" * 60)
    
    if not venv_ok:
        print("⚠️ 가상환경이 활성화되지 않았지만 계속 진행합니다...")
    
    if not env_ok:
        print("⚠️ OpenAI API 키가 설정되지 않았습니다. AI 기능이 제한될 수 있습니다.")
    
    try:
        # 작업 디렉토리 변경
        os.chdir(backend_path)
        
        # FastAPI 서버 시작
        uvicorn.run(
            "app.main:app",
=======
    essential_dirs = [
        "backend",
        "frontend",
        "database"
    ]
    optional_dirs = [
        "models",  # 허깅페이스 모델 사용 시 선택사항
        "tests"
    ]
    
    missing_essential = []
    missing_optional = []
    
    for dir_name in essential_dirs:
        if not (project_root / dir_name).exists():
            missing_essential.append(dir_name)
    
    for dir_name in optional_dirs:
        if not (project_root / dir_name).exists():
            missing_optional.append(dir_name)
    
    if missing_essential:
        print("❌ 다음 필수 디렉토리가 없습니다:")
        for dir_name in missing_essential:
            print(f"  - {dir_name}")
        return False
    
    if missing_optional:
        print("⚠️  다음 선택 디렉토리가 없습니다:")
        for dir_name in missing_optional:
            print(f"  - {dir_name}")
        print("선택 디렉토리는 시스템 작동에 필수가 아닙니다.")
    
    return True

def check_models():
    """모델 파일 확인"""
    print("🔍 허깅페이스 모델 사용 모드로 설정됨")
    print("   - 임베딩 모델: nlpai-lab/KURE-v1")
    print("   - 리랭커 모델: dragonkue/bge-reranker-v2-m3-ko")
    print("   - 로컬 모델 다운로드 불필요")
    
    # 로컬 모델 디렉토리 확인 (참고용)
    model_dirs = [
        "models/KURE-V1",
        "models/bge-reranker-v2-m3-ko"
    ]
    
    missing_models = []
    for model_dir in model_dirs:
        if not (project_root / model_dir).exists():
            missing_models.append(model_dir)
    
    if missing_models:
        print("ℹ️  로컬 모델 디렉토리가 없습니다 (허깅페이스 모델 사용):")
        for model_dir in missing_models:
            print(f"   - {model_dir}")
        print("✅ 허깅페이스에서 모델을 자동으로 다운로드합니다.")
    
    return True

def setup_environment():
    """환경 설정"""
    # 환경 변수 설정
    os.environ.setdefault('PYTHONPATH', str(backend_path))
    
    # 로그 레벨 설정
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    print("✅ 환경 설정 완료")

def main():
    """메인 함수"""
    print("🚀 NaruTalk AI 챗봇 시스템 시작")
    print("=" * 50)
    
    # 1. 의존성 확인
    print("1. 의존성 확인 중...")
    if not check_requirements():
        sys.exit(1)
    print("✅ 의존성 확인 완료")
    
    # 2. 디렉토리 확인
    print("\n2. 디렉토리 구조 확인 중...")
    if not check_directories():
        sys.exit(1)
    print("✅ 디렉토리 구조 확인 완료")
    
    # 3. 모델 확인
    print("\n3. 모델 파일 확인 중...")
    models_ok = check_models()
    if models_ok:
        print("✅ 모델 파일 확인 완료")
    
    # 4. 환경 설정
    print("\n4. 환경 설정 중...")
    setup_environment()
    
    # 5. 서버 시작
    print("\n5. 서버 시작 중...")
    print("=" * 50)
    print("📌 서버 정보:")
    print("   - 주소: http://localhost:8000")
    print("   - API 문서: http://localhost:8000/docs")
    print("   - 테스트 페이지: http://localhost:8000/tests/test_frontend.html")
    print("   - 중지: Ctrl+C")
    print("=" * 50)
    
    try:
        # FastAPI 서버 시작
        os.chdir(backend_path)
        uvicorn.run(
            "main:app",
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(backend_path)],
            log_level="info"
        )
    except KeyboardInterrupt:
<<<<<<< HEAD
        print("\n\n🛑 서버가 사용자에 의해 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 실행 중 오류 발생: {e}")
        print("💡 문제 해결 방법:")
        print("   1. 가상환경이 활성화되어 있는지 확인")
        print("   2. 모든 패키지가 설치되어 있는지 확인: pip install -r requirements.txt")
        print("   3. OPENAI_API_KEY가 .env 파일에 설정되어 있는지 확인")
=======
        print("\n\n🛑 서버가 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 시작 중 오류 발생: {e}")
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
        sys.exit(1)

if __name__ == "__main__":
    main() 