import React, { useState, useEffect } from 'react';
import './Schedule.css';

const Schedule = ({ schedules, setSchedules }) => {
  // 오늘 날짜 가져오기
  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // 현재 시간 가져오기
  const getCurrentTime = () => {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
  };

  // schedules와 setSchedules는 이제 props로 받음

  const [selectedDate, setSelectedDate] = useState(getTodayDate());
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSchedule, setNewSchedule] = useState({
    employee_id: '',
    title: '',
    location: '',
    contact_person: '',
    schedule_date: getTodayDate(),
    schedule_time: getCurrentTime(),
    duration: '1시간',
    schedule_type: '방문',
    status: '예정',
    memo: '',
  });

  // 날짜가 변경될 때마다 새 일정의 날짜도 업데이트
  useEffect(() => {
    setNewSchedule(prev => ({ ...prev, schedule_date: selectedDate }));
  }, [selectedDate]);

  const filteredSchedules = schedules.filter(schedule => schedule.schedule_date === selectedDate);

  // 오늘 일정만 필터링
  const todaySchedules = schedules.filter(schedule => schedule.schedule_date === getTodayDate());

  // 이번 주 일정 계산
  const getWeekSchedules = () => {
    const today = new Date();
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());
    
    const endOfWeek = new Date(today);
    endOfWeek.setDate(today.getDate() + (6 - today.getDay()));
    
    return schedules.filter(schedule => {
      const scheduleDate = new Date(schedule.schedule_date);
      return scheduleDate >= startOfWeek && scheduleDate <= endOfWeek;
    });
  };

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

  // 새 일정 추가
  const handleAddSchedule = () => {
    if (!newSchedule.title || !newSchedule.location || !newSchedule.contact_person) {
      alert('제목, 거래처(위치), 담당자는 필수 입력 항목입니다.');
      return;
    }

    // 현재 로그인한 사용자의 employee_id 설정 (실제로는 props나 context에서 가져와야 함)
    const schedule = {
      ...newSchedule,
      id: Date.now(),
      employee_id: 'EMP001', // TODO: 실제 로그인한 사용자 ID로 변경 필요
    };

    setSchedules([...schedules, schedule]);
    setShowAddForm(false);
    setNewSchedule({
      employee_id: '',
      title: '',
      location: '',
      contact_person: '',
      schedule_date: selectedDate,
      schedule_time: getCurrentTime(),
      duration: '1시간',
      schedule_type: '방문',
      status: '예정',
      memo: '',
    });
  };

  // 일정 삭제
  const handleDeleteSchedule = (id) => {
    if (window.confirm('이 일정을 삭제하시겠습니까?')) {
      setSchedules(schedules.filter(schedule => schedule.id !== id));
    }
  };

  // 일정 상태 변경
  const handleStatusChange = (id, newStatus) => {
    setSchedules(schedules.map(schedule => 
      schedule.id === id ? { ...schedule, status: newStatus } : schedule
    ));
  };

  return (
    <div className="schedule-page">
      <div className="schedule-header">
        <h2>일정 관리</h2>
        <div className="today-info">
          오늘: {new Date().toLocaleDateString('ko-KR', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric', 
            weekday: 'long' 
          })}
        </div>
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
          <button 
            className="today-btn"
            onClick={() => setSelectedDate(getTodayDate())}
          >
            오늘
          </button>
        </div>
        
        <button 
          className="add-schedule-btn"
          onClick={() => setShowAddForm(true)}
        >
          + 새 일정 추가
        </button>
      </div>

      <div className="schedule-stats">
        <div className="schedule-stat-card">
          <div className="schedule-stat-icon">📅</div>
          <h3>오늘 일정</h3>
          <div className="schedule-stat-value">{todaySchedules.length}</div>
        </div>
        <div className="schedule-stat-card">
          <div className="schedule-stat-icon">📆</div>
          <h3>이번 주 일정</h3>
          <div className="schedule-stat-value">{getWeekSchedules().length}</div>
        </div>
        <div className="schedule-stat-card">
          <div className="schedule-stat-icon">✅</div>
          <h3>완료된 일정</h3>
          <div className="schedule-stat-value">{schedules.filter(s => s.status === '완료').length}</div>
        </div>
      </div>

      {/* 일정 추가 폼 */}
      {showAddForm && (
        <div className="add-schedule-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>새 일정 추가</h3>
              <button 
                className="close-btn"
                onClick={() => setShowAddForm(false)}
              >
                ✕
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label>제목 *</label>
                <input
                  type="text"
                  value={newSchedule.title}
                  onChange={(e) => setNewSchedule({...newSchedule, title: e.target.value})}
                  placeholder="예: ○○병원 방문"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>거래처 (위치) *</label>
                  <input
                    type="text"
                    value={newSchedule.location}
                    onChange={(e) => setNewSchedule({...newSchedule, location: e.target.value})}
                    placeholder="예: A병원, B약국"
                  />
                </div>

                <div className="form-group">
                  <label>담당자 *</label>
                  <input
                    type="text"
                    value={newSchedule.contact_person}
                    onChange={(e) => setNewSchedule({...newSchedule, contact_person: e.target.value})}
                    placeholder="예: 김의사, 이약사"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>날짜</label>
                  <input
                    type="date"
                    value={newSchedule.schedule_date}
                    onChange={(e) => setNewSchedule({...newSchedule, schedule_date: e.target.value})}
                  />
                </div>

                <div className="form-group">
                  <label>시간</label>
                  <input
                    type="time"
                    value={newSchedule.schedule_time}
                    onChange={(e) => setNewSchedule({...newSchedule, schedule_time: e.target.value})}
                  />
                </div>

                <div className="form-group">
                  <label>소요 시간</label>
                  <select
                    value={newSchedule.duration}
                    onChange={(e) => setNewSchedule({...newSchedule, duration: e.target.value})}
                  >
                    <option value="30분">30분</option>
                    <option value="1시간">1시간</option>
                    <option value="1시간 30분">1시간 30분</option>
                    <option value="2시간">2시간</option>
                    <option value="2시간 30분">2시간 30분</option>
                    <option value="3시간">3시간</option>
                    <option value="반나절">반나절</option>
                    <option value="종일">종일</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>일정 유형</label>
                  <select
                    value={newSchedule.schedule_type}
                    onChange={(e) => setNewSchedule({...newSchedule, schedule_type: e.target.value})}
                  >
                    {scheduleTypes.map(type => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>상태</label>
                  <select
                    value={newSchedule.status}
                    onChange={(e) => setNewSchedule({...newSchedule, status: e.target.value})}
                  >
                    <option value="예정">예정</option>
                    <option value="진행중">진행중</option>
                    <option value="완료">완료</option>
                    <option value="취소">취소</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>메모</label>
                <textarea
                  value={newSchedule.memo}
                  onChange={(e) => setNewSchedule({...newSchedule, memo: e.target.value})}
                  placeholder="일정에 대한 메모를 입력하세요"
                  rows="3"
                />
              </div>
            </div>

            <div className="modal-footer">
              <button 
                className="cancel-btn"
                onClick={() => setShowAddForm(false)}
              >
                취소
              </button>
              <button 
                className="save-btn"
                onClick={handleAddSchedule}
              >
                저장
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="schedule-content">
        <div className="schedule-list">
          <h3>
            {selectedDate === getTodayDate() ? '오늘' : selectedDate} 일정
            {filteredSchedules.length > 0 && ` (${filteredSchedules.length}개)`}
          </h3>
          
          {filteredSchedules.length === 0 ? (
            <div className="no-schedule">
              <p>선택한 날짜에 일정이 없습니다.</p>
              <button 
                className="add-first-schedule"
                onClick={() => setShowAddForm(true)}
              >
                첫 일정 추가하기
              </button>
            </div>
          ) : (
            <div className="schedule-items">
              {filteredSchedules
                .sort((a, b) => a.schedule_time.localeCompare(b.schedule_time))
                .map(schedule => (
                <div key={schedule.id} className="schedule-item">
                  <div className="schedule-time">
                    <div className="time">{schedule.schedule_time}</div>
                    <div className="duration">{schedule.duration}</div>
                  </div>
                  
                  <div className="schedule-info">
                    <div className="schedule-header">
                      <h4>{schedule.title}</h4>
                      <span 
                        className="schedule-type"
                        style={{ 
                          backgroundColor: scheduleTypes.find(t => t.id === schedule.schedule_type)?.color + '20', 
                          color: scheduleTypes.find(t => t.id === schedule.schedule_type)?.color 
                        }}
                      >
                        {schedule.schedule_type}
                      </span>
                    </div>
                    
                    <div className="schedule-details">
                      <div className="detail-item">
                        <span className="detail-label">📍</span>
                        <span>{schedule.location}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">👤</span>
                        <span>{schedule.contact_person}</span>
                      </div>
                      {schedule.memo && (
                        <div className="detail-item">
                          <span className="detail-label">📝</span>
                          <span>{schedule.memo}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="schedule-status">
                    <select 
                      className="status-select"
                      value={schedule.status}
                      onChange={(e) => handleStatusChange(schedule.id, e.target.value)}
                      style={{ 
                        backgroundColor: statusColors[schedule.status] + '20', 
                        color: statusColors[schedule.status],
                        border: `1px solid ${statusColors[schedule.status]}50`
                      }}
                    >
                      <option value="예정">예정</option>
                      <option value="진행중">진행중</option>
                      <option value="완료">완료</option>
                      <option value="취소">취소</option>
                    </select>
                    <div className="schedule-actions">
                      <button 
                        className="action-btn delete"
                        onClick={() => handleDeleteSchedule(schedule.id)}
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Schedule;