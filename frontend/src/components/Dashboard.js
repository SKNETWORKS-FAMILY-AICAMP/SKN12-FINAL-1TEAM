import React from 'react';
import './Dashboard.css';

const Dashboard = ({ currentUser }) => {
  const isAdmin = currentUser?.role === 'admin';

  // 관리자용 요약 카드
  const adminSummaryCards = [
    { title: '전체 사용자 수', value: '24명', color: '#6f42c1' },
    { title: '오늘 로그인 사용자', value: '18명', color: '#28a745' },
    { title: '시스템 알림', value: '2건', color: '#dc3545' },
  ];

  // 일반 사용자용 요약 카드
  const userSummaryCards = [
    { title: '오늘 방문 일정', value: '3건', color: '#6f42c1' },
    { title: '미제출 보고서', value: '1건', color: '#dc3545' },
    { title: '이번 주 실적 달성률', value: '85%', color: '#28a745' },
  ];

  const summaryCards = isAdmin ? adminSummaryCards : userSummaryCards;

  // 관리자용 일정
  const adminSchedule = [
    { time: '오전 9:00 - 10:00', location: '시스템 백업 점검' },
    { time: '오후 2:00 - 3:00', location: '사용자 계정 관리' },
    { time: '오후 4:00 - 5:00', location: '데이터베이스 최적화' },
  ];

  // 일반 사용자용 일정
  const userSchedule = [
    { time: '오전 10:00 - 11:00', location: 'A병원' },
    { time: '오후 1:00 - 2:00', location: 'B약국' },
    { time: '오후 3:00 - 4:00', location: 'C의원' },
  ];

  const dailySchedule = isAdmin ? adminSchedule : userSchedule;

  // 관리자용 최근 활동
  const adminActivities = [
    { 
      icon: '🔧', 
      activity: '시스템 설정 업데이트', 
      date: '2024년 7월 15일' 
    },
    { 
      icon: '👥', 
      activity: '새 사용자 계정 3개 생성', 
      date: '2024년 7월 14일' 
    },
    { 
      icon: '📊', 
      activity: '월간 시스템 리포트 생성', 
      date: '2024년 7월 13일' 
    },
  ];

  // 일반 사용자용 최근 활동
  const userActivities = [
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
          {dailySchedule.map((schedule, index) => (
            <div key={index} className="schedule-item">
              <div className="schedule-icon">{scheduleIcon}</div>
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
        <h3>{isAdmin ? "최근 관리 활동" : "최근 활동"}</h3>
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