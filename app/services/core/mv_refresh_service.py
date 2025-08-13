"""
Materialized View 자동 갱신 서비스
데이터 업로드 후 관련 MV를 자동으로 갱신합니다.
"""

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from typing import List, Optional, Union

logger = logging.getLogger(__name__)

class MVRefreshService:
    """Materialized View 갱신 서비스 클래스"""
    
    @staticmethod
    async def refresh_customer_performance_mv(db: Union[Session, AsyncSession]) -> bool:
        """
        거래처 성과 MV 갱신
        
        Args:
            db: 데이터베이스 세션 (동기 또는 비동기)
            
        Returns:
            bool: 갱신 성공 여부
        """
        try:
            logger.info("🔄 customer_monthly_performance_mv 갱신 시작...")
            # AsyncSession인 경우 await 사용
            if isinstance(db, AsyncSession):
                await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY customer_monthly_performance_mv"))
                await db.commit()
            else:
                # 일반 Session인 경우 동기 실행
                db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY customer_monthly_performance_mv"))
                db.commit()
            logger.info("✅ customer_monthly_performance_mv 갱신 완료")
            return True
        except Exception as e:
            logger.error(f"❌ customer_monthly_performance_mv 갱신 실패: {e}")
            if isinstance(db, AsyncSession):
                await db.rollback()
            else:
                db.rollback()
            return False
    
    @staticmethod
    async def refresh_employee_performance_mv(db: Union[Session, AsyncSession]) -> bool:
        """
        직원 성과 MV 갱신
        
        Args:
            db: 데이터베이스 세션 (동기 또는 비동기)
            
        Returns:
            bool: 갱신 성공 여부
        """
        try:
            logger.info("🔄 employee_performance_mv 갱신 시작...")
            # AsyncSession인 경우 await 사용
            if isinstance(db, AsyncSession):
                await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY employee_performance_mv"))
                await db.commit()
            else:
                # 일반 Session인 경우 동기 실행
                db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY employee_performance_mv"))
                db.commit()
            logger.info("✅ employee_performance_mv 갱신 완료")
            return True
        except Exception as e:
            logger.error(f"❌ employee_performance_mv 갱신 실패: {e}")
            if isinstance(db, AsyncSession):
                await db.rollback()
            else:
                db.rollback()
            return False
    
    @staticmethod
    async def refresh_all_mvs(db: Union[Session, AsyncSession]) -> dict:
        """
        모든 MV 갱신
        
        Args:
            db: 데이터베이스 세션 (동기 또는 비동기)
            
        Returns:
            dict: 각 MV별 갱신 결과
        """
        results = {
            'customer_monthly_performance_mv': False,
            'employee_performance_mv': False
        }
        
        # 거래처 성과 MV 갱신
        results['customer_monthly_performance_mv'] = await MVRefreshService.refresh_customer_performance_mv(db)
        
        # 직원 성과 MV 갱신
        results['employee_performance_mv'] = await MVRefreshService.refresh_employee_performance_mv(db)
        
        # 결과 로깅
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info(f"✅ 모든 MV 갱신 완료 ({success_count}/{total_count})")
        else:
            logger.warning(f"⚠️ 일부 MV 갱신 실패 ({success_count}/{total_count})")
        
        return results
    
    @staticmethod
    async def refresh_mvs_for_table(db: Union[Session, AsyncSession], table_name: str) -> bool:
        """
        특정 테이블과 관련된 MV만 갱신
        
        Args:
            db: 데이터베이스 세션 (동기 또는 비동기)
            table_name: 테이블명
            
        Returns:
            bool: 갱신 성공 여부
        """
        try:
            logger.info(f"📊 {table_name} 테이블 관련 MV 갱신 시작...")
            
            # sales_records 테이블 업데이트 시
            if table_name in ['sales_records', 'sales_record']:
                # 거래처 성과 MV 갱신
                await MVRefreshService.refresh_customer_performance_mv(db)
                # 직원 성과 MV 갱신
                await MVRefreshService.refresh_employee_performance_mv(db)
                
            # customer_monthly_status 테이블 업데이트 시
            elif table_name in ['customer_monthly_status', 'customers']:
                # 거래처 성과 MV 갱신
                await MVRefreshService.refresh_customer_performance_mv(db)
                
            # employees 관련 테이블 업데이트 시
            elif table_name in ['employees', 'employee_info']:
                # 직원 성과 MV 갱신
                await MVRefreshService.refresh_employee_performance_mv(db)
                
            else:
                logger.info(f"ℹ️ {table_name} 테이블과 관련된 MV가 없습니다.")
                return True
            
            logger.info(f"✅ {table_name} 테이블 관련 MV 갱신 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ {table_name} 테이블 관련 MV 갱신 실패: {e}")
            return False

# 싱글톤 인스턴스
mv_refresh_service = MVRefreshService()