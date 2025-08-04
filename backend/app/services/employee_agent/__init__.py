# Employee Agent Module
"""
Employee Agent Module
직원 실적 분석 에이전트 모듈
"""
from typing import Dict, Any
from .employee_agent import EnhancedEmployeeAgent

# 전역 에이전트 인스턴스
_agent = EnhancedEmployeeAgent()

async def run(query: str, session_id: str, messages: list = None) -> Dict[str, Any]:
    """하위 호환성을 위한 run 함수"""
    return await _agent.run(query, session_id, messages)

# 하위 호환성을 위한 별칭
process_query = run

__all__ = ['run', 'process_query', 'EnhancedEmployeeAgent']