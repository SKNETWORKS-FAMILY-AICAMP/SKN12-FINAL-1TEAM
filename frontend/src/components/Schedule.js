import React, { useState, useEffect } from 'react';
import './Schedule.css';

const Schedule = ({ currentUser }) => {
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
    return `${hours}:${minutes}:00`;
  };

  const [schedules, setSchedules] = useState([]);
  const [selectedDate, setSelectedDate] = useState(getTodayDate());
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [useLocalStorage, setUseLocalStorage] = useState(false); // API 실패시 localStorage 사용
  const [newSchedule, setNewSchedule] = useState({
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

  // 컴포넌트 마운트 시 일정 가져오기
  useEffect(() => {
    fetchSchedules();
  }, []);

  // localStorage에서 일정 가져오기
  const getSchedulesFromLocalStorage = () => {
    const userId = currentUser?.employee_id || currentUser?.email || 'guest';
    const storageKey = `schedules_${userId}`;
    const saved = localStorage.getItem(storageKey);
    return saved ? JSON.parse(saved) : [];
  };

  // localStorage에 일정 저장
  const saveSchedulesToLocalStorage = (schedulesToSave) => {
    const userId = currentUser?.employee_id || currentUser?.email || 'guest';
    const storageKey = `schedules_${userId}`;
    localStorage.setItem(storageKey, JSON.stringify(schedulesToSave));
  };

  // 일정 가져오기
  const fetchSchedules = async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    
    console.log('📅 일정 API 호출 시작');
    console.log('토큰:', token ? '있음' : '없음');
    
    try {
      const response = await fetch('http://localhost:8010/schedules/my', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('응답 상태:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📅 받은 일정 데이터:', data);
        console.log('일정 개수:', data.length);
        setSchedules(data);
        setUseLocalStorage(false);
      } else {
        console.warn('Schedule API not available:', response.status);
        setUseLocalStorage(true);
        const localSchedules = getSchedulesFromLocalStorage();
        setSchedules(localSchedules);
      }
    } catch (error) {
      console.error('일정 가져오기 오류:', error);
      console.warn('Using localStorage due to API error');
      setUseLocalStorage(true);
      const localSchedules = getSchedulesFromLocalStorage();
      setSchedules(localSchedules);
    } finally {
      setLoading(false);
    }
  };

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
    { id: '회의', name: '회의', color: '#ffc107' },
    { id: '교육', name: '교육', color: '#28a745' },
    { id: '기타', name: '기타', color: '#dc3545' },
  ];

  const statusColors = {
    '예정': '#6f42c1',
    '진행중': '#ffc107',
    '완료': '#28a745',
    '취소': '#dc3545',
  };

  // 새 일정 추가
  const handleAddSchedule = async () => {
    if (!newSchedule.title || !newSchedule.location || !newSchedule.contact_person) {
      alert('제목, 거래처(위치), 담당자는 필수 입력 항목입니다.');
      return;
    }

    if (useLocalStorage) {
      // localStorage 사용
      const newScheduleWithId = {
        ...newSchedule,
        schedule_id: Date.now(),
        employee_id: currentUser?.employee_id || 'guest',
        created_at: new Date().toISOString()
      };
      const updatedSchedules = [...schedules, newScheduleWithId];
      setSchedules(updatedSchedules);
      saveSchedulesToLocalStorage(updatedSchedules);
      setShowAddForm(false);
      setNewSchedule({
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
      alert('일정이 추가되었습니다. (로컬 저장)');
      return;
    }

    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    
    try {
      const response = await fetch('http://localhost:8010/schedules', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newSchedule)
      });

      if (response.ok) {
        const createdSchedule = await response.json();
        setSchedules([...schedules, createdSchedule]);
        setShowAddForm(false);
        setNewSchedule({
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
        alert('일정이 추가되었습니다.');
      } else if (response.status === 404) {
        // API가 없으면 localStorage로 전환
        setUseLocalStorage(true);
        handleAddSchedule(); // localStorage로 다시 시도
      } else {
        const error = await response.json();
        alert(`일정 추가 실패: ${error.detail || '오류가 발생했습니다.'}`);
      }
    } catch (error) {
      console.error('일정 추가 오류:', error);
      setUseLocalStorage(true);
      handleAddSchedule(); // localStorage로 다시 시도
    }
  };

  // 일정 삭제
  const handleDeleteSchedule = async (scheduleId) => {
    if (!window.confirm('이 일정을 삭제하시겠습니까?')) {
      return;
    }

    if (useLocalStorage) {
      // localStorage 사용
      const updatedSchedules = schedules.filter(schedule => schedule.schedule_id !== scheduleId);
      setSchedules(updatedSchedules);
      saveSchedulesToLocalStorage(updatedSchedules);
      alert('일정이 삭제되었습니다. (로컬)');
      return;
    }

    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    
    try {
      const response = await fetch(`http://localhost:8010/schedules/${scheduleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setSchedules(schedules.filter(schedule => schedule.schedule_id !== scheduleId));
        alert('일정이 삭제되었습니다.');
      } else if (response.status === 404) {
        // API가 없으면 localStorage로 전환
        setUseLocalStorage(true);
        handleDeleteSchedule(scheduleId); // localStorage로 다시 시도
      } else {
        const error = await response.json();
        alert(`일정 삭제 실패: ${error.detail || '오류가 발생했습니다.'}`);
      }
    } catch (error) {
      console.error('일정 삭제 오류:', error);
      setUseLocalStorage(true);
      handleDeleteSchedule(scheduleId); // localStorage로 다시 시도
    }
  };

  // 일정 상태 변경
  const handleStatusChange = async (scheduleId, newStatus) => {
    if (useLocalStorage) {
      // localStorage 사용
      const updatedSchedules = schedules.map(schedule => 
        schedule.schedule_id === scheduleId ? { ...schedule, status: newStatus } : schedule
      );
      setSchedules(updatedSchedules);
      saveSchedulesToLocalStorage(updatedSchedules);
      return;
    }

    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    
    try {
      const response = await fetch(`http://localhost:8010/schedules/${scheduleId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        const updatedSchedule = await response.json();
        setSchedules(schedules.map(schedule => 
          schedule.schedule_id === scheduleId ? updatedSchedule : schedule
        ));
      } else if (response.status === 404) {
        // API가 없으면 localStorage로 전환
        setUseLocalStorage(true);
        handleStatusChange(scheduleId, newStatus); // localStorage로 다시 시도
      } else {
        const error = await response.json();
        alert(`상태 변경 실패: ${error.detail || '오류가 발생했습니다.'}`);
      }
    } catch (error) {
      console.error('상태 변경 오류:', error);
      setUseLocalStorage(true);
      handleStatusChange(scheduleId, newStatus); // localStorage로 다시 시도
    }
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
          {useLocalStorage && (
            <span style={{ marginLeft: '10px', color: '#ff9800', fontSize: '0.9rem' }}>
              (로컬 저장 모드)
            </span>
          )}
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
                    value={newSchedule.schedule_time.substring(0, 5)}
                    onChange={(e) => setNewSchedule({...newSchedule, schedule_time: e.target.value + ':00'})}
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
          
          {loading ? (
            <div className="loading-container">
              <p>일정을 불러오는 중입니다...</p>
            </div>
          ) : filteredSchedules.length === 0 ? (
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
                <div key={schedule.schedule_id} className="schedule-item">
                  <div className="schedule-time">
                    <div className="time">{schedule.schedule_time ? schedule.schedule_time.substring(0, 5) : ''}</div>
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
                      <div className="schedule-detail-item">
                        <span className="schedule-detail-label">📍</span>
                        <span>{schedule.location}</span>
                      </div>
                      <div className="schedule-detail-item">
                        <span className="schedule-detail-label">👤</span>
                        <span>{schedule.contact_person}</span>
                      </div>
                      {schedule.memo && (
                        <div className="schedule-detail-item">
                          <span className="schedule-detail-label">📝</span>
                          <span>{schedule.memo}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="schedule-status">
                    <select 
                      className="status-select"
                      value={schedule.status}
                      onChange={(e) => handleStatusChange(schedule.schedule_id, e.target.value)}
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
                        onClick={() => handleDeleteSchedule(schedule.schedule_id)}
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