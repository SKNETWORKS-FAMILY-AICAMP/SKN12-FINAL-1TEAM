import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Employee.css';

function Employee({ currentUser }) {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedPeriod, setSelectedPeriod] = useState('최근 3개월');
  const [selectedDates, setSelectedDates] = useState([]); // 수동 선택된 날짜들
  const [selectedEmployee, setSelectedEmployee] = useState(null); // 선택된 직원
  const [performanceData, setPerformanceData] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAdmin = currentUser?.role === 'admin';

  // 관리자용 직원 목록
  const employees = [
    { id: 'E001', name: '김민지', team: '영업 1팀', performance: 85 },
    { id: 'E002', name: '최수아', team: '영업 1팀', performance: 92 },
    { id: 'E003', name: '정다은', team: '영업 1팀', performance: 78 },
    { id: 'E004', name: '박준호', team: '영업 2팀', performance: 88 },
    { id: 'E005', name: '이현우', team: '영업 2팀', performance: 95 },
    { id: 'E006', name: '강지훈', team: '영업 2팀', performance: 82 },
  ];

  // 실적 분석 히스토리
  const analysisHistory = isAdmin 
    ? [`${selectedEmployee?.name || '전체'}_23.03~23.06...`]
    : [`${currentUser?.name || '사용자'}_23.03~23.06...`];

  // 기간 설정 옵션
  const periodOptions = ['최근 3개월', '올해', '1분기', '2분기', '3분기', '4분기', '수동 선택'];

  // 실적 요약 데이터 가져오기
  const fetchPerformanceSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/employee/performance/summary');
      const data = await response.json();
      
      if (data.success) {
        setPerformanceData(data.summary);
      } else {
        setError(data.message || '실적 데이터를 가져오는데 실패했습니다.');
      }
    } catch (err) {
      setError('서버 연결 오류가 발생했습니다.');
      console.error('실적 요약 조회 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 실적 분석 실행
  const runAnalysis = async (saveReport = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/employee/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employee_name: '최수아',
          period: '202312~202403',
          save_report: saveReport,
          filename: saveReport ? '최수아_실적분석보고서.docx' : null
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setAnalysisData(data);
        if (saveReport) {
          alert('보고서가 성공적으로 생성되었습니다!');
        }
      } else {
        setError(data.message || '분석 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError('서버 연결 오류가 발생했습니다.');
      console.error('실적 분석 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  // 기간 선택 핸들러
  const handlePeriodSelect = (period) => {
    setSelectedPeriod(period);
    if (period !== '수동 선택') {
      setSelectedDates([]); // 수동 선택이 아닐 때는 선택된 날짜 초기화
    }
  };

  // 날짜 클릭 핸들러 (수동 선택일 때만)
  const handleDateClick = (year, month, day) => {
    if (!day || selectedPeriod !== '수동 선택') return;
    
    const clickedDate = new Date(year, month, day);
    const dateKey = clickedDate.toDateString();
    
    setSelectedDates(prev => {
      if (prev.includes(dateKey)) {
        // 이미 선택된 날짜면 제거
        return prev.filter(date => date !== dateKey);
      } else {
        // 새로운 날짜 추가 (최대 2개까지만)
        if (prev.length >= 2) {
          return [prev[1], dateKey]; // 첫 번째 제거하고 새로운 것 추가
        }
        return [...prev, dateKey].sort(); // 날짜 순으로 정렬
      }
    });
  };

  // 선택된 기간에 따른 시작월과 끝월 계산
  const getPeriodRange = (period) => {
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth(); // 0-based
    
    switch(period) {
      case '최근 3개월':
        const startMonth = currentMonth - 2;
        return {
          startDate: new Date(currentYear, startMonth, 1),
          endDate: new Date(currentYear, currentMonth + 1, 0)
        };
      case '올해':
        return {
          startDate: new Date(currentYear, 0, 1),
          endDate: new Date(currentYear, 11, 31)
        };
      case '1분기':
        return {
          startDate: new Date(currentYear, 0, 1),
          endDate: new Date(currentYear, 2, 31)
        };
      case '2분기':
        return {
          startDate: new Date(currentYear, 3, 1),
          endDate: new Date(currentYear, 5, 30)
        };
      case '3분기':
        return {
          startDate: new Date(currentYear, 6, 1),
          endDate: new Date(currentYear, 8, 30)
        };
      case '4분기':
        return {
          startDate: new Date(currentYear, 9, 1),
          endDate: new Date(currentYear, 11, 31)
        };
      default:
        return {
          startDate: new Date(currentYear, currentMonth - 2, 1),
          endDate: new Date(currentYear, currentMonth + 1, 0)
        };
    }
  };

  // 표시할 달력 월 계산
  const getDisplayMonths = () => {
    if (selectedPeriod === '수동 선택') {
      // 수동 선택일 때는 현재 날짜 기준으로 연속된 두 달
      const currentYear = currentDate.getFullYear();
      const currentMonth = currentDate.getMonth();
      const nextMonth = currentMonth === 11 ? 0 : currentMonth + 1;
      const nextYear = currentMonth === 11 ? currentYear + 1 : currentYear;
      
      return {
        firstMonth: { year: currentYear, month: currentMonth },
        secondMonth: { year: nextYear, month: nextMonth }
      };
    } else {
      // 정해진 기간일 때는 시작월과 끝월
      const { startDate, endDate } = getPeriodRange(selectedPeriod);
      return {
        firstMonth: { year: startDate.getFullYear(), month: startDate.getMonth() },
        secondMonth: { year: endDate.getFullYear(), month: endDate.getMonth() }
      };
    }
  };

  // 실제 달력 데이터 생성
  const getCalendarDays = (year, month) => {
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    const days = [];
    
    // 이전 달의 빈 날짜들
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    
    // 현재 달의 날짜들
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }
    
    return days;
  };

  // 특정 날짜가 선택된 기간의 시작 또는 끝인지 확인
  const isSelectedDate = (year, month, day) => {
    if (!day) return false;
    
    if (selectedPeriod === '수동 선택') {
      // 수동 선택일 때는 selectedDates 확인
      const dateKey = new Date(year, month, day).toDateString();
      return selectedDates.includes(dateKey);
    } else {
      // 정해진 기간일 때는 기존 로직
      const { startDate, endDate } = getPeriodRange(selectedPeriod);
      const currentDateObj = new Date(year, month, day);
      
      return (
        (currentDateObj.getTime() === startDate.getTime()) ||
        (currentDateObj.getTime() === endDate.getTime())
      );
    }
  };

  const changeMonth = (direction) => {
    setCurrentDate(prevDate => {
      const newDate = new Date(prevDate);
      newDate.setMonth(newDate.getMonth() + direction);
      return newDate;
    });
  };

  const weekDays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

  // 표시할 월 정보
  const { firstMonth, secondMonth } = getDisplayMonths();
  const isManualSelection = selectedPeriod === '수동 선택';

  // 컴포넌트 마운트 시 실적 데이터 로드
  useEffect(() => {
    fetchPerformanceSummary();
  }, []);

  return (
    <div className="employee-performance">
      <div className="performance-header">
        <div className="header-left">
          <h1>직원 실적 관리</h1>
        </div>
        <div className="header-center">
          <div className="logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">Pharma-Helper</span>
          </div>
        </div>
        <div className="header-right">
          <nav className="header-nav">
            <a href="#" className="nav-link" onClick={(e) => { e.preventDefault(); navigate('/'); }}>홈</a>
            <a href="#" className="nav-link">AI 채팅</a>
            <a href="#" className="nav-link">고객/데이터 위키</a>
            <a href="#" className="nav-link">문서 생성</a>
            <a href="#" className="nav-link active">실적 확인</a>
          </nav>
          <div className="header-actions">
            <button className="notification-btn">🔔</button>
            <div className="user-profile">
              <img src="https://via.placeholder.com/32x32" alt="User" />
            </div>
          </div>
        </div>
      </div>

      <div className="performance-container">
        <div className="performance-sidebar">
          <div className="employee-info">
            <h3>직원 정보</h3>
            <div className="employee-card">
              <div className="employee-avatar">
                <img src="https://via.placeholder.com/60x60" alt="Employee" />
              </div>
              <div className="employee-details">
                <h4>{currentUser?.name || '사용자'}</h4>
                <p>{currentUser?.team || '영업 1팀'}</p>
                <p>{currentUser?.position || '영업사원'}</p>
              </div>
            </div>
          </div>

          {isAdmin && (
            <div className="employee-selector">
              <h3>직원 선택</h3>
              <div className="employee-list">
                {employees.map(employee => (
                  <div 
                    key={employee.id}
                    className={`employee-item ${selectedEmployee?.id === employee.id ? 'selected' : ''}`}
                    onClick={() => setSelectedEmployee(employee)}
                  >
                    <div className="employee-info">
                      <h4>{employee.name}</h4>
                      <p>{employee.team}</p>
                    </div>
                    <div className="performance-score">
                      {employee.performance}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="period-selector">
            <h3>기간 설정</h3>
            <div className="period-options">
              {periodOptions.map(period => (
                <button
                  key={period}
                  className={`period-option ${selectedPeriod === period ? 'selected' : ''}`}
                  onClick={() => handlePeriodSelect(period)}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>

          <div className="analysis-actions">
            <h3>분석 도구</h3>
            <button 
              className="analyze-btn"
              onClick={() => runAnalysis(false)}
              disabled={loading}
            >
              {loading ? '분석 중...' : '실적 분석'}
            </button>
            <button 
              className="generate-report-btn"
              onClick={() => runAnalysis(true)}
              disabled={loading}
            >
              {loading ? '생성 중...' : '보고서 생성'}
            </button>
          </div>

          <div className="analysis-history">
            <h3>분석 히스토리</h3>
            <div className="history-list">
              {analysisHistory.map((item, index) => (
                <div key={index} className="history-item">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="performance-main">
          <div className="performance-overview">
            <h2>실적 개요</h2>
            {loading ? (
              <div className="loading">데이터를 불러오는 중...</div>
            ) : error ? (
              <div className="error">{error}</div>
            ) : performanceData ? (
              <div className="performance-stats">
                <div className="stat-card">
                  <h3>총 매출</h3>
                  <p className="stat-value">{performanceData.totalSales?.toLocaleString()}원</p>
                </div>
                <div className="stat-card">
                  <h3>평균 실적</h3>
                  <p className="stat-value">{performanceData.averagePerformance}%</p>
                </div>
                <div className="stat-card">
                  <h3>목표 달성률</h3>
                  <p className="stat-value">{performanceData.goalAchievement}%</p>
                </div>
              </div>
            ) : (
              <div className="no-data">데이터가 없습니다.</div>
            )}
          </div>

          <div className="performance-chart">
            <h2>실적 추이</h2>
            <div className="chart-container">
              {/* 차트 컴포넌트가 여기에 들어갈 예정 */}
              <div className="chart-placeholder">
                실적 차트가 여기에 표시됩니다.
              </div>
            </div>
          </div>

          {analysisData && (
            <div className="analysis-results">
              <h2>분석 결과</h2>
              <div className="analysis-content">
                <pre>{JSON.stringify(analysisData, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Employee; 