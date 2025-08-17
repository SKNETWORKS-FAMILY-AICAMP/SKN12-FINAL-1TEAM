import React, { useState, useEffect, useRef } from 'react';
import { 
  getEmployeeList, 
  analyzeEmployeePerformance,
  getDashboardStats 
} from '../services/api';
import './EmployeePerformance.css';

const EmployeePerformance = ({ currentUser }) => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // 분석 히스토리 관련 상태
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  
  // 채팅 형식의 메시지 관련 상태
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);
  
  // 대시보드 통계 상태
  const [dashboardStats, setDashboardStats] = useState(null);
  
  const isAdmin = currentUser?.role === 'admin';

  // 사용자별 localStorage 키 생성 함수
  const getUserHistoryKey = () => {
    if (!currentUser) return 'employeeAnalysisHistory_guest';
    // 사용자 ID나 이메일을 기반으로 고유 키 생성
    const userId = currentUser.employee_id || currentUser.email || currentUser.username || 'unknown';
    return `employeeAnalysisHistory_${userId}`;
  };

  // 컴포넌트 마운트 시 직원 목록 가져오기 (관리자만)
  useEffect(() => {
    console.log('EmployeePerformance - Current User:', currentUser);
    console.log('EmployeePerformance - Is Admin:', isAdmin);
    
    if (isAdmin) {
      fetchEmployeeList();
    } else if (currentUser) {
      setSelectedEmployee(currentUser.name || currentUser.username || currentUser.email);
      console.log('Set selected employee to:', currentUser.name || currentUser.username || currentUser.email);
    }
    
    // 대시보드 통계 가져오기
    fetchDashboardStats();
    
    // localStorage에서 사용자별 분석 히스토리 불러오기
    if (currentUser) {
      const userHistoryKey = getUserHistoryKey();
      const savedHistory = localStorage.getItem(userHistoryKey);
      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          setAnalysisHistory(parsed);
        } catch (error) {
          console.error('분석 히스토리 불러오기 실패:', error);
        }
      } else {
        // 새 사용자의 경우 빈 히스토리로 초기화
        setAnalysisHistory([]);
      }
    }
  }, [isAdmin, currentUser]);

  // 메시지 변경 시 자동 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchEmployeeList = async () => {
    try {
      const data = await getEmployeeList();
      setEmployees(data.employees || []);
      if (data.employees && data.employees.length > 0) {
        setSelectedEmployee(data.employees[0].name);
      }
    } catch (error) {
      console.error('직원 목록 조회 실패:', error);
      setError('직원 목록을 불러오는데 실패했습니다.');
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const data = await getDashboardStats();
      console.log('Dashboard stats:', data);
      setDashboardStats(data);
    } catch (error) {
      console.error('대시보드 통계 조회 실패:', error);
      // 실패해도 기본값으로 표시
      setDashboardStats({
        stats: [
          {
            title: "목표 달성률",
            value: "0%",
            change: "0%",
            trend: "neutral",
            period: "이번 달"
          },
          {
            title: "매출 증감률",
            value: "0%",
            change: "₩0",
            trend: "neutral",
            period: "전월 대비"
          },
          {
            title: "분기 총 실적",
            value: "₩0",
            change: "0개 거래처",
            trend: "neutral",
            period: "최근 3개월"
          }
        ]
      });
    }
  };

  const handleAnalysis = async () => {
    if (!analysisQuery) {
      setError('분석할 내용을 입력해주세요.');
      return;
    }

    setLoading(true);
    setError('');
    
    // 디버깅용 로그
    console.log('Current User:', currentUser);
    console.log('Is Admin:', isAdmin);
    console.log('Selected Employee:', selectedEmployee);
    
    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: analysisQuery,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    try {
      console.log('Current User:', currentUser);
      console.log('Is Admin:', isAdmin);
      console.log('Original Query:', analysisQuery);
      
      // 관리자인 경우에만 직원명 전달, 일반 사용자는 백엔드에서 자동 처리
      let requestData = {
        query: analysisQuery
      };
      
      // 관리자가 특정 직원을 선택한 경우에만 employee_name 추가
      if (isAdmin && selectedEmployee) {
        requestData.employee_name = selectedEmployee;
        console.log('Admin selected employee:', selectedEmployee);
      }
      
      console.log('Request data:', requestData);
      
      const result = await analyzeEmployeePerformance(requestData);
      
      // AI 응답 메시지 추가
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: result.report || JSON.stringify(result, null, 2),
        data: result,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
      
      // 현재 분석 결과 저장
      setCurrentAnalysis(result);
      
      // 히스토리에 추가
      const newHistoryItem = {
        id: Date.now(),
        title: `${isAdmin ? selectedEmployee : currentUser?.name} - ${new Date().toLocaleString('ko-KR')}`,
        query: analysisQuery,
        result: result,
        messages: [...messages, userMessage, aiMessage],
        timestamp: new Date().toISOString()
      };
      
      const updatedHistory = [...analysisHistory, newHistoryItem];
      setAnalysisHistory(updatedHistory);
      setActiveHistoryId(newHistoryItem.id);
      
      // 사용자별 localStorage에 저장
      const userHistoryKey = getUserHistoryKey();
      localStorage.setItem(userHistoryKey, JSON.stringify(updatedHistory));
      
    } catch (error) {
      console.error('분석 실패:', error);
      setError('분석에 실패했습니다.');
      
      // 에러 메시지 추가
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: '분석 중 오류가 발생했습니다.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setAnalysisQuery('');
    }
  };

  // 히스토리 항목 선택
  const selectHistory = (historyItem) => {
    setActiveHistoryId(historyItem.id);
    setMessages(historyItem.messages || []);
    setCurrentAnalysis(historyItem.result);
  };

  // 새 분석 시작
  const startNewAnalysis = () => {
    setActiveHistoryId(null);
    setMessages([]);
    setCurrentAnalysis(null);
  };

  // 히스토리 삭제
  const deleteHistory = (historyId) => {
    const updatedHistory = analysisHistory.filter(item => item.id !== historyId);
    setAnalysisHistory(updatedHistory);
    const userHistoryKey = getUserHistoryKey();
    localStorage.setItem(userHistoryKey, JSON.stringify(updatedHistory));
    
    if (activeHistoryId === historyId) {
      startNewAnalysis();
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW'
    }).format(amount);
  };

  return (
    <div className="employee-performance">
      <div className="performance-header">
        <h1>직원 실적 관리</h1>
        {!isAdmin && currentUser && (
          <p className="current-employee">현재 직원: {currentUser.name}</p>
        )}
      </div>

      <div className="performance-layout">
        {/* 왼쪽: 메모리 세션 (히스토리) */}
        <div className="history-sidebar">
          <div className="sidebar-header">
            <h3>분석 히스토리</h3>
            <button className="new-analysis-btn" onClick={startNewAnalysis}>
              + 새 분석
            </button>
          </div>
          <div className="history-list">
            {analysisHistory.length === 0 ? (
              <div className="empty-history">
                아직 분석 기록이 없습니다
              </div>
            ) : (
              analysisHistory.map(item => (
                <div 
                  key={item.id}
                  className={`history-item ${activeHistoryId === item.id ? 'active' : ''}`}
                  onClick={() => selectHistory(item)}
                >
                  <div className="history-title">{item.title}</div>
                  <div className="history-date">
                    {new Date(item.timestamp).toLocaleDateString('ko-KR')}
                  </div>
                  <button 
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistory(item.id);
                    }}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 가운데: 메인 콘텐츠 */}
        <div className="main-content">
          <div className="search-section">
            {isAdmin && (
              <div className="control-group">
                <label>직원 선택</label>
                <select 
                  value={selectedEmployee} 
                  onChange={(e) => setSelectedEmployee(e.target.value)}
                  className="employee-select"
                >
                  <option value="">직원을 선택하세요</option>
                  {employees.map((emp) => (
                    <option key={emp.employee_id} value={emp.name}>
                      {emp.name} (사번: {emp.사번})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="analysis-controls">
              <div className="control-group full-width">
                <label>실적 분석 쿼리</label>
                <input
                  type="text"
                  value={analysisQuery}
                  onChange={(e) => setAnalysisQuery(e.target.value)}
                  placeholder="예: 2024년 3분기 실적을 분석해주세요"
                  className="analysis-input"
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalysis()}
                />
              </div>
              <button onClick={handleAnalysis} className="analysis-btn" disabled={loading}>
                {loading ? '분석 중...' : '분석하기'}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* 실적 요약 카드 - 항상 표시 (대시보드 통계 사용) */}
          {dashboardStats && dashboardStats.stats && (
            <div className="performance-summary-cards">
              {dashboardStats.stats.map((stat, index) => (
                <div key={index} className="summary-card">
                  <div className="card-title">{stat.title}</div>
                  <div className="card-value">
                    {stat.value}
                  </div>
                  <div className={`card-change ${stat.trend === 'up' ? 'positive' : stat.trend === 'down' ? 'negative' : ''}`}>
                    {stat.change}
                  </div>
                  <div className="card-period">
                    {stat.period}
                  </div>
                </div>
              ))}
            </div>
          )}

          {loading && (
            <div className="loading-message">
              데이터를 분석하는 중...
            </div>
          )}
        </div>

        {/* 오른쪽: 채팅창 형식의 분석 결과 */}
        <div className="chat-sidebar">
          <div className="chat-header">
            <h3>분석 대화</h3>
          </div>
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="empty-chat">
                분석 쿼리를 입력하여 대화를 시작하세요
              </div>
            ) : (
              messages.map(message => (
                <div key={message.id} className={`message ${message.type}`}>
                  <div className="message-header">
                    <span className="message-sender">
                      {message.type === 'user' ? '사용자' : message.type === 'ai' ? 'AI 분석' : '시스템'}
                    </span>
                    <span className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString('ko-KR')}
                    </span>
                  </div>
                  <div className="message-content">
                    {message.type === 'ai' && message.data ? (
                      <div className="analysis-result-content">
                        {message.data.report ? (
                          <div className="report-text">
                            {message.data.report.split('\n').map((paragraph, index) => (
                              paragraph.trim() && <p key={index}>{paragraph}</p>
                            ))}
                          </div>
                        ) : (
                          <pre>{JSON.stringify(message.data, null, 2)}</pre>
                        )}
                        
                        {message.data.summary?.grade && (
                          <div className="grade-badge">
                            등급: {message.data.summary.grade}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p>{message.content}</p>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeePerformance;