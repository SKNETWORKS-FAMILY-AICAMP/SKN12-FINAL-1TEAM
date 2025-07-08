"""
테스트용 환경 변수 설정
API 키 없이도 기본적인 테스트가 가능하도록 mock 설정
"""

import os
from unittest.mock import Mock, patch

# 테스트용 환경 변수 설정
os.environ["OPENAI_API_KEY"] = "test_key_please_set_real_key"
os.environ["OPENAI_MODEL_GPT4O"] = "gpt-4o"
os.environ["OPENAI_MODEL_GPT4O_MINI"] = "gpt-4o-mini"
os.environ["ANTHROPIC_API_KEY"] = "test_key_please_set_real_key"
os.environ["ANTHROPIC_MODEL"] = "claude-3-haiku-20240307"
os.environ["DATABASE_URL"] = "sqlite:///./test_qa_medical.db"
os.environ["DEBUG"] = "true"
os.environ["DEVELOPMENT"] = "true"

print("✅ 테스트용 환경 변수 설정 완료")
print("🚨 주의: 실제 API 키는 .env 파일에 설정하세요!") 