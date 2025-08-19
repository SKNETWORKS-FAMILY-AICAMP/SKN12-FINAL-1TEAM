"""
지점 정보 관련 라우터
지점 정보 조회 및 검색 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from pydantic import BaseModel

from app.services.utils.db import get_db
from app.routers.user_router import get_current_user
from app.models.branches import Branch
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class BranchInfo(BaseModel):
    """지점 정보 스키마"""
    branch_id: int
    headquarters: str
    department: str
    branch_name: str
    contact_number: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[BranchInfo])
def get_all_branches(
    skip: int = Query(0, description="건너뛸 항목 수"),
    limit: int = Query(100, description="조회할 최대 항목 수"),
    status: Optional[str] = Query(None, description="상태 필터 (active/inactive)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[BranchInfo]:
    """
    모든 지점 정보 목록 조회
    
    Args:
        skip: 건너뛸 항목 수 (페이지네이션용)
        limit: 조회할 최대 항목 수
        status: 상태 필터 (active/inactive)
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        List[BranchInfo]: 지점 정보 목록
    """
    try:
        query = db.query(Branch)
        
        # 상태 필터 적용
        if status:
            query = query.filter(Branch.status == status)
        
        branches = query.offset(skip).limit(limit).all()
        
        logger.info(f"지점 목록 조회 완료: {len(branches)}개")
        
        return [BranchInfo.from_orm(branch) for branch in branches]
        
    except Exception as e:
        logger.error(f"지점 목록 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"지점 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/search", response_model=Dict[str, Any])
def search_branch_by_name(
    name: str = Query(..., description="검색할 지점명"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    지점명으로 지점 정보 검색
    
    Args:
        name: 검색할 지점명 (부분 일치 검색)
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 검색 결과
        {
            "search_term": "검색어",
            "count": 1,
            "results": [
                {
                    "branch_id": 1,
                    "branch_name": "서울지점",
                    "headquarters": "수도권본부",
                    "department": "영업1부",
                    "status": "active"
                }
            ]
        }
    """
    try:
        # 부분 일치 검색 (대소문자 구분 없음)
        branches = db.query(Branch).filter(
            Branch.branch_name.ilike(f"%{name}%")
        ).all()
        
        if not branches:
            logger.info(f"지점명 '{name}' 검색 결과 없음")
            return {
                "search_term": name,
                "count": 0,
                "results": []
            }
        
        results = []
        for branch in branches:
            results.append({
                "branch_id": branch.branch_id,
                "branch_name": branch.branch_name,
                "headquarters": branch.headquarters,
                "department": branch.department,
                "status": branch.status,
                "contact_number": branch.contact_number
            })
        
        logger.info(f"지점명 '{name}' 검색 완료: {len(results)}개 발견")
        
        return {
            "search_term": name,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"지점명 검색 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"지점명 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/by-headquarters", response_model=List[BranchInfo])
def get_branches_by_headquarters(
    headquarters: str = Query(..., description="본부명"),
    status: Optional[str] = Query(None, description="상태 필터 (active/inactive)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[BranchInfo]:
    """
    본부별 지점 목록 조회
    
    Args:
        headquarters: 본부명
        status: 상태 필터 (active/inactive)
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        List[BranchInfo]: 해당 본부의 지점 목록
    """
    try:
        query = db.query(Branch).filter(Branch.headquarters == headquarters)
        
        # 상태 필터 적용
        if status:
            query = query.filter(Branch.status == status)
        
        branches = query.all()
        
        if not branches:
            logger.info(f"본부 '{headquarters}' 지점 없음")
            return []
        
        logger.info(f"본부 '{headquarters}' 지점 조회 완료: {len(branches)}개")
        
        return [BranchInfo.from_orm(branch) for branch in branches]
        
    except Exception as e:
        logger.error(f"본부별 지점 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"본부별 지점 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/by-department", response_model=List[BranchInfo])
def get_branches_by_department(
    department: str = Query(..., description="부서명"),
    headquarters: Optional[str] = Query(None, description="본부명 (선택사항)"),
    status: Optional[str] = Query(None, description="상태 필터 (active/inactive)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[BranchInfo]:
    """
    부서별 지점 목록 조회
    
    Args:
        department: 부서명
        headquarters: 본부명 (선택사항)
        status: 상태 필터 (active/inactive)
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        List[BranchInfo]: 해당 부서의 지점 목록
    """
    try:
        query = db.query(Branch).filter(Branch.department == department)
        
        # 본부 필터 적용
        if headquarters:
            query = query.filter(Branch.headquarters == headquarters)
        
        # 상태 필터 적용
        if status:
            query = query.filter(Branch.status == status)
        
        branches = query.all()
        
        if not branches:
            logger.info(f"부서 '{department}' 지점 없음")
            return []
        
        logger.info(f"부서 '{department}' 지점 조회 완료: {len(branches)}개")
        
        return [BranchInfo.from_orm(branch) for branch in branches]
        
    except Exception as e:
        logger.error(f"부서별 지점 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"부서별 지점 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/statistics", response_model=Dict[str, Any])
def get_branch_statistics(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    지점 통계 정보 조회
    
    Args:
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 지점 통계 정보
        {
            "total_branches": 100,
            "active_branches": 90,
            "inactive_branches": 10,
            "by_headquarters": {
                "수도권본부": 30,
                "경기본부": 25,
                ...
            },
            "by_department": {
                "영업1부": 20,
                "영업2부": 15,
                ...
            }
        }
    """
    try:
        # 전체 지점 수
        total_branches = db.query(Branch).count()
        
        # 활성/비활성 지점 수
        active_branches = db.query(Branch).filter(Branch.status == "active").count()
        inactive_branches = db.query(Branch).filter(Branch.status == "inactive").count()
        
        # 본부별 지점 수
        headquarters_stats = {}
        headquarters_list = db.query(Branch.headquarters).distinct().all()
        for (hq,) in headquarters_list:
            if hq:
                count = db.query(Branch).filter(Branch.headquarters == hq).count()
                headquarters_stats[hq] = count
        
        # 부서별 지점 수
        department_stats = {}
        department_list = db.query(Branch.department).distinct().all()
        for (dept,) in department_list:
            if dept:
                count = db.query(Branch).filter(Branch.department == dept).count()
                department_stats[dept] = count
        
        result = {
            "total_branches": total_branches,
            "active_branches": active_branches,
            "inactive_branches": inactive_branches,
            "by_headquarters": headquarters_stats,
            "by_department": department_stats
        }
        
        logger.info("지점 통계 조회 완료")
        
        return result
        
    except Exception as e:
        logger.error(f"지점 통계 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"지점 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{branch_id}", response_model=BranchInfo)
def get_branch_detail(
    branch_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> BranchInfo:
    """
    특정 지점의 상세 정보 조회
    
    Args:
        branch_id: 지점 ID
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        BranchInfo: 지점 상세 정보
    """
    try:
        branch = db.query(Branch).filter(
            Branch.branch_id == branch_id
        ).first()
        
        if not branch:
            raise HTTPException(
                status_code=404,
                detail=f"지점 ID {branch_id}를 찾을 수 없습니다."
            )
        
        logger.info(f"지점 상세 정보 조회 완료: ID={branch_id}")
        
        return BranchInfo.from_orm(branch)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지점 상세 정보 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"지점 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )