from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.schemas.employee_info import (
    EmployeeInfoResponse,
    EmployeeInfoWithBranch,
    EmployeeInfoCreate,
    EmployeeInfoUpdate
)
from app.models.employee_info import EmployeeInfo
from app.models.branches import Branch
from app.models.employees import Employee
from app.services.utils.db import get_db
from app.routers.user_router import get_current_user
from app.schemas.employee import EmployeeInfo as CurrentUserInfo
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[EmployeeInfoWithBranch])
def get_employee_info_list(
    skip: int = Query(0, description="페이지네이션 오프셋"),
    limit: int = Query(100, description="페이지 크기"),
    branch_id: Optional[int] = Query(None, description="지점 ID로 필터링"),
    position: Optional[str] = Query(None, description="직급으로 필터링"),
    name: Optional[str] = Query(None, description="이름으로 검색"),
    approval_status: Optional[str] = Query(None, description="승인 상태로 필터링"),
    db: Session = Depends(get_db),
    current_user: CurrentUserInfo = Depends(get_current_user)
):
    """
    직원 정보 리스트를 반환합니다.
    
    필터링 옵션:
    - branch_id: 특정 지점의 직원만 조회
    - position: 특정 직급의 직원만 조회
    - name: 이름으로 검색 (부분 일치)
    - approval_status: 승인 상태로 필터링 (pending/approved/rejected)
    """
    try:
        query = db.query(EmployeeInfo).options(joinedload(EmployeeInfo.branch))
        
        # 필터링 적용
        if branch_id:
            query = query.filter(EmployeeInfo.branch_id == branch_id)
        if position:
            query = query.filter(EmployeeInfo.position == position)
        if name:
            query = query.filter(EmployeeInfo.name.ilike(f"%{name}%"))
        if approval_status:
            query = query.filter(EmployeeInfo.approval_status == approval_status)
        
        # 승인된 항목만 보이도록 (관리자는 모두 볼 수 있음)
        if current_user.role != "admin":
            query = query.filter(EmployeeInfo.approval_status == "approved")
        
        # 페이지네이션 적용
        employee_infos = query.offset(skip).limit(limit).all()
        
        # 응답 데이터 구성
        result = []
        for emp_info in employee_infos:
            emp_dict = {
                "employee_info_id": emp_info.employee_info_id,
                "employee_id": emp_info.employee_id,
                "name": emp_info.name,
                "employee_number": emp_info.employee_number,
                "position": emp_info.position,
                "branch_id": emp_info.branch_id,
                "contact_number": emp_info.contact_number,
                "base_salary": emp_info.base_salary,
                "incentive_pay": emp_info.incentive_pay,
                "avg_monthly_budget": emp_info.avg_monthly_budget,
                "latest_evaluation": emp_info.latest_evaluation,
                "responsibilities": emp_info.responsibilities,
                "is_auto_created": emp_info.is_auto_created,
                "approval_status": emp_info.approval_status,
                "approved_by": emp_info.approved_by,
                "approved_at": emp_info.approved_at,
                "approval_notes": emp_info.approval_notes,
                "created_at": emp_info.created_at,
                "updated_at": emp_info.updated_at,
                "branch_name": emp_info.branch.branch_name if emp_info.branch else None,
                "headquarters": emp_info.branch.headquarters if emp_info.branch else None,
                "department": emp_info.branch.department if emp_info.branch else None
            }
            result.append(emp_dict)
        
        logger.info(f"직원 정보 리스트 조회 성공: {len(result)}건")
        return result
        
    except Exception as e:
        logger.error(f"직원 정보 리스트 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"직원 정보 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{employee_info_id}", response_model=EmployeeInfoWithBranch)
def get_employee_info_detail(
    employee_info_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserInfo = Depends(get_current_user)
):
    """
    특정 직원의 상세 정보를 반환합니다.
    
    Parameters:
    - employee_info_id: 조회할 직원 정보 ID
    """
    try:
        # 직원 정보 조회 (지점 정보 포함)
        emp_info = db.query(EmployeeInfo).options(
            joinedload(EmployeeInfo.branch)
        ).filter(
            EmployeeInfo.employee_info_id == employee_info_id
        ).first()
        
        if not emp_info:
            raise HTTPException(status_code=404, detail="직원 정보를 찾을 수 없습니다.")
        
        # 권한 확인 (관리자가 아닌 경우 승인된 정보만 볼 수 있음)
        if current_user.role != "admin" and emp_info.approval_status != "approved":
            raise HTTPException(status_code=403, detail="승인되지 않은 직원 정보입니다.")
        
        # 응답 데이터 구성
        result = {
            "employee_info_id": emp_info.employee_info_id,
            "employee_id": emp_info.employee_id,
            "name": emp_info.name,
            "employee_number": emp_info.employee_number,
            "position": emp_info.position,
            "branch_id": emp_info.branch_id,
            "contact_number": emp_info.contact_number,
            "base_salary": emp_info.base_salary,
            "incentive_pay": emp_info.incentive_pay,
            "avg_monthly_budget": emp_info.avg_monthly_budget,
            "latest_evaluation": emp_info.latest_evaluation,
            "responsibilities": emp_info.responsibilities,
            "is_auto_created": emp_info.is_auto_created,
            "approval_status": emp_info.approval_status,
            "approved_by": emp_info.approved_by,
            "approved_at": emp_info.approved_at,
            "approval_notes": emp_info.approval_notes,
            "created_at": emp_info.created_at,
            "updated_at": emp_info.updated_at,
            "branch_name": emp_info.branch.branch_name if emp_info.branch else None,
            "headquarters": emp_info.branch.headquarters if emp_info.branch else None,
            "department": emp_info.branch.department if emp_info.branch else None
        }
        
        logger.info(f"직원 정보 상세 조회 성공: ID={employee_info_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"직원 정보 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"직원 정보 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/by-employee/{employee_id}", response_model=Optional[EmployeeInfoWithBranch])
def get_employee_info_by_employee_id(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUserInfo = Depends(get_current_user)
):
    """
    직원 계정 ID로 직원 정보를 조회합니다.
    
    Parameters:
    - employee_id: 직원 계정 ID (employees 테이블의 employee_id)
    """
    try:
        # 직원 정보 조회
        emp_info = db.query(EmployeeInfo).options(
            joinedload(EmployeeInfo.branch)
        ).filter(
            EmployeeInfo.employee_id == employee_id
        ).first()
        
        if not emp_info:
            return None
        
        # 권한 확인
        if current_user.role != "admin" and emp_info.approval_status != "approved":
            raise HTTPException(status_code=403, detail="승인되지 않은 직원 정보입니다.")
        
        # 응답 데이터 구성
        result = {
            "employee_info_id": emp_info.employee_info_id,
            "employee_id": emp_info.employee_id,
            "name": emp_info.name,
            "employee_number": emp_info.employee_number,
            "position": emp_info.position,
            "branch_id": emp_info.branch_id,
            "contact_number": emp_info.contact_number,
            "base_salary": emp_info.base_salary,
            "incentive_pay": emp_info.incentive_pay,
            "avg_monthly_budget": emp_info.avg_monthly_budget,
            "latest_evaluation": emp_info.latest_evaluation,
            "responsibilities": emp_info.responsibilities,
            "is_auto_created": emp_info.is_auto_created,
            "approval_status": emp_info.approval_status,
            "approved_by": emp_info.approved_by,
            "approved_at": emp_info.approved_at,
            "approval_notes": emp_info.approval_notes,
            "created_at": emp_info.created_at,
            "updated_at": emp_info.updated_at,
            "branch_name": emp_info.branch.branch_name if emp_info.branch else None,
            "headquarters": emp_info.branch.headquarters if emp_info.branch else None,
            "department": emp_info.branch.department if emp_info.branch else None
        }
        
        logger.info(f"직원 계정 ID로 정보 조회 성공: employee_id={employee_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"직원 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"직원 정보 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/search/by-name", response_model=List[EmployeeInfoWithBranch])
def search_employee_by_name(
    name: str = Query(..., description="검색할 직원 이름"),
    db: Session = Depends(get_db),
    current_user: CurrentUserInfo = Depends(get_current_user)
):
    """
    이름으로 직원을 검색합니다. (부분 일치)
    
    Parameters:
    - name: 검색할 직원 이름
    """
    try:
        query = db.query(EmployeeInfo).options(joinedload(EmployeeInfo.branch))
        
        # 이름으로 검색 (부분 일치)
        query = query.filter(EmployeeInfo.name.ilike(f"%{name}%"))
        
        # 권한에 따른 필터링
        if current_user.role != "admin":
            query = query.filter(EmployeeInfo.approval_status == "approved")
        
        employee_infos = query.all()
        
        if not employee_infos:
            return []
        
        # 응답 데이터 구성
        result = []
        for emp_info in employee_infos:
            emp_dict = {
                "employee_info_id": emp_info.employee_info_id,
                "employee_id": emp_info.employee_id,
                "name": emp_info.name,
                "employee_number": emp_info.employee_number,
                "position": emp_info.position,
                "branch_id": emp_info.branch_id,
                "contact_number": emp_info.contact_number,
                "base_salary": emp_info.base_salary,
                "incentive_pay": emp_info.incentive_pay,
                "avg_monthly_budget": emp_info.avg_monthly_budget,
                "latest_evaluation": emp_info.latest_evaluation,
                "responsibilities": emp_info.responsibilities,
                "is_auto_created": emp_info.is_auto_created,
                "approval_status": emp_info.approval_status,
                "approved_by": emp_info.approved_by,
                "approved_at": emp_info.approved_at,
                "approval_notes": emp_info.approval_notes,
                "created_at": emp_info.created_at,
                "updated_at": emp_info.updated_at,
                "branch_name": emp_info.branch.branch_name if emp_info.branch else None,
                "headquarters": emp_info.branch.headquarters if emp_info.branch else None,
                "department": emp_info.branch.department if emp_info.branch else None
            }
            result.append(emp_dict)
        
        logger.info(f"이름 검색 성공: '{name}' - {len(result)}건")
        return result
        
    except Exception as e:
        logger.error(f"직원 이름 검색 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"직원 검색 중 오류가 발생했습니다: {str(e)}")