"""
Import 테스트 - 어디서 오류가 발생하는지 확인
"""
import sys
from pathlib import Path

# 경로 설정
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("=== Import 테스트 ===")

# 1. 기본 모듈
try:
    from dotenv import load_dotenv
    import os
    
    # .env 로드
    env_path = backend_dir / "app" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] .env loaded from {env_path}")
    
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"[OK] OPENAI_API_KEY is set: {api_key[:20]}...")
    else:
        print("[ERROR] OPENAI_API_KEY is not set!")
except Exception as e:
    print(f"[ERROR] Basic imports: {e}")

# 2. RouterAgent import
try:
    from app.services.router_agent.router_agent import RouterAgent
    print("[OK] RouterAgent imported")
    
    # 초기화 테스트
    try:
        agent = RouterAgent()
        print("[OK] RouterAgent initialized")
    except Exception as e:
        print(f"[ERROR] RouterAgent initialization: {e}")
except Exception as e:
    print(f"[ERROR] RouterAgent import: {e}")

# 3. router_state_graph import
try:
    from app.services.router_agent.router_state_graph import router_graph
    print("[OK] router_graph imported")
except Exception as e:
    print(f"[ERROR] router_graph import: {e}")
    import traceback
    traceback.print_exc()

# 4. handlers import
try:
    from app.services.common.handlers import HANDLERS
    print(f"[OK] HANDLERS imported: {list(HANDLERS.keys())}")
except Exception as e:
    print(f"[ERROR] HANDLERS import: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 결론 ===")
print("위의 오류들이 500 에러의 원인입니다.")