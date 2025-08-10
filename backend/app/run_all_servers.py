"""
모든 서버를 동시에 실행하는 스크립트
- 8000 포트: 에이전트 서버 (docs_agent, router_agent)
- 8010 포트: 메인 백엔드 서버 (user, admin)
"""
import subprocess
import sys
from pathlib import Path
import threading
import time

def run_agent_server():
    """8000 포트에서 에이전트 서버 실행"""
    print("Starting Agent Server on port 8000...")
    subprocess.run([sys.executable, "agent_server.py"])

def run_main_server():
    """8010 포트에서 메인 서버 실행"""
    print("Starting Main Server on port 8010...")
    subprocess.run([sys.executable, "main.py"])

if __name__ == "__main__":
    print("="*60)
    print("Starting All Servers")
    print("-"*60)
    print("1. Agent Server: http://localhost:8000")
    print("   - Docs Agent API: /api/v1/docs/*")
    print("   - Router Agent API: /api/v1/*")
    print("-"*60)
    print("2. Main Server: http://localhost:8010")
    print("   - User API: /user/*")
    print("   - Admin API: /admin/*")
    print("="*60)
    print("\nPress Ctrl+C to stop all servers\n")
    
    # 두 서버를 별도 스레드에서 실행
    agent_thread = threading.Thread(target=run_agent_server)
    main_thread = threading.Thread(target=run_main_server)
    
    agent_thread.start()
    time.sleep(2)  # 에이전트 서버가 먼저 시작되도록 잠시 대기
    main_thread.start()
    
    try:
        # 두 스레드가 모두 종료될 때까지 대기
        agent_thread.join()
        main_thread.join()
    except KeyboardInterrupt:
        print("\n\nStopping all servers...")
        sys.exit(0)