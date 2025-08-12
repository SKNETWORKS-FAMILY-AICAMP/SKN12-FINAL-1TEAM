import pandas as pd
import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import os
import random  # 랜덤 생성을 위해 추가

class EmployeeDBManager:
    """직원 실적 및 목표 데이터베이스 관리 클래스"""
    
    def __init__(self):
        # 프로젝트 루트에서의 상대 경로 설정
        # 현재 파일: backend/app/services/employee_agent/db_manager.py
        # 프로젝트 루트까지: 5번의 parent 필요
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        self.performance_db_path = base_dir / "database" / "relationdb" / "performance_swest_sua.sqlite"
        self.target_db_path = base_dir / "database" / "relationdb" / "joonpharma_target.sqlite"
        
        # 경로 문제 해결을 위한 대안 경로 체크
        if not self.performance_db_path.exists():
            # 현재 작업 디렉토리 기준으로 다시 시도
            cwd_base = Path.cwd()
            alt_performance_path = cwd_base / "database" / "relationdb" / "performance_swest_sua.sqlite"
            alt_target_path = cwd_base / "database" / "relationdb" / "joonpharma_target.sqlite"
            
            if alt_performance_path.exists():
                self.performance_db_path = alt_performance_path
                self.target_db_path = alt_target_path
                self.use_dummy_data = False
            else:
                self.use_dummy_data = True
        else:
            self.use_dummy_data = False
    
    def get_connection(self, db_type: str) -> sqlite3.Connection:
        """데이터베이스 연결을 반환합니다."""
        if db_type == "performance":
            db_path = self.performance_db_path
        elif db_type == "target":
            db_path = self.target_db_path
        else:
            raise ValueError("db_type은 'performance' 또는 'target'이어야 합니다.")
        
        # 파일 존재 확인
        if not db_path.exists():
            raise FileNotFoundError(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
        
        return sqlite3.connect(str(db_path))
    
    def get_available_employees(self) -> List[str]:
        """사용 가능한 직원 목록을 반환합니다."""
        if hasattr(self, 'use_dummy_data') and self.use_dummy_data:
            return ["최수아", "김영희", "박철수", "조시현", "이민수"]
        
        try:
            with self.get_connection("performance") as conn:
                query = "SELECT DISTINCT 담당자 FROM sales_performance WHERE 담당자 IS NOT NULL"
                df = pd.read_sql_query(query, conn)
                return df['담당자'].tolist()
        except Exception as e:
            print(f"직원 목록 조회 오류: {e}")
            return ["최수아", "김영희", "박철수", "조시현", "이민수"]
    
    def get_employee_performance_data(self, employee_name: str = None,
                                     start_period: str = None,
                                     end_period: str = None) -> pd.DataFrame:
        """직원의 실적 데이터를 조회합니다."""
        try:
            with self.get_connection("performance") as conn:
                # 기본 쿼리 (실제 테이블 구조에 맞게 수정)
                base_query = "SELECT * FROM sales_performance WHERE 1=1"
                params = []
                
                # 담당자 필터링
                if employee_name:
                    base_query += " AND 담당자 = ?"
                    params.append(employee_name)
                
                base_query += " ORDER BY 담당자, 품목"
                
                df = pd.read_sql_query(base_query, conn, params=params)
                return df
                
        except Exception as e:
            print(f"실적 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_employee_target_data(self, employee_name: str = None,
                                start_period: str = None,
                                end_period: str = None) -> pd.DataFrame:
        """직원의 목표 데이터를 조회합니다."""
        try:
            with self.get_connection("target") as conn:
                # 기본 쿼리: 지점, 담당자, 년월, 목표 칼럼만 사용
                base_query = "SELECT 지점, 담당자, 년월, 목표 FROM monthly_target WHERE 1=1"
                params = []
                
                # 담당자 필터링
                if employee_name:
                    base_query += " AND 담당자 = ?"
                    params.append(employee_name)
                
                # 기간 필터링
                if start_period:
                    base_query += " AND 년월 >= ?"
                    params.append(int(start_period))
                
                if end_period:
                    base_query += " AND 년월 <= ?"
                    params.append(int(end_period))
                
                base_query += " ORDER BY 담당자, 년월"
                
                df = pd.read_sql_query(base_query, conn, params=params)
                return df
                
        except Exception as e:
            print(f"목표 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_performance_summary(self, employee_name: str, 
                              start_period: str, end_period: str) -> Dict[str, Any]:
        """직원의 실적 요약을 반환합니다."""
        if hasattr(self, 'use_dummy_data') and self.use_dummy_data:
            return self._get_dummy_performance_data(employee_name, start_period, end_period)
        
        try:
            df = self.get_employee_performance_data(employee_name)
            
            # pandas boolean을 Python bool로 변환
            if bool(df.empty):
                # 실제 데이터가 없으면 더미 데이터 사용
                if hasattr(self, 'use_dummy_data') and self.use_dummy_data:
                    return self._get_dummy_performance_data(employee_name, start_period, end_period)
                else:
                    return {
                        "employee_name": employee_name,
                        "period": f"{start_period}~{end_period}",
                        "total_performance": 0,
                        "monthly_breakdown": [],
                        "product_breakdown": [],
                        "client_breakdown": []
                    }
            
            # 월별 컬럼 찾기 (202312, 202401 등)
            month_columns = [col for col in df.columns if col.isdigit() and len(col) == 6]
            
            if start_period and end_period:
                start_num = int(start_period)
                end_num = int(end_period)
                analysis_months = [col for col in month_columns if start_num <= int(col) <= end_num]
            else:
                analysis_months = month_columns
            
            print(f"[DATE] 분석 대상 월: {analysis_months}")
            
            # 총 실적 계산
            total_performance = 0
            monthly_breakdown = []
            product_breakdown = {}
            client_breakdown = {}
            
            for month in analysis_months:
                month_total = 0
                for idx, row in df.iterrows():
                    # pandas boolean을 Python bool로 변환
                    is_not_na = bool(pd.notna(row[month]))  # numpy.bool → bool 변환
                    value_check = bool(row[month] > 0) if is_not_na else False
                    
                    if is_not_na and value_check:
                        amount = float(row[month])
                        month_total += amount
                        
                        # 제품별 집계
                        product = row.get('품목', 'Unknown')
                        if product not in product_breakdown:
                            product_breakdown[product] = 0
                        product_breakdown[product] += amount
                        
                        # 거래처별 집계
                        client = row.get('ID', 'Unknown')
                        if client not in client_breakdown:
                            client_breakdown[client] = 0
                        client_breakdown[client] += amount
                
                if month_total > 0:
                    monthly_breakdown.append({
                        "month": month,
                        "amount": int(month_total)  # numpy 타입 방지
                    })
                    total_performance += month_total
            
            # 요청된 기간에 데이터가 없으면 더미 데이터 사용
            if total_performance == 0 and hasattr(self, 'use_dummy_data') and self.use_dummy_data:
                print(f"[INFO] '{employee_name}'의 {start_period}~{end_period} 기간 데이터가 없어서 더미 데이터를 사용합니다.")
                return self._get_dummy_performance_data(employee_name, start_period, end_period)
            
            # numpy 타입을 Python 기본 타입으로 변환
            product_list = [
                {"name": name, "amount": int(amount)} 
                for name, amount in sorted(product_breakdown.items(), key=lambda x: x[1], reverse=True)
            ]
            
            client_list = [
                {"name": name, "amount": int(amount)}
                for name, amount in sorted(client_breakdown.items(), key=lambda x: x[1], reverse=True)
            ]
            
            return {
                "employee_name": employee_name,
                "period": f"{start_period}~{end_period}",
                "total_performance": int(total_performance),  # numpy 타입 방지
                "monthly_breakdown": monthly_breakdown,
                "product_breakdown": product_list,
                "client_breakdown": client_list
            }
            
        except Exception as e:
            print(f"실적 요약 계산 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                "employee_name": employee_name,
                "period": f"{start_period}~{end_period}",
                "total_performance": 0,
                "monthly_breakdown": [],
                "product_breakdown": [],
                "client_breakdown": []
            }
    
    def _get_dummy_performance_data(self, employee_name: str, start_period: str, end_period: str) -> Dict[str, Any]:
        """더미 실적 데이터를 생성합니다."""
        # 더미 월별 데이터 생성
        monthly_data = []
        total_amount = 0
        
        # 요청된 기간에 맞는 월별 데이터 생성
        periods = self._generate_period_list(start_period, end_period)
        
        # 직원별로 다른 시드 설정 (같은 직원은 같은 랜덤 패턴)
        random.seed(hash(employee_name))
        
        for i, period in enumerate(periods):
            # 랜덤 실적 생성 (1,000만원 ~ 3,000만원 범위)
            base_amount = random.randint(10000000, 30000000)
            # 월별 점진적 증가 패턴 + 랜덤 변동
            growth_factor = 1.0 + (i * 0.1) + random.uniform(-0.2, 0.2)
            amount = int(base_amount * growth_factor)
            
            monthly_data.append({
                "month": period,
                "amount": amount,
                "count": random.randint(10, 30)  # 랜덤 거래 건수
            })
            total_amount += amount
        
        # 랜덤 제품별 분포
        products = ["제품A", "제품B", "제품C", "제품D", "제품E"]
        product_breakdown = []
        remaining_amount = total_amount
        
        for i, product in enumerate(products[:-1]):  # 마지막 제품 제외
            if remaining_amount > 0:
                # 랜덤 비율 (10% ~ 40%)
                ratio = random.uniform(0.1, 0.4)
                amount = int(total_amount * ratio)
                product_breakdown.append({"name": product, "amount": amount})
                remaining_amount -= amount
        
        # 남은 금액을 마지막 제품에 할당
        if remaining_amount > 0:
            product_breakdown.append({"name": products[-1], "amount": remaining_amount})
        
        # 랜덤 거래처별 분포
        clients = ["병원A", "병원B", "병원C", "병원D", "병원E", "기타"]
        client_breakdown = []
        remaining_amount = total_amount
        
        for i, client in enumerate(clients[:-1]):  # 마지막 거래처 제외
            if remaining_amount > 0:
                # 랜덤 비율 (5% ~ 35%)
                ratio = random.uniform(0.05, 0.35)
                amount = int(total_amount * ratio)
                client_breakdown.append({"name": client, "amount": amount})
                remaining_amount -= amount
        
        # 남은 금액을 마지막 거래처에 할당
        if remaining_amount > 0:
            client_breakdown.append({"name": clients[-1], "amount": remaining_amount})
        
        return {
            "employee_name": employee_name,
            "period": f"{start_period}~{end_period}",
            "total_performance": total_amount,
            "monthly_breakdown": monthly_data,
            "product_breakdown": product_breakdown,
            "client_breakdown": client_breakdown
        }
    
    def _generate_period_list(self, start_period: str, end_period: str) -> List[str]:
        """시작 기간부터 종료 기간까지의 월별 기간 리스트를 생성합니다."""
        periods = []
        
        try:
            # YYYYMM 형식의 문자열을 정수로 변환
            start_year = int(start_period[:4])
            start_month = int(start_period[4:])
            end_year = int(end_period[:4])
            end_month = int(end_period[4:])
            
            current_year = start_year
            current_month = start_month
            
            while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
                period = f"{current_year}{current_month:02d}"
                periods.append(period)
                
                # 다음 월로 이동
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
                    
        except Exception as e:
            print(f"기간 리스트 생성 오류: {e}")
            # 오류 발생시 기본 기간 반환
            periods = ["202312", "202401", "202402", "202403"]
        
        return periods
    
    def _get_dummy_target_data(self, employee_name: str, start_period: str, end_period: str) -> Dict[str, Any]:
        """더미 목표 데이터를 생성합니다."""
        # 더미 실적 데이터 가져오기
        performance_data = self._get_dummy_performance_data(employee_name, start_period, end_period)
        total_performance = performance_data["total_performance"]
        
        # 목표는 실적의 90%로 설정 (도전적이지만 달성 가능한 목표)
        total_target = int(total_performance * 0.9)
        achievement_rate = (total_performance / total_target * 100) if total_target > 0 else 0
        gap_amount = total_performance - total_target
        
        # 평가 등급 결정
        if achievement_rate >= 120:
            evaluation = "목표 초과 달성"
            grade = "S"
        elif achievement_rate >= 100:
            evaluation = "목표 달성"
            grade = "A"
        elif achievement_rate >= 80:
            evaluation = "목표 근접"
            grade = "B"
        elif achievement_rate >= 60:
            evaluation = "목표 미달"
            grade = "C"
        else:
            evaluation = "목표 크게 미달"
            grade = "D"
        
        return {
            "total_performance": total_performance,
            "total_target": total_target,
            "achievement_rate": achievement_rate,
            "evaluation": evaluation,
            "grade": grade,
            "gap_amount": gap_amount
        }
    
    def _get_dummy_trend_data(self, employee_name: str, start_period: str, end_period: str) -> Dict[str, Any]:
        """더미 트렌드 데이터를 생성합니다."""
        # 직원별로 다른 시드 설정
        random.seed(hash(employee_name))
        
        # 랜덤 트렌드 생성
        trend_options = [
            ("상승", "강함", "실적이 지속적으로 증가하는 강한 상승 추세를 보입니다."),
            ("상승", "보통", "실적이 점진적으로 증가하는 추세를 보입니다."),
            ("안정", "강함", "실적이 매우 안정적으로 유지되고 있습니다."),
            ("안정", "보통", "실적이 안정적으로 유지되고 있습니다."),
            ("하락", "약함", "실적이 다소 감소하는 추세를 보입니다."),
            ("하락", "강함", "실적이 크게 감소하는 추세를 보입니다.")
        ]
        
        trend, strength, analysis = random.choice(trend_options)
        
        return {
            "trend": trend,
            "trend_strength": strength,
            "analysis": analysis
        }
    
    def analyze_performance_trend(self, employee_name: str,
                                start_period: str, end_period: str) -> Dict[str, Any]:
        """실적 트렌드를 분석합니다."""
        if hasattr(self, 'use_dummy_data') and self.use_dummy_data:
            return self._get_dummy_trend_data(employee_name, start_period, end_period)
        
        try:
            summary = self.get_performance_summary(employee_name, start_period, end_period)
            monthly_data = summary["monthly_breakdown"]
            
            if len(monthly_data) < 2:
                return {
                    "trend": "데이터 부족",
                    "analysis": "트렌드 분석을 위해서는 최소 2개월 이상의 데이터가 필요합니다."
                }
            
            # 월별 실적 추이 분석
            amounts = [data["amount"] for data in monthly_data]
            
            # 단순 트렌드 계산
            if len(amounts) >= 3:
                recent_avg = sum(amounts[-2:]) / 2
                early_avg = sum(amounts[:2]) / 2
                
                if recent_avg > early_avg * 1.1:
                    trend = "상승"
                elif recent_avg < early_avg * 0.9:
                    trend = "하락"
                else:
                    trend = "안정"
            else:
                if amounts[-1] > amounts[0]:
                    trend = "상승"
                elif amounts[-1] < amounts[0]:
                    trend = "하락"
                else:
                    trend = "안정"
            
            return {
                "trend": trend,
                "analysis": f"분석 기간 동안 실적은 {trend} 추세를 보이고 있습니다.",
                "monthly_amounts": [int(amount) for amount in amounts]  # numpy 타입 방지
            }
            
        except Exception as e:
            print(f"트렌드 분석 오류: {e}")
            return {
                "trend": "분석 실패",
                "analysis": "트렌드 분석 중 오류가 발생했습니다."
            }
    
    def get_target_vs_performance(self, employee_name: str,
                                 start_period: str, end_period: str) -> Dict[str, Any]:
        """목표 대비 실적을 비교 분석합니다."""
        if hasattr(self, 'use_dummy_data') and self.use_dummy_data:
            return self._get_dummy_target_data(employee_name, start_period, end_period)
        
        performance_summary = self.get_performance_summary(employee_name, start_period, end_period)
        
        # 목표 데이터 직접 조회 (간단한 쿼리 사용)
        target_df = self.get_employee_target_data(employee_name, start_period, end_period)
        
        total_performance = performance_summary["total_performance"]
        total_target = 0
        
        # 목표 데이터 계산
        if not bool(target_df.empty):  # pandas boolean → Python bool 변환
            try:
                # 목표 칼럼의 합계 계산
                numeric_targets = pd.to_numeric(target_df['목표'], errors='coerce')
                total_target = float(numeric_targets.sum())  # numpy 타입 방지
                print(f"[TARGET] 목표 데이터: {employee_name}의 목표 {total_target:,.0f}원")
                
            except Exception as e:
                print(f"목표 데이터 계산 오류: {e}")
                total_target = 0.0
        
        # 목표가 0이면 실적 기반으로 가상 목표 설정
        if float(total_target) <= 0:  # Python float로 비교
            print(f"[WARNING] '{employee_name}'의 목표 데이터가 없거나 0입니다.")
            # 실적의 80%를 목표로 가정 (실제 환경에서는 별도 설정 필요)
            total_target = float(total_performance) * 0.8
            print(f"[INFO] 실적의 80%({total_target:,.0f}원)를 가상 목표로 설정합니다.")
        
        # 달성률 계산 (Python float로 연산)
        achievement_rate = (float(total_performance) / float(total_target) * 100) if float(total_target) > 0 else 0.0
        
        # 달성률 평가 (Python float로 비교)
        achievement_rate_val = float(achievement_rate)
        if achievement_rate_val >= 120:
            evaluation = "매우 우수"
            grade = "A+"
        elif achievement_rate_val >= 100:
            evaluation = "우수"
            grade = "A"
        elif achievement_rate_val >= 80:
            evaluation = "양호"
            grade = "B"
        elif achievement_rate_val >= 60:
            evaluation = "보통"
            grade = "C"
        else:
            evaluation = "개선 필요"
            grade = "D"
        
        return {
            "total_performance": int(total_performance),  # numpy 타입 방지
            "total_target": int(total_target),
            "achievement_rate": float(achievement_rate),  # numpy 타입 방지
            "gap_amount": int(total_performance - total_target),
            "evaluation": evaluation,
            "grade": grade
        } 