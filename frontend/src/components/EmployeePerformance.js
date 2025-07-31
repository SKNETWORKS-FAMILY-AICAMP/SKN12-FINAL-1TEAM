<<<<<<< HEAD
import React, { useState } from 'react';
import './EmployeePerformance.css';

function EmployeePerformance({ currentUser }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedPeriod, setSelectedPeriod] = useState('최근 3개월');
  const [selectedDates, setSelectedDates] = useState([]); // 수동 선택된 날짜들
  const [selectedEmployee, setSelectedEmployee] = useState(null); // 선택된 직원

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

  return (
    <div className="employee-performance">
      {/* 왼쪽 사이드바 - 일반 사용자만 표시 */}
      {!isAdmin && (
        <div className="performance-sidebar">
          <h2>실적 분석</h2>
          
          <button className="new-analysis-btn">
            <span className="plus-icon">+</span>
            새로운 분석 생성
          </button>

          <div className="analysis-history">
            {analysisHistory.map((analysis, index) => (
              <div key={index} className="history-item">
                <span className="history-icon">💬</span>
                <span className="history-text">{analysis}</span>
                <span className="history-arrow">›</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 가운데 메인 영역 */}
      <div className="performance-main">
                 {/* 관리자용 직원 선택 */}
         {isAdmin && (
           <div className="employee-selection">
             <h3>직원 선택</h3>
             <div className="employee-search">
               <input 
                 type="text" 
                 placeholder="분석할 직원의 이름 또는 사번을 입력하세요."
                 className="employee-search-input"
               />
             </div>
             <div className="employee-list">
               <h4>나의 팀원</h4>
               <div className="employee-grid">
                 {employees.map((employee) => (
                   <button 
                     key={employee.id}
                     className={`employee-card ${selectedEmployee?.id === employee.id ? 'selected' : ''}`}
                     onClick={() => setSelectedEmployee(employee)}
                   >
                     <div className="employee-info">
                       <div className="employee-name">{employee.name}</div>
                       <div className="employee-team">{employee.team}</div>
                     </div>
                   </button>
                 ))}
               </div>
             </div>
           </div>
         )}

         {/* 선택된 직원의 상세 성과 보고서 */}
         {isAdmin && selectedEmployee && (
           <div className="employee-performance-report">
             <div className="report-header">
               <h2>직원 성과 보고서</h2>
               <p>직원 개발을 위한 상세한 성과 분석 및 전략 인사이트.</p>
             </div>
             
             <div className="employee-profile">
               <div className="profile-image">
                 <div className="profile-avatar">👤</div>
               </div>
               <div className="profile-info">
                 <h3>{selectedEmployee.team} {selectedEmployee.name} 과장</h3>
                 <p>{selectedEmployee.team}</p>
               </div>
             </div>

             <div className="performance-overview">
               <h3>성과 개요</h3>
               <div className="overview-cards">
                 <div className="overview-card">
                   <div className="card-label">할당 업무 완수율</div>
                   <div className="card-value">95%</div>
                 </div>
                 <div className="overview-card">
                   <div className="card-label">분기 매출 증감</div>
                   <div className="card-value">+12%</div>
                 </div>
               </div>
             </div>

             <div className="performance-trend">
               <h3>성과 추이</h3>
               <div className="trend-summary">
                 <div className="trend-value">+8%</div>
                 <div className="trend-period">This Quarter +8%</div>
               </div>
               <div className="trend-chart">
                 <div className="chart-placeholder">
                   📈 성과 추이 그래프 (1월~6월)
                 </div>
               </div>
             </div>
           </div>
         )}

        {/* 조회 기간 설정 - 일반 사용자만 표시 */}
        {!isAdmin && (
          <div className="period-selection">
            <h3>조회 기간 설정</h3>
            <div className="period-tabs">
              {periodOptions.map((period) => (
                <button 
                  key={period}
                  className={`period-tab ${selectedPeriod === period ? 'active' : ''}`}
                  onClick={() => handlePeriodSelect(period)}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 달력 영역 - 일반 사용자만 표시 */}
        {!isAdmin && (
          <div className="calendar-section">
            {isManualSelection ? (
              // 수동 선택일 때 - 제목 옆 네비게이션
              <div className="calendar-container">
                {/* 첫 번째 달력 */}
                <div className="calendar">
                  <div className="calendar-header">
                    <button className="month-nav" onClick={() => changeMonth(-1)}>
                      &#8249;
                    </button>
                    <div className="calendar-title">{firstMonth.year}년 {firstMonth.month + 1}월</div>
                    <div className="nav-spacer"></div>
                  </div>
                  <div className="calendar-grid">
                    <div className="weekdays">
                      {weekDays.map((day) => (
                        <div key={day} className="weekday">{day}</div>
                      ))}
                    </div>
                    <div className="days">
                      {getCalendarDays(firstMonth.year, firstMonth.month).map((day, index) => (
                        <div 
                          key={index} 
                          className={`day ${isSelectedDate(firstMonth.year, firstMonth.month, day) ? 'selected' : ''} ${day ? 'clickable' : ''}`}
                          onClick={() => handleDateClick(firstMonth.year, firstMonth.month, day)}
                        >
                          {day}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 두 번째 달력 */}
                <div className="calendar">
                  <div className="calendar-header">
                    <div className="nav-spacer"></div>
                    <div className="calendar-title">{secondMonth.year}년 {secondMonth.month + 1}월</div>
                    <button className="month-nav" onClick={() => changeMonth(1)}>
                      &#8250;
                    </button>
                  </div>
                  <div className="calendar-grid">
                    <div className="weekdays">
                      {weekDays.map((day) => (
                        <div key={day} className="weekday">{day}</div>
                      ))}
                    </div>
                    <div className="days">
                      {getCalendarDays(secondMonth.year, secondMonth.month).map((day, index) => (
                        <div 
                          key={index} 
                          className={`day ${isSelectedDate(secondMonth.year, secondMonth.month, day) ? 'selected' : ''} ${day ? 'clickable' : ''}`}
                          onClick={() => handleDateClick(secondMonth.year, secondMonth.month, day)}
                        >
                          {day}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              // 정해진 기간일 때 - 기존 방식
              <div className="calendar-container">
                {/* 첫 번째 달력 */}
                <div className="calendar">
                  <div className="calendar-header">
                    <div className="nav-spacer"></div>
                    <div className="calendar-title">{firstMonth.year}년 {firstMonth.month + 1}월</div>
                    <div className="nav-spacer"></div>
                  </div>
                  <div className="calendar-grid">
                    <div className="weekdays">
                      {weekDays.map((day) => (
                        <div key={day} className="weekday">{day}</div>
                      ))}
                    </div>
                    <div className="days">
                      {getCalendarDays(firstMonth.year, firstMonth.month).map((day, index) => (
                        <div 
                          key={index} 
                          className={`day ${isSelectedDate(firstMonth.year, firstMonth.month, day) ? 'selected' : ''}`}
                        >
                          {day}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 두 번째 달력 */}
                <div className="calendar">
                  <div className="calendar-header">
                    <div className="nav-spacer"></div>
                    <div className="calendar-title">{secondMonth.year}년 {secondMonth.month + 1}월</div>
                    <div className="nav-spacer"></div>
                  </div>
                  <div className="calendar-grid">
                    <div className="weekdays">
                      {weekDays.map((day) => (
                        <div key={day} className="weekday">{day}</div>
                      ))}
                    </div>
                    <div className="days">
                      {getCalendarDays(secondMonth.year, secondMonth.month).map((day, index) => (
                        <div 
                          key={index} 
                          className={`day ${isSelectedDate(secondMonth.year, secondMonth.month, day) ? 'selected' : ''}`}
                        >
                          {day}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 달력 하단 버튼들 */}
            <div className="calendar-actions">
              <button className="action-btn secondary">취소</button>
              <button className="action-btn primary">적용하기</button>
            </div>
          </div>
        )}

        {/* 통계 카드 섹션 - 일반 사용자만 표시 */}
        {!isAdmin && (
          <div className="stats-section">
            <div className="stat-card">
              <div className="stat-label">달성 업무 완료율</div>
              <div className="stat-value">92%</div>
              <div className="stat-change positive">+2%</div>
            </div>
            
            <div className="stat-card">
              <div className="stat-label">매출 증감률</div>
              <div className="stat-value">+15%</div>
              <div className="stat-change positive">+15%</div>
            </div>
            
            <div className="stat-card">
              <div className="stat-label">총 방문 횟수</div>
              <div className="stat-value">128</div>
              <div className="stat-change negative">-5%</div>
            </div>
          </div>
        )}
      </div>

      {/* 오른쪽 패널 - 일반 사용자만 표시 */}
      {!isAdmin && (
        <div className="performance-right-panel">
          <h2>실적 분석 보고서 생성</h2>
          
          <div className="report-input">
            <input 
              type="text" 
              placeholder="생성중..."
              className="report-input-field"
              readOnly
            />
          </div>

          <div className="generate-actions">
            <button className="generate-btn">
              보고서 다운로드
            </button>
          </div>
        </div>
      )}
=======
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './EmployeePerformance.css';

function EmployeePerformance() {
  const navigate = useNavigate();
  const [performanceData, setPerformanceData] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
                <img src="https://via.placeholder.com/80x80" alt="Employee" />
              </div>
              <div className="employee-details">
                <h4>최수아</h4>
                <p>영업팀</p>
                <p>담당 지역: 서부팀</p>
              </div>
            </div>
          </div>
          
          <div className="quick-actions">
            <h3>빠른 작업</h3>
            <button 
              className="action-btn primary" 
              onClick={() => runAnalysis(false)}
              disabled={loading}
            >
              {loading ? '분석 중...' : '실적 분석'}
            </button>
            <button 
              className="action-btn secondary" 
              onClick={() => runAnalysis(true)}
              disabled={loading}
            >
              {loading ? '생성 중...' : '보고서 생성'}
            </button>
            <button 
              className="action-btn refresh" 
              onClick={fetchPerformanceSummary}
              disabled={loading}
            >
              {loading ? '새로고침 중...' : '데이터 새로고침'}
            </button>
          </div>
        </div>

        <div className="performance-main">
          <div className="performance-title">
            <h2>실적 현황</h2>
            <p>2023년 12월 ~ 2024년 3월</p>
          </div>

          {error && (
            <div className="error-message">
              <span>❌ {error}</span>
            </div>
          )}

          {loading && (
            <div className="loading-message">
              <span>⏳ 데이터를 불러오는 중...</span>
            </div>
          )}

          {performanceData && (
            <div className="performance-summary">
              <div className="summary-cards">
                <div className="summary-card">
                  <h3>총 실적</h3>
                  <p className="card-value">
                    {performanceData.total_performance?.toLocaleString() || 0}원
                  </p>
                </div>
                <div className="summary-card">
                  <h3>총 목표</h3>
                  <p className="card-value">
                    {performanceData.total_target?.toLocaleString() || 0}원
                  </p>
                </div>
                <div className="summary-card">
                  <h3>달성률</h3>
                  <p className={`card-value ${performanceData.achievement_rate >= 100 ? 'success' : 'warning'}`}>
                    {performanceData.achievement_rate?.toFixed(1) || 0}%
                  </p>
                </div>
                <div className="summary-card">
                  <h3>상태</h3>
                  <p className={`card-value status-${performanceData.status === '급증' ? 'excellent' : performanceData.status === '안정' ? 'good' : 'poor'}`}>
                    {performanceData.status || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {analysisData && (
            <div className="analysis-results">
              <h3>분석 결과</h3>
              <div className="analysis-content">
                <div className="analysis-section">
                  <h4>기본 정보</h4>
                  <p><strong>직원명:</strong> {analysisData.analysis_result?.employee_name || 'N/A'}</p>
                  <p><strong>기간:</strong> {analysisData.analysis_result?.period || 'N/A'}</p>
                  <p><strong>상태:</strong> {analysisData.analysis_result?.status || 'N/A'}</p>
                </div>
                
                {analysisData.analysis_result?.recommendations && (
                  <div className="analysis-section">
                    <h4>권장사항</h4>
                    <ul>
                      {analysisData.analysis_result.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysisData.report && (
                  <div className="analysis-section">
                    <h4>상세 보고서</h4>
                    <div className="report-preview">
                      {analysisData.report.split('\n').map((line, index) => (
                        <p key={index}>{line}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    </div>
  );
}

export default EmployeePerformance; 