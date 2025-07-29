"""
컨텍스트 관리자 - 대화 연속성을 위한 문맥 추적 및 관리
"""
import re
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationContext:
    """세션별 대화 컨텍스트 관리"""
    
    def __init__(self):
        self.last_person: Optional[str] = None          # 마지막 언급된 사람
        self.last_client: Optional[str] = None          # 마지막 언급된 고객/병원
        self.last_topic: Optional[str] = None           # 마지막 주제
        self.last_time_period: Optional[str] = None     # 마지막 시간 표현
        self.last_metric: Optional[str] = None          # 마지막 지표
        self.last_agent: Optional[str] = None           # 마지막 사용 에이전트
        self.last_update: datetime = datetime.now()      # 마지막 업데이트 시간
        
    def to_dict(self) -> Dict[str, Any]:
        """컨텍스트를 딕셔너리로 변환"""
        return {
            "last_person": self.last_person,
            "last_client": self.last_client,
            "last_topic": self.last_topic,
            "last_time_period": self.last_time_period,
            "last_metric": self.last_metric,
            "last_agent": self.last_agent,
            "last_update": self.last_update.isoformat()
        }


class ContextManager:
    """대화 컨텍스트 관리자"""
    
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        
        # 엔티티 추출 패턴
        self.patterns = {
            'person': r'([가-힣]{2,4})\s*(사원|직원|님|씨)?',
            'client': r'([가-힣]+병원|[가-힣]+의원|[가-힣]+약국|[A-Z]병원)',
            'time': r'(오늘|어제|이번\s*주|저번\s*주|이번\s*달|저번\s*달|작년|올해|[0-9]+월|[0-9]+년)',
            'metric': r'(실적|매출|판매량|목표|달성률|성과)'
        }
        
        # 주제 키워드 매핑
        self.topic_keywords = {
            'performance': ['실적', '매출', '성과', '목표', '달성'],
            'client': ['고객', '병원', '거래처', '약국', '의원'],
            'employee': ['직원', '사원', '인사', '조직', '부서'],
            'document': ['문서', '보고서', '양식', '서류', '계획서']
        }
        
        # 참조 표현 패턴
        self.reference_patterns = {
            'person': ['그 사람', '해당 직원', '그 직원', '같은 사람'],
            'client': ['그 병원', '해당 고객', '그 거래처', '같은 곳'],
            'thing': ['그것', '그거', '것', '그걸'],
            'previous': ['방금', '아까', '위에서', '이전에']
        }
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """세션 컨텍스트 가져오기 또는 생성"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext()
        return self.contexts[session_id]
    
    def extract_entities(self, query: str) -> Dict[str, Optional[str]]:
        """쿼리에서 엔티티 추출"""
        entities = {}
        
        # 사람 이름 추출
        person_match = re.search(self.patterns['person'], query)
        if person_match:
            entities['person'] = person_match.group(1)
            
        # 고객/병원 추출
        client_match = re.search(self.patterns['client'], query)
        if client_match:
            entities['client'] = client_match.group(1)
            
        # 시간 표현 추출
        time_match = re.search(self.patterns['time'], query)
        if time_match:
            entities['time'] = time_match.group(1)
            
        # 지표 추출
        metric_match = re.search(self.patterns['metric'], query)
        if metric_match:
            entities['metric'] = metric_match.group(1)
            
        # 주제 판단
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in query for keyword in keywords):
                entities['topic'] = topic
                break
                
        logger.info(f"추출된 엔티티: {entities}")
        return entities
    
    def resolve_references(self, query: str, context: ConversationContext) -> str:
        """참조 표현을 실제 값으로 해결"""
        resolved_query = query
        
        # 사람 참조 해결
        for ref in self.reference_patterns['person']:
            if ref in query and context.last_person:
                resolved_query = resolved_query.replace(ref, context.last_person)
                logger.info(f"참조 해결: '{ref}' -> '{context.last_person}'")
        
        # 고객 참조 해결
        for ref in self.reference_patterns['client']:
            if ref in query and context.last_client:
                resolved_query = resolved_query.replace(ref, context.last_client)
                logger.info(f"참조 해결: '{ref}' -> '{context.last_client}'")
        
        # "그것" 류 참조 해결 - 문맥에 따라 다르게 처리
        for ref in self.reference_patterns['thing']:
            if ref in query:
                # 마지막 주제와 관련 정보로 추론
                if context.last_topic == 'performance' and context.last_person:
                    if context.last_metric:
                        replacement = f"{context.last_person}의 {context.last_metric}"
                    else:
                        replacement = f"{context.last_person}의 실적"
                    resolved_query = resolved_query.replace(ref, replacement)
                    logger.info(f"참조 해결: '{ref}' -> '{replacement}'")
                elif context.last_topic == 'client' and context.last_client:
                    replacement = f"{context.last_client} 정보"
                    resolved_query = resolved_query.replace(ref, replacement)
                    logger.info(f"참조 해결: '{ref}' -> '{replacement}'")
        
        return resolved_query
    
    def enhance_query(self, query: str, context: ConversationContext) -> str:
        """쿼리를 컨텍스트 기반으로 보완"""
        enhanced = query
        
        # 시간 표현만 있는 경우
        time_only_patterns = [r'^작년$', r'^올해$', r'^이번\s*달$', r'^저번\s*달$']
        for pattern in time_only_patterns:
            if re.match(pattern, query.strip()):
                if context.last_person and context.last_metric:
                    enhanced = f"{context.last_person}의 {query} {context.last_metric}"
                elif context.last_client and context.last_metric:
                    enhanced = f"{context.last_client}의 {query} {context.last_metric}"
                logger.info(f"쿼리 보완: '{query}' -> '{enhanced}'")
                break
        
        # 사람 이름만 있는 경우
        person_only_match = re.match(r'^([가-힣]{2,4})\s*(사원|직원|님)?$', query.strip())
        if person_only_match and context.last_topic:
            person_name = person_only_match.group(1)
            if context.last_topic == 'performance':
                enhanced = f"{person_name}의 실적"
            elif context.last_metric:
                enhanced = f"{person_name}의 {context.last_metric}"
            logger.info(f"쿼리 보완: '{query}' -> '{enhanced}'")
        
        return enhanced
    
    def update_context(self, session_id: str, query: str, response: Optional[Dict] = None):
        """쿼리와 응답을 기반으로 컨텍스트 업데이트"""
        context = self.get_or_create_context(session_id)
        
        # 엔티티 추출
        entities = self.extract_entities(query)
        
        # 컨텍스트 업데이트
        if entities.get('person'):
            context.last_person = entities['person']
        if entities.get('client'):
            context.last_client = entities['client']
        if entities.get('topic'):
            context.last_topic = entities['topic']
        if entities.get('time'):
            context.last_time_period = entities['time']
        if entities.get('metric'):
            context.last_metric = entities['metric']
            
        # 응답에서 에이전트 정보 업데이트
        if response and response.get('agent'):
            context.last_agent = response['agent']
            
        context.last_update = datetime.now()
        
        logger.info(f"컨텍스트 업데이트 완료: {context.to_dict()}")
    
    def process_query(self, session_id: str, query: str) -> str:
        """쿼리 처리: 참조 해결 및 보완"""
        context = self.get_or_create_context(session_id)
        
        # 1. 참조 해결
        resolved_query = self.resolve_references(query, context)
        
        # 2. 쿼리 보완
        enhanced_query = self.enhance_query(resolved_query, context)
        
        logger.info(f"쿼리 처리: '{query}' -> '{enhanced_query}'")
        return enhanced_query
    
    def clear_context(self, session_id: str):
        """특정 세션의 컨텍스트 초기화"""
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"세션 {session_id}의 컨텍스트 초기화")


# 싱글톤 인스턴스
context_manager = ContextManager()