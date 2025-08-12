import React, { useState } from 'react';
import './Employee.css';

function Employee({ currentUser }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedPeriod, setSelectedPeriod] = useState('최근 3개월');
  const [selectedDates, setSelectedDates] = useState([]); // 수동 선택된 날짜들

  // 실적 분석 히스토리
  const analysisHistory = [
    `${currentUser?.name || '사용자'}_23.03~23.06...`
  ];

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
      {/* 왼쪽 사이드바 */}
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

      {/* 가운데 메인 영역 */}
      <div className="performance-main">
        {/* 조회 기간 설정 */}
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

        {/* 달력 영역 */}
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

        {/* 통계 카드 섹션 */}
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
      </div>

      {/* 오른쪽 패널 */}
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
    </div>
  );
}

export default Employee; 