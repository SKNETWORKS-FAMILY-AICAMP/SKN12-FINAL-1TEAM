"""
테이블 설명 JSON 파일 로더
pgvector 초기화 시 사용되는 유틸리티 함수
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_table_descriptions() -> Dict[str, Any]:
    """테이블 설명 JSON 파일을 로드합니다"""
    try:
        # 현재 파일의 디렉토리를 기준으로 상대 경로 계산
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'table_descriptions.json')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            table_descriptions = json.load(f)
        
        logger.info(f"테이블 설명 로드 완료: {len(table_descriptions)}개 테이블")
        return table_descriptions
        
    except FileNotFoundError:
        logger.error(f"테이블 설명 파일을 찾을 수 없음: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"테이블 설명 JSON 파싱 오류: {e}")
        raise
    except Exception as e:
        logger.error(f"테이블 설명 로드 중 오류: {e}")
        raise