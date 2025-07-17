"""
Router System 통합 테스트
- RouterAgent 클래스 테스트
- StateGraphRouter 클래스 테스트
- 4가지 에이전트 분류 테스트
- 재시도 로직 테스트
- H2H 모드 테스트
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from backend.app.services.router_agent.router_agent import RouterAgent, RouterState
from backend.app.services.router_agent.state_graph_router import StateGraphRouter


class TestRouterAgent(unittest.TestCase):
    def setUp(self):
        """테스트 전 설정"""
        self.router = RouterAgent()
        
    def test_router_agent_initialization(self):
        """RouterAgent 초기화 테스트"""
        self.assertIsNotNone(self.router.client)
        self.assertEqual(len(self.router.available_agents), 4)
        self.assertEqual(self.router.max_retry_attempts, 3)
        self.assertIn("employee_agent", self.router.available_agents)
        self.assertIn("client_agent", self.router.available_agents)
        self.assertIn("db_agent", self.router.available_agents)
        self.assertIn("docs_agent", self.router.available_agents)

    def test_extract_agent_from_response(self):
        """에이전트 추출 테스트"""
        # 정상 응답
        response1 = "AGENT: employee_agent\nREASON: 직원 정보 관련 질문"
        result1 = self.router.extract_agent_from_response(response1)
        self.assertEqual(result1, "employee_agent")
        
        # none 응답
        response2 = "AGENT: none\nREASON: 분류 불가능"
        result2 = self.router.extract_agent_from_response(response2)
        self.assertIsNone(result2)
        
        # 잘못된 형식
        response3 = "잘못된 형식"
        result3 = self.router.extract_agent_from_response(response3)
        self.assertIsNone(result3)

    @patch('backend.app.services.router_agent.router_agent.OpenAI')
    def test_classify_query_success(self, mock_openai):
        """GPT-4o 분류 성공 테스트"""
        # Mock OpenAI 응답
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "AGENT: employee_agent\nREASON: 직원 정보 질문"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = self.router.classify_query("김철수 직원의 실적을 보여줘")
        self.assertIn("employee_agent", result)

    @patch('backend.app.services.router_agent.router_agent.OpenAI')
    def test_classify_query_error(self, mock_openai):
        """GPT-4o 분류 실패 테스트"""
        # Mock OpenAI 에러
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API 오류")
        
        result = self.router.classify_query("테스트 질문")
        self.assertIn("ERROR:", result)


class TestRouterState(unittest.TestCase):
    def test_router_state_initialization(self):
        """RouterState 초기화 테스트"""
        state = RouterState("테스트 질문")
        self.assertEqual(state.query, "테스트 질문")
        self.assertIsNone(state.selected_agent)
        self.assertEqual(state.routing_attempts, 0)
        self.assertEqual(state.final_response, "")
        
    def test_router_state_to_dict(self):
        """RouterState to_dict 테스트"""
        state = RouterState("테스트 질문")
        state.selected_agent = "employee_agent"
        state.routing_attempts = 1
        
        result = state.to_dict()
        self.assertEqual(result["query"], "테스트 질문")
        self.assertEqual(result["selected_agent"], "employee_agent")
        self.assertEqual(result["routing_attempts"], 1)


class TestStateGraphRouter(unittest.TestCase):
    def setUp(self):
        """테스트 전 설정"""
        self.state_router = StateGraphRouter()
        
    def test_state_graph_router_initialization(self):
        """StateGraphRouter 초기화 테스트"""
        self.assertIsNotNone(self.state_router.app)

    @patch('backend.app.services.router_agent.router_agent.RouterAgent.classify_query')
    @patch('backend.app.services.router_agent.router_agent.RouterAgent.extract_agent_from_response')
    def test_process_query_success(self, mock_extract, mock_classify):
        """정상 분류 처리 테스트"""
        # Mock 응답 설정
        mock_classify.return_value = "AGENT: employee_agent\nREASON: 직원 정보"
        mock_extract.return_value = "employee_agent"
        
        result = self.state_router.process_query("김철수 직원의 실적을 보여줘")
        
        self.assertEqual(result["selected_agent"], "employee_agent")
        self.assertEqual(result["routing_attempts"], 1)
        self.assertIn("employee_agent", result["final_response"])

    @patch('backend.app.services.router_agent.router_agent.RouterAgent.classify_query')
    @patch('backend.app.services.router_agent.router_agent.RouterAgent.extract_agent_from_response')
    def test_process_query_none_classification(self, mock_extract, mock_classify):
        """분류 불가능 테스트"""
        # Mock 응답 설정 - 분류 불가능
        mock_classify.return_value = "AGENT: none\nREASON: 분류 불가능"
        mock_extract.return_value = None
        
        result = self.state_router.process_query("의미 없는 질문")
        
        self.assertIsNone(result["selected_agent"])
        self.assertGreaterEqual(result["routing_attempts"], 1)


class TestAgentClassification(unittest.TestCase):
    """에이전트 분류 시나리오 테스트"""
    
    def setUp(self):
        self.router = RouterAgent()
        
    def test_employee_agent_questions(self):
        """직원 관련 질문 테스트"""
        questions = [
            "김철수 직원의 실적을 보여줘",
            "이번 달 우수 직원은 누구인가요?",
            "박영희 사원의 인사 이력을 확인해주세요",
            "조직도를 보여주세요"
        ]
        
        for question in questions:
            with self.subTest(question=question):
                # 실제 분류는 GPT-4o에 의존하므로 Mock 사용
                response = "AGENT: employee_agent\nREASON: 직원 정보 관련"
                agent = self.router.extract_agent_from_response(response)
                self.assertEqual(agent, "employee_agent")
    
    def test_client_agent_questions(self):
        """고객 관련 질문 테스트"""
        questions = [
            "ABC 병원의 매출 추이를 보여줘",
            "주요 거래처 현황을 확인해주세요",
            "잠재 고객 분석 결과는?",
            "이번 분기 영업 성과는?"
        ]
        
        for question in questions:
            with self.subTest(question=question):
                response = "AGENT: client_agent\nREASON: 고객/거래처 관련"
                agent = self.router.extract_agent_from_response(response)
                self.assertEqual(agent, "client_agent")
    
    def test_db_agent_questions(self):
        """데이터베이스 검색 질문 테스트"""
        questions = [
            "사내 규정을 찾아주세요",
            "제품 매뉴얼을 검색해주세요",
            "교육 자료를 찾아주세요",
            "업무 프로세스 문서를 보여줘"
        ]
        
        for question in questions:
            with self.subTest(question=question):
                response = "AGENT: db_agent\nREASON: 데이터베이스 검색 관련"
                agent = self.router.extract_agent_from_response(response)
                self.assertEqual(agent, "db_agent")
    
    def test_docs_agent_questions(self):
        """문서 생성 질문 테스트"""
        questions = [
            "월간 보고서를 작성해주세요",
            "컴플라이언스 위반 여부를 확인해주세요",
            "영업 계획서를 생성해주세요",
            "문서 오류를 검토해주세요"
        ]
        
        for question in questions:
            with self.subTest(question=question):
                response = "AGENT: docs_agent\nREASON: 문서 생성/검토 관련"
                agent = self.router.extract_agent_from_response(response)
                self.assertEqual(agent, "docs_agent")


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2) 