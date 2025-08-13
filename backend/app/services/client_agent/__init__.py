"""
Client Agent Module
거래처 분석 에이전트
"""
from .client_agent_v1 import run_full_pipeline as run, ClientAgent

# router_agent 호환성을 위한 래퍼 클래스
class ClientAgentWrapper:
    def __init__(self):
        self.agent = ClientAgent()
    
    async def run(self, user_input, **kwargs):
        return await run(self.agent, user_input, **kwargs)

# router_agent 호환성을 위한 인스턴스
client_agent = ClientAgentWrapper()

__all__ = ['run', 'ClientAgent', 'client_agent']