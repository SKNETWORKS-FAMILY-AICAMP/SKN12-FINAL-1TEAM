import asyncio
import asyncpg
import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseAPIClient:
    """PostgreSQL 데이터베이스 클라이언트"""
    
    def __init__(self):
        self.pool = None
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", "joonpharma"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres")
        }
    
    async def _get_pool(self):
        """연결 풀을 가져오거나 생성합니다."""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(**self.db_config)
                logger.info("Database connection pool created")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise
        return self.pool
    
    async def execute_query(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        SQL 쿼리를 실행하고 결과를 반환합니다.
        
        Args:
            query: 실행할 SQL 쿼리
            params: 쿼리 파라미터
        
        Returns:
            쿼리 결과 리스트
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as connection:
                if params:
                    rows = await connection.fetch(query, *params)
                else:
                    rows = await connection.fetch(query)
                
                # Record 객체를 딕셔너리로 변환
                result = [dict(row) for row in rows]
                return result
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            return []
    
    async def execute_command(self, command: str, params: Optional[List] = None) -> bool:
        """
        SQL 명령을 실행합니다 (INSERT, UPDATE, DELETE 등).
        
        Args:
            command: 실행할 SQL 명령
            params: 명령 파라미터
        
        Returns:
            성공 여부
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as connection:
                if params:
                    await connection.execute(command, *params)
                else:
                    await connection.execute(command)
                return True
                
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            logger.error(f"Command: {command}")
            if params:
                logger.error(f"Params: {params}")
            return False
    
    async def get_employee_info(self, employee_name: str) -> Optional[Dict[str, Any]]:
        """
        직원 정보를 조회합니다.
        
        Args:
            employee_name: 직원명
        
        Returns:
            직원 정보 딕셔너리
        """
        query = """
            SELECT 
                employee_id,
                name,
                사번,
                department,
                position,
                email,
                is_active
            FROM employees
            WHERE name = $1 AND is_deleted = false
        """
        
        result = await self.execute_query(query, [employee_name])
        return result[0] if result else None
    
    async def get_all_employees(self) -> List[Dict[str, Any]]:
        """
        모든 활성 직원 목록을 조회합니다.
        
        Returns:
            직원 정보 리스트
        """
        query = """
            SELECT 
                employee_id,
                name,
                사번,
                department,
                position,
                email
            FROM employees
            WHERE is_active = true AND is_deleted = false
            ORDER BY name
        """
        
        return await self.execute_query(query)
    
    async def close(self):
        """연결 풀을 닫습니다."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")