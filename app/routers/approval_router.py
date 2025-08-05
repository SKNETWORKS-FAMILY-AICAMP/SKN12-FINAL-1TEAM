"""
승인 시스템 라우터
자동 생성된 엔티티에 대한 승인/거부 관리
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from app.services.utils.db import get_db
from app.routers.user_router import get_current_admin_user
from app.models.employee_info import EmployeeInfo
from app.models.customers import Customer
from app.models.products import Product
from app.models.employees import Employee
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/pending")
def get_pending_approvals(
    entity_type: Optional[str] = Query(None, description="엔티티 타입 (employee, customer, product)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    승인 대기 중인 엔티티 목록 조회
    
    Args:
        entity_type: 엔티티 타입 필터
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        List: 승인 대기 중인 엔티티 목록
    """
    try:
        pending_items = []
        
        if entity_type is None or entity_type == 'employee':
            # 승인 대기 중인 직원 조회
            pending_employees = db.query(EmployeeInfo).filter(
                EmployeeInfo.is_auto_created == True,
                EmployeeInfo.approval_status == 'pending'
            ).all()
            
            for emp in pending_employees:
                pending_items.append({
                    'entity_type': 'employee',
                    'entity_id': emp.employee_info_id,
                    'name': emp.name,
                    'employee_number': emp.employee_number,
                    'team': emp.team,
                    'position': emp.position,
                    'created_at': emp.created_at.isoformat() if emp.created_at else None,
                    'details': {
                        'business_unit': emp.business_unit,
                        'branch': emp.branch,
                        'contact_number': emp.contact_number,
                        'base_salary': emp.base_salary,
                        'incentive_pay': emp.incentive_pay,
                        'avg_monthly_budget': emp.avg_monthly_budget,
                        'latest_evaluation': emp.latest_evaluation,
                        'responsibilities': emp.responsibilities
                    }
                })
        
        if entity_type is None or entity_type == 'customer':
            # 승인 대기 중인 고객 조회
            pending_customers = db.query(Customer).filter(
                Customer.is_auto_created == True,
                Customer.approval_status == 'pending'
            ).all()
            
            for cust in pending_customers:
                pending_items.append({
                    'entity_type': 'customer',
                    'entity_id': cust.customer_id,
                    'name': cust.customer_name,
                    'address': cust.address,
                    'doctor_name': cust.doctor_name,
                    'total_patients': cust.total_patients,
                    'customer_grade': cust.customer_grade,
                    'created_at': cust.created_at.isoformat() if cust.created_at else None,
                    'details': {
                        'notes': cust.notes
                    }
                })
        
        if entity_type is None or entity_type == 'product':
            # 승인 대기 중인 제품 조회
            pending_products = db.query(Product).filter(
                Product.is_auto_created == True,
                Product.approval_status == 'pending'
            ).all()
            
            for prod in pending_products:
                pending_items.append({
                    'entity_type': 'product',
                    'entity_id': prod.product_id,
                    'name': prod.product_name,
                    'description': prod.description,
                    'category': prod.category,
                    'is_active': prod.is_active,
                    'created_at': prod.created_at.isoformat() if prod.created_at else None,
                    'details': {
                        'approval_notes': prod.approval_notes
                    }
                })
        
        logger.info(f"승인 대기 목록 조회 완료: {len(pending_items)}건")
        return {
            'total_count': len(pending_items),
            'items': pending_items
        }
        
    except Exception as e:
        logger.error(f"승인 대기 목록 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"승인 대기 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/approve/{entity_type}/{entity_id}")
def approve_entity(
    entity_type: str,
    entity_id: int,
    notes: Optional[str] = Query(None, description="승인 메모"),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    엔티티 승인
    
    Args:
        entity_type: 엔티티 타입 (employee, customer, product)
        entity_id: 엔티티 ID
        notes: 승인 메모
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 승인 결과
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        if entity_type == 'employee':
            entity = db.query(EmployeeInfo).filter(
                EmployeeInfo.employee_info_id == entity_id,
                EmployeeInfo.approval_status == 'pending'
            ).first()
        elif entity_type == 'customer':
            entity = db.query(Customer).filter(
                Customer.customer_id == entity_id,
                Customer.approval_status == 'pending'
            ).first()
        elif entity_type == 'product':
            entity = db.query(Product).filter(
                Product.product_id == entity_id,
                Product.approval_status == 'pending'
            ).first()
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 엔티티 타입입니다")
        
        if not entity:
            raise HTTPException(status_code=404, detail="승인 대기 중인 엔티티를 찾을 수 없습니다")
        
        # 승인 처리
        entity.approval_status = 'approved'
        entity.approved_by = user.employee_id
        entity.approved_at = current_time
        entity.approval_notes = notes
        
        db.commit()
        
        logger.info(f"엔티티 승인 완료: {entity_type} ID {entity_id}")
        return {
            'success': True,
            'message': f'{entity_type} 승인 완료',
            'entity_type': entity_type,
            'entity_id': entity_id,
            'approved_by': user.employee_id,
            'approved_at': current_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"엔티티 승인 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"엔티티 승인 중 오류가 발생했습니다: {str(e)}")

@router.post("/reject/{entity_type}/{entity_id}")
def reject_entity(
    entity_type: str,
    entity_id: int,
    notes: str = Query(..., description="거부 사유"),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    엔티티 거부
    
    Args:
        entity_type: 엔티티 타입 (employee, customer, product)
        entity_id: 엔티티 ID
        notes: 거부 사유
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 거부 결과
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        if entity_type == 'employee':
            entity = db.query(EmployeeInfo).filter(
                EmployeeInfo.employee_info_id == entity_id,
                EmployeeInfo.approval_status == 'pending'
            ).first()
        elif entity_type == 'customer':
            entity = db.query(Customer).filter(
                Customer.customer_id == entity_id,
                Customer.approval_status == 'pending'
            ).first()
        elif entity_type == 'product':
            entity = db.query(Product).filter(
                Product.product_id == entity_id,
                Product.approval_status == 'pending'
            ).first()
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 엔티티 타입입니다")
        
        if not entity:
            raise HTTPException(status_code=404, detail="승인 대기 중인 엔티티를 찾을 수 없습니다")
        
        # 거부 처리
        entity.approval_status = 'rejected'
        entity.approved_by = user.employee_id
        entity.approved_at = current_time
        entity.approval_notes = notes
        
        db.commit()
        
        logger.info(f"엔티티 거부 완료: {entity_type} ID {entity_id}")
        return {
            'success': True,
            'message': f'{entity_type} 거부 완료',
            'entity_type': entity_type,
            'entity_id': entity_id,
            'rejected_by': user.employee_id,
            'rejected_at': current_time.isoformat(),
            'rejection_reason': notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"엔티티 거부 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"엔티티 거부 중 오류가 발생했습니다: {str(e)}")

@router.get("/stats")
def get_approval_stats(
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    승인 시스템 통계 조회
    
    Args:
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 승인 시스템 통계
    """
    try:
        # 트랜잭션 격리 레벨 설정으로 락 경합 방지
        db.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
        
        # 직원 승인 통계
        employee_pending = db.query(EmployeeInfo).filter(
            EmployeeInfo.is_auto_created == True,
            EmployeeInfo.approval_status == 'pending'
        ).count()
        
        employee_approved = db.query(EmployeeInfo).filter(
            EmployeeInfo.is_auto_created == True,
            EmployeeInfo.approval_status == 'approved'
        ).count()
        
        employee_rejected = db.query(EmployeeInfo).filter(
            EmployeeInfo.is_auto_created == True,
            EmployeeInfo.approval_status == 'rejected'
        ).count()
        
        # 고객 승인 통계
        customer_pending = db.query(Customer).filter(
            Customer.is_auto_created == True,
            Customer.approval_status == 'pending'
        ).count()
        
        customer_approved = db.query(Customer).filter(
            Customer.is_auto_created == True,
            Customer.approval_status == 'approved'
        ).count()
        
        customer_rejected = db.query(Customer).filter(
            Customer.is_auto_created == True,
            Customer.approval_status == 'rejected'
        ).count()
        
        # 제품 승인 통계
        product_pending = db.query(Product).filter(
            Product.is_auto_created == True,
            Product.approval_status == 'pending'
        ).count()
        
        product_approved = db.query(Product).filter(
            Product.is_auto_created == True,
            Product.approval_status == 'approved'
        ).count()
        
        product_rejected = db.query(Product).filter(
            Product.is_auto_created == True,
            Product.approval_status == 'rejected'
        ).count()
        
        return {
            'employee': {
                'pending': employee_pending,
                'approved': employee_approved,
                'rejected': employee_rejected,
                'total': employee_pending + employee_approved + employee_rejected
            },
            'customer': {
                'pending': customer_pending,
                'approved': customer_approved,
                'rejected': customer_rejected,
                'total': customer_pending + customer_approved + customer_rejected
            },
            'product': {
                'pending': product_pending,
                'approved': product_approved,
                'rejected': product_rejected,
                'total': product_pending + product_approved + product_rejected
            }
        }
        
    except Exception as e:
        logger.error(f"승인 통계 조회 중 오류: {e}")
        # 트랜잭션 롤백 후 기본값 반환
        try:
            db.rollback()
        except:
            pass
        return {
            'employee': {
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'total': 0
            },
            'customer': {
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'total': 0
            },
            'product': {
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'total': 0
            }
        } 