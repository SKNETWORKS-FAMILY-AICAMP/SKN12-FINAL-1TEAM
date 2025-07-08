#!/usr/bin/env python3
"""
Narutalk 의료업계 QA 챗봇 시스템 통합 실행 스크립트
전체 시스템을 한번에 실행하고 관리합니다.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path


class NarutalkRunner:
    def __init__(self):
        self.processes = []
        self.project_root = Path(__file__).parent
        self.venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        
    def print_banner(self):
        print("=" * 60)
        print("🏥 Narutalk 의료업계 QA 챗봇 시스템")
        print("=" * 60)
        print(f"📍 프로젝트 경로: {self.project_root}")
        print()
        
    def check_requirements(self):
        """필수 요구사항 확인"""
        print("🔍 시스템 요구사항을 확인합니다...")
        
        # 가상환경 확인
        if not self.venv_python.exists():
            print("❌ 가상환경이 없습니다. 먼저 가상환경을 생성하세요:")
            print("   python -m venv .venv")
            return False
            
        # Node.js 확인
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Node.js 또는 npm이 설치되지 않았습니다.")
            return False
            
        # node_modules 확인 및 설치
        node_modules = self.project_root / "node_modules"
        if not node_modules.exists():
            print("📦 Node.js 의존성을 설치합니다...")
            try:
                subprocess.run(["npm", "install"], check=True, cwd=self.project_root)
            except subprocess.CalledProcessError:
                print("❌ npm install 실패")
                return False
                
        print("✅ 모든 요구사항이 충족되었습니다.")
        return True
        
    def run_django(self):
        """Django 백엔드 실행"""
        print("🌐 Django 백엔드를 시작합니다 (포트 8000)...")
        cmd = [str(self.venv_python), "manage.py", "runserver", "--noreload"]
        process = subprocess.Popen(
            cmd, 
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.processes.append(("Django", process))
        return process
        
    def run_fastapi(self):
        """FastAPI 마이크로서비스 실행"""
        print("⚡ FastAPI 검색 서비스를 시작합니다 (포트 8001)...")
        search_dir = self.project_root / "service_8001_search"
        cmd = [str(self.venv_python), "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
        process = subprocess.Popen(
            cmd,
            cwd=search_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.processes.append(("FastAPI", process))
        return process
        
    def run_react(self):
        """React 프론트엔드 실행"""
        print("⚛️ React 프론트엔드를 시작합니다 (포트 5173)...")
        cmd = ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]
        process = subprocess.Popen(
            cmd,
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.processes.append(("React", process))
        return process
        
    def monitor_processes(self):
        """프로세스 모니터링"""
        def monitor_process(name, process):
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"[{name}] {output.strip()}")
                    
        for name, process in self.processes:
            thread = threading.Thread(target=monitor_process, args=(name, process))
            thread.daemon = True
            thread.start()
            
    def cleanup(self):
        """프로세스 정리"""
        print("\n🔄 시스템을 종료합니다...")
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} 서비스가 종료되었습니다.")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 {name} 서비스를 강제 종료했습니다.")
        print("✅ 모든 서비스가 종료되었습니다.")
        
    def run(self):
        """전체 시스템 실행"""
        self.print_banner()
        
        if not self.check_requirements():
            return 1
            
        try:
            # 각 서비스 실행
            self.run_django()
            time.sleep(2)
            
            self.run_fastapi()
            time.sleep(2)
            
            self.run_react()
            time.sleep(3)
            
            # 시작 메시지
            print("\n" + "=" * 60)
            print("🎉 Narutalk 시스템이 성공적으로 시작되었습니다!")
            print("📱 접속 URL:")
            print("  - 메인 웹사이트: http://localhost:5173")
            print("  - Django API: http://localhost:8000")
            print("  - FastAPI 서비스: http://localhost:8001")
            print("=" * 60)
            print("🛑 종료하려면 Ctrl+C를 누르세요")
            print()
            
            # 프로세스 모니터링 시작
            self.monitor_processes()
            
            # 무한 대기
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n사용자가 중단을 요청했습니다.")
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")
        finally:
            self.cleanup()
            
        return 0


def main():
    runner = NarutalkRunner()
    
    # 신호 처리
    def signal_handler(signum, frame):
        runner.cleanup()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    return runner.run()


if __name__ == "__main__":
    sys.exit(main()) 