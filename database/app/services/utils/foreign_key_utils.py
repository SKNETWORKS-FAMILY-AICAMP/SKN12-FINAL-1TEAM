"""
외래키 조회를 위한 공통 유틸리티 함수들
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.employee_info import EmployeeInfo
from app.models.customers import Customer
from app.models.products import Product

logger = logging.getLogger(__name__)


async def get_customer_id(session: AsyncSession, customer_name: str) -> int:
    """고객 ID를 가져오기 (기존 고객만 조회, 생성하지 않음)"""
    try:
        if not customer_name or customer_name == 'nan' or customer_name == '':
            raise ValueError("고객명이 유효하지 않습니다.")
        
        # 기존 고객만 조회 (의존성 순서에 따라 customers가 먼저 저장되어 있어야 함)
        result = await session.execute(
            select(Customer).filter(Customer.customer_name == customer_name)
        )
        existing_customer = result.scalar_one_or_none()
        
        if existing_customer:
            return existing_customer.customer_id
        else:
            # 고객이 존재하지 않으면 에러 발생 (의존성 순서 위반)
            raise ValueError(f"고객 '{customer_name}'이 customers 테이블에 존재하지 않습니다. customers 테이블을 먼저 처리해야 합니다.")
            
    except Exception as e:
        logger.error(f"고객 ID 조회 중 오류: {e}")
        raise ValueError(f"고객 ID 조회 실패: {str(e)}")


async def get_employee_id_by_number(session: AsyncSession, employee_number: str) -> int:
    """사번으로 직원 ID를 가져오기 (기존 직원만 조회, 생성하지 않음)"""
    try:
        if not employee_number or employee_number == 'nan':
            raise ValueError("사번이 필수입니다.")
        
        # 기존 직원만 조회 (의존성 순서에 따라 employee_info가 먼저 저장되어 있어야 함)
        result = await session.execute(
            select(EmployeeInfo).filter(EmployeeInfo.employee_number == employee_number)
        )
        existing_employee = result.scalar_one_or_none()
        
        if existing_employee:
            return existing_employee.employee_info_id
        else:
            # 직원이 존재하지 않으면 에러 발생 (의존성 순서 위반)
            raise ValueError(f"사번 '{employee_number}'이 employee_info 테이블에 존재하지 않습니다. employee_info 테이블을 먼저 처리해야 합니다.")
            
    except Exception as e:
        logger.error(f"직원 ID 조회 중 오류: {e}")
        raise ValueError(f"직원 ID 조회 실패: {str(e)}")


async def get_employee_id_by_name(session: AsyncSession, employee_name: str) -> int:
    """직원명으로 직원 ID를 가져오기 (기존 직원만 조회, 생성하지 않음)"""
    try:
        if not employee_name or employee_name == 'nan':
            raise ValueError("직원명이 필수입니다.")
        
        # 기존 직원만 조회 (의존성 순서에 따라 employee_info가 먼저 저장되어 있어야 함)
        result = await session.execute(
            select(EmployeeInfo).filter(EmployeeInfo.name == employee_name)
        )
        existing_employee = result.scalar_one_or_none()
        
        if existing_employee:
            return existing_employee.employee_info_id
        else:
            # 직원이 존재하지 않으면 에러 발생 (의존성 순서 위반)
            raise ValueError(f"직원명 '{employee_name}'이 employee_info 테이블에 존재하지 않습니다. employee_info 테이블을 먼저 처리해야 합니다.")
            
    except Exception as e:
        logger.error(f"직원 ID 조회 중 오류: {e}")
        raise ValueError(f"직원 ID 조회 실패: {str(e)}")


async def get_employee_id(session: AsyncSession, employee_name: Optional[str] = None, employee_number: Optional[str] = None) -> int:
    """직원 ID를 가져오기 (사번 우선, 없으면 직원명으로 조회)"""
    if employee_number and employee_number != 'nan':
        return await get_employee_id_by_number(session, employee_number)
    elif employee_name and employee_name != 'nan':
        return await get_employee_id_by_name(session, employee_name)
    else:
        raise ValueError("직원명 또는 사번이 필수입니다.")


async def get_product_id(session: AsyncSession, product_name: str) -> Optional[int]:
    """제품 ID를 가져오기 (기존 제품만 조회, 생성하지 않음)"""
    try:
        if not product_name or product_name == 'nan':
            return None
        
        # 기존 제품만 조회 (의존성 순서에 따라 products가 먼저 저장되어 있어야 함)
        result = await session.execute(
            select(Product).filter(Product.product_name == product_name)
        )
        existing_product = result.scalar_one_or_none()
        
        if existing_product:
            return existing_product.product_id
        else:
            # 제품이 존재하지 않으면 에러 발생 (의존성 순서 위반)
            raise ValueError(f"제품 '{product_name}'이 products 테이블에 존재하지 않습니다. products 테이블을 먼저 처리해야 합니다.")
            
    except Exception as e:
        logger.error(f"제품 ID 조회 중 오류: {e}")
        return None
