import React, { useState, useEffect } from 'react';
import { analyzeClient, getClientHealthCheck } from '../services/api';
import './ClientAnalysis.css';

const ClientAnalysis = () => {
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [currentReport, setCurrentReport] = useState(null);
  const [serviceStatus, setServiceStatus] = useState(null);

  // 컴포넌트 마운트 시 서비스 상태 확인
  useEffect(() => {
    checkServiceHealth();
    loadAnalysisHistory();
  }, []);

  const checkServiceHealth = async () => {
    try {
      const health = await getClientHealthCheck();
      setServiceStatus(health);
      console.log('Client Agent 서비스 상태:', health);
    } catch (error) {
      console.error('서비스 상태 확인 실패:', error);
      setError('거래처 분석 서비스가 준비되지 않았습니다.');
    }
  };

  const loadAnalysisHistory = () => {
    // localStorage에서 분석 히스토리 불러오기
    const savedHistory = localStorage.getItem('clientAnalysisHistory');
    if (savedHistory) {
      try {
        const history = JSON.parse(savedHistory);
        setAnalysisHistory(history);
      } catch (error) {
        console.error('분석 히스토리 로드 실패:', error);
      }
    }
  };

  const saveAnalysisHistory = (newAnalysis) => {
    const updatedHistory = [newAnalysis, ...analysisHistory].slice(0, 10); // 최대 10개 저장
    setAnalysisHistory(updatedHistory);
    localStorage.setItem('clientAnalysisHistory', JSON.stringify(updatedHistory));
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMsg = inputMessage.trim();
    setInputMessage('');
    setLoading(true);
    setError(null);
    
    // 사용자 메시지 추가
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMsg,
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, newUserMessage]);
    
    try {
      // API 호출
      const response = await analyzeClient({
        query: userMsg,
        generate_docs: true
      });
      
      if (response.success) {
        // AI 응답 메시지 추가
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: response.final_report || '분석이 완료되었습니다.',
          data: response,
          timestamp: new Date().toISOString()
        };
        setChatHistory(prev => [...prev, aiMessage]);
        
        // 현재 보고서 설정
        setCurrentReport(response);
        setSelectedAnalysis(`${response.company_name || '분석'} 보고서`);
        
        // 분석 히스토리에 추가
        const historyItem = {
          id: Date.now(),
          company_name: response.company_name,
          query: userMsg,
          timestamp: new Date().toISOString(),
          report: response.final_report,
          grade: response.grade_result
        };
        saveAnalysisHistory(historyItem);
      } else {
        throw new Error(response.error || '분석 실패');
      }
    } catch (error) {
      console.error('거래처 분석 실패:', error);
      setError(error.message || '거래처 분석 중 오류가 발생했습니다.');
      
      // 오류 메시지 추가
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `오류: ${error.message || '분석 중 문제가 발생했습니다.'}`,
        timestamp: new Date().toISOString()
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewAnalysis = () => {
    setChatHistory([]);
    setCurrentReport(null);
    setSelectedAnalysis(null);
    setError(null);
  };

  const handleSelectHistory = (item) => {
    setSelectedAnalysis(`${item.company_name} 보고서`);
    setCurrentReport({
      company_name: item.company_name,
      final_report: item.report,
      grade_result: item.grade
    });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleSendMessage();
    }
  };

  return (
    <div className="client-page">
      {/* Left Sidebar */}
      <div className="client-sidebar">
        <h2>고객 분석</h2>
        
        <button className="new-analysis-btn" onClick={handleNewAnalysis}>
          <span className="plus-icon">+</span>
          새로운 고객 분석
        </button>

        <div className="existing-analyses">
          <h3>분석 히스토리</h3>
          {analysisHistory.length > 0 ? (
            analysisHistory.map((item) => (
              <div 
                key={item.id} 
                className="analysis-item"
                onClick={() => handleSelectHistory(item)}
                style={{ cursor: 'pointer' }}
              >
                <span className="analysis-icon">📊</span>
                <span className="analysis-name">
                  {item.company_name || '분석'} - {new Date(item.timestamp).toLocaleDateString()}
                </span>
                <span className="analysis-arrow">›</span>
              </div>
            ))
          ) : (
            <div className="no-analyses">
              <p>분석 히스토리가 없습니다.</p>
            </div>
          )}
        </div>
      </div>

      {/* Center Content Area */}
      <div className="client-main">
        <div className="analysis-content">
          <h1>{selectedAnalysis || '거래처 분석'}</h1>
          
          {error && (
            <div className="error-message" style={{ 
              padding: '10px', 
              backgroundColor: '#ffebee', 
              color: '#c62828', 
              borderRadius: '4px',
              marginBottom: '20px'
            }}>
              {error}
            </div>
          )}
          
          <div className="analysis-body">
            {currentReport ? (
              <div className="report-container">
                {currentReport.final_report && (
                  <div className="report-section">
                    <h2>📋 분석 보고서</h2>
                    <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                      {currentReport.final_report}
                    </pre>
                  </div>
                )}
                
                {currentReport.grade_result && (
                  <div className="report-section">
                    <h2>📊 등급 평가</h2>
                    <div className="grade-info">
                      <p><strong>최종 등급:</strong> {currentReport.grade_result.final_grade || 'N/A'}</p>
                      <p><strong>점수:</strong> {currentReport.grade_result.total_score || 0}점</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
                <p>거래처를 선택하거나 새로운 분석을 시작하세요.</p>
                <p>예: "서울대병원 2024년 1월부터 12월까지 분석해줘"</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - AI Assistant */}
      <div className="client-ai-panel">
        <h2>고객 분석 요청</h2>
        
        <div className="chat-container">
          {chatHistory.map((message) => (
            <div key={message.id} className={`message ${message.type}-message`}>
              {message.type === 'ai' && <div className="ai-avatar">🤖</div>}
              <div className="message-content">
                {message.content}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message ai-message">
              <div className="ai-avatar">🤖</div>
              <div className="message-content">
                <div className="loading-dots">
                  분석 중<span>.</span><span>.</span><span>.</span>
                </div>
              </div>
            </div>
          )}
          
          {chatHistory.length === 0 && !loading && (
            <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
              <p>거래처 분석을 시작하세요.</p>
              <p style={{ fontSize: '0.9em', marginTop: '10px' }}>
                예시:<br/>
                "서울대병원 2024년 분석해줘"<br/>
                "ABC회사 등급 평가해줘"
              </p>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="input-area">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="거래처명과 분석 기간을 입력하세요..."
            className="message-input"
            disabled={loading}
          />
          <button 
            onClick={handleSendMessage}
            className="send-button"
            disabled={loading || !inputMessage.trim()}
          >
            <span className="send-icon">{loading ? '⏳' : '➤'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ClientAnalysis;