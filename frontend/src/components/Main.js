import React, { useState } from 'react';
import './Main.css';

const Main = ({ currentUser, schedules = [] }) => {
  const isAdmin = currentUser?.role === 'admin';

  // 오늘 날짜 가져오기
  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // 오늘 일정만 필터링
  const todaySchedules = schedules.filter(schedule => schedule.date === getTodayDate());
  
  // 최근 활동 상태 관리 (필요시 나중에 구현)
  const userActivities = [];
  const adminActivities = [];

  // 관리자용 요약 카드
  const adminSummaryCards = [
    { title: '전체 사용자 수', value: '24명', color: '#6f42c1' },
    { title: '오늘 로그인 사용자', value: '18명', color: '#28a745' },
    { title: '시스템 알림', value: '2건', color: '#dc3545' },
  ];

  // 일반 사용자용 요약 카드
  const userSummaryCards = [
    { title: '오늘 방문 일정', value: `${todaySchedules.length}건`, color: '#6f42c1' },
    { title: '미제출 보고서', value: '0건', color: '#dc3545' },
    { title: '이번 주 실적 달성률', value: '0%', color: '#28a745' },
  ];

  const summaryCards = isAdmin ? adminSummaryCards : userSummaryCards;

  // 현재 일정 (관리자/사용자 구분)
  const dailySchedule = isAdmin ? [] : todaySchedules;

  // 현재 활동 (관리자/사용자 구분)
  const recentActivities = isAdmin ? adminActivities : userActivities;

  // AI 제안 내용
  const aiSuggestion = isAdmin 
    ? "사용자 활동이 증가하고 있습니다. 서버 리소스 모니터링을 권장합니다."
    : "B 병원 방문 시, 최근 발표된 경쟁사 논문 자료를 준비하세요";

  const scheduleTitle = isAdmin ? "관리 업무 일정" : "나의 일일 계획";
  const scheduleIcon = isAdmin ? "⚙️" : "💼";

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{currentUser?.name || '사용자'}님, 좋은 하루입니다!</h1>
        {isAdmin && (
          <div className="admin-badge" style={{
            backgroundColor: '#dc3545',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            marginTop: '8px',
            display: 'inline-block'
          }}>
            🛡️ 시스템 관리자
          </div>
        )}
      </div>

      {/* 요약 정보 카드 */}
      <div className="summary-cards">
        {summaryCards.map((card, index) => (
          <div key={index} className="summary-card">
            <h3>{card.title}</h3>
            <div className="card-value" style={{ color: card.color }}>
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* AI 제안 섹션 */}
      <div className="ai-suggestion">
        <div className="ai-suggestion-content">
          <h3>{isAdmin ? "시스템 AI 제안" : "AI 제안"}</h3>
          <p>{aiSuggestion}</p>
        </div>
        <div className="ai-suggestion-bg"></div>
      </div>

      {/* 일일 계획 섹션 */}
      <div className="daily-plan">
        <h3>{scheduleTitle}</h3>
        <div className="schedule-list">
          {dailySchedule.length > 0 ? (
            dailySchedule.map((schedule, index) => (
              <div key={index} className="schedule-item">
                <div className="schedule-icon">{scheduleIcon}</div>
                <div className="schedule-details">
                  <div className="schedule-time">{schedule.time}</div>
                  <div className="schedule-location">{schedule.location}</div>
                </div>
                {index < dailySchedule.length - 1 && <div className="schedule-connector"></div>}
              </div>
            ))
          ) : (
            <div className="no-schedule">
              <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                등록된 일정이 없습니다. 일정 관리 페이지에서 일정을 추가해주세요.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 최근 활동 섹션 */}
      <div className="recent-activities">
        <h3>{isAdmin ? "최근 관리 활동" : "최근 활동"}</h3>
        <div className="activity-list">
          {recentActivities.length > 0 ? (
            recentActivities.map((activity, index) => (
              <div key={index} className="activity-item">
                <div className="activity-icon">{activity.icon}</div>
                <div className="activity-details">
                  <div className="activity-text">{activity.activity}</div>
                  <div className="activity-date">{activity.date}</div>
                </div>
              </div>
            ))
          ) : (
            <div className="no-activities">
              <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                최근 활동이 없습니다.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Main; 