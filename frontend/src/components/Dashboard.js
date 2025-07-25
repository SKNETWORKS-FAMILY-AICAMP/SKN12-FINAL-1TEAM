import React from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const summaryCards = [
    { title: '오늘 방문 일정', value: '3건', color: '#6f42c1' },
    { title: '미제출 보고서', value: '1건', color: '#dc3545' },
    { title: '이번 주 실적 달성률', value: '85%', color: '#28a745' },
  ];

  const dailySchedule = [
    { time: '오전 10:00 - 11:00', location: 'A병원' },
    { time: '오후 1:00 - 2:00', location: 'B약국' },
    { time: '오후 3:00 - 4:00', location: 'C의원' },
  ];

  const recentActivities = [
    { 
      icon: '📄', 
      activity: 'A병원 방문 보고서 제출', 
      date: '2024년 7월 15일' 
    },
    { 
      icon: '💬', 
      activity: 'B약국 담당자와의 채팅', 
      date: '2024년 7월 14일' 
    },
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>김복남님, 좋은 하루입니다!</h1>
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
          <h3>AI 제안</h3>
          <p>B 병원 방문 시, 최근 발표된 경쟁사 논문 자료를 준비하세요</p>
        </div>
        <div className="ai-suggestion-bg"></div>
      </div>

      {/* 일일 계획 섹션 */}
      <div className="daily-plan">
        <h3>나의 일일 계획</h3>
        <div className="schedule-list">
          {dailySchedule.map((schedule, index) => (
            <div key={index} className="schedule-item">
              <div className="schedule-icon">💼</div>
              <div className="schedule-details">
                <div className="schedule-time">{schedule.time}</div>
                <div className="schedule-location">{schedule.location}</div>
              </div>
              {index < dailySchedule.length - 1 && <div className="schedule-connector"></div>}
            </div>
          ))}
        </div>
      </div>

      {/* 최근 활동 섹션 */}
      <div className="recent-activities">
        <h3>최근 활동</h3>
        <div className="activity-list">
          {recentActivities.map((activity, index) => (
            <div key={index} className="activity-item">
              <div className="activity-icon">{activity.icon}</div>
              <div className="activity-details">
                <div className="activity-text">{activity.activity}</div>
                <div className="activity-date">{activity.date}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 