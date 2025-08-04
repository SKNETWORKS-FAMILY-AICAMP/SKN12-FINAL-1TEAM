import React, { useState } from 'react';
import './Schedule.css';

const Schedule = () => {
  const [schedules, setSchedules] = useState([
    {
      id: 1,
      title: 'A병원 방문',
      type: '방문',
      date: '2024-07-22',
      time: '10:00',
      duration: '1시간',
      location: 'A병원',
      contact: '김의사',
      status: '예정',
      notes: '신제품 소개 및 계약 논의',
    },
    {
      id: 2,
      title: 'B약국 제품 교육',
      type: '교육',
      date: '2024-07-22',
      time: '14:00',
      duration: '2시간',
      location: 'B약국',
      contact: '이약사',
      status: '예정',
      notes: '신제품 사용법 교육',
    },
    {
      id: 3,
      title: 'C의원 계약 갱신',
      type: '계약',
      date: '2024-07-23',
      time: '09:00',
      duration: '30분',
      location: 'C의원',
      contact: '박원장',
      status: '완료',
      notes: '계약 갱신 완료',
    },
  ]);

  const [selectedDate, setSelectedDate] = useState('2024-07-22');
  const [showAddForm, setShowAddForm] = useState(false);

  const filteredSchedules = schedules.filter(schedule => schedule.date === selectedDate);

  const scheduleTypes = [
    { id: '방문', name: '방문', color: '#6f42c1' },
    { id: '교육', name: '교육', color: '#28a745' },
    { id: '계약', name: '계약', color: '#dc3545' },
    { id: '회의', name: '회의', color: '#ffc107' },
  ];

  const statusColors = {
    '예정': '#6f42c1',
    '진행중': '#ffc107',
    '완료': '#28a745',
    '취소': '#dc3545',
  };

  return (
    <div className="schedule-page">
      <div className="schedule-header">
        <h2>일정 관리</h2>
        
      </div>

      <div className="schedule-controls">
        <div className="date-control">
          <label>날짜 선택:</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="date-picker"
          />
        </div>
        
        <button 
          className="add-schedule-btn"
          onClick={() => setShowAddForm(true)}
        >
          + 새 일정 추가
        </button>
      </div>

      <div className="schedule-stats">
        <div className="stat-card">
          <h3>오늘 일정</h3>
          <div className="stat-value">{filteredSchedules.length}</div>
        </div>
        <div className="stat-card">
          <h3>이번 주 일정</h3>
          <div className="stat-value">8</div>
        </div>
        <div className="stat-card">
          <h3>완료된 일정</h3>
          <div className="stat-value">{schedules.filter(s => s.status === '완료').length}</div>
        </div>
      </div>

      <div className="schedule-content">
        <div className="schedule-list">
          <h3>{selectedDate} 일정</h3>
          
          {filteredSchedules.length === 0 ? (
            <div className="no-schedule">
              <p>선택한 날짜에 일정이 없습니다.</p>
            </div>
          ) : (
            <div className="schedule-items">
              {filteredSchedules.map(schedule => (
                <div key={schedule.id} className="schedule-item">
                  <div className="schedule-time">
                    <div className="time">{schedule.time}</div>
                    <div className="duration">{schedule.duration}</div>
                  </div>
                  
                  <div className="schedule-info">
                    <div className="schedule-header">
                      <h4>{schedule.title}</h4>
                      <span 
                        className="schedule-type"
                        style={{ backgroundColor: scheduleTypes.find(t => t.id === schedule.type)?.color + '20', color: scheduleTypes.find(t => t.id === schedule.type)?.color }}
                      >
                        {schedule.type}
                      </span>
                    </div>
                    
                    <div className="schedule-details">
                      <div className="detail-item">
                        <span className="detail-label">📍</span>
                        <span>{schedule.location}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">👤</span>
                        <span>{schedule.contact}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">📝</span>
                        <span>{schedule.notes}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="schedule-status">
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: statusColors[schedule.status] + '20', color: statusColors[schedule.status] }}
                    >
                      {schedule.status}
                    </span>
                    <div className="schedule-actions">
                      <button className="action-btn edit">수정</button>
                      <button className="action-btn delete">삭제</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* <div className="schedule-calendar">
          <h3>월간 일정</h3>
          <div className="calendar-placeholder">
            <p>달력 뷰는 추후 구현 예정입니다.</p>
            <p>현재는 목록 뷰로 일정을 확인할 수 있습니다.</p>
          </div>
        </div> */}
      </div>
    </div>
  );
};

export default Schedule; 