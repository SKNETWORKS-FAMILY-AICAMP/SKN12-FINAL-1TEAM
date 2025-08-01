import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatScreen.css';

function ChatScreen() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
      timestamp: new Date().toLocaleString(),
      agentType: null
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
  const [userId] = useState(() => 'user_' + Math.random().toString(36).substr(2, 9));
  
  const messagesEndRef = useRef(null);
  const DEBUG_MODE = true;

  // 디버깅 로그 함수
  const debugLog = (message, data = null) => {
    if (DEBUG_MODE) {
      console.log(`[DEBUG] ${message}`, data);
    }
  };

  // 스크롤을 맨 아래로 이동
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Agent 표시 정보 반환 함수
  const getAgentDisplayInfo = (agentType) => {
    const agentMap = {
      'search_agent': {
        name: '🔍 SEARCH_AGENT',
        icon: 'fas fa-search'
      },
      'employee_db_agent': {
        name: '👥 직원 정보',
        icon: 'fas fa-users'
      },
      'client_analysis_agent': {
        name: '📊 고객 분석',
        icon: 'fas fa-chart-line'
      },
      'rule_compliance_agent': {
        name: '📋 규정 분석',
        icon: 'fas fa-shield-alt'
      },
      'general_chat': {
        name: '💬 일반 대화',
        icon: 'fas fa-comments'
      }
    };
    
    return agentMap[agentType] || {
      name: `🤖 ${agentType}`,
      icon: 'fas fa-robot'
    };
  };

  // 메시지 전송 함수 (스트리밍 방식)
  const sendMessage = async () => {
    const message = inputMessage.trim();
    if (!message || isLoading) return;

    debugLog('메시지 전송 시작', { message: message.substring(0, 50) + '...' });

    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: message,
      timestamp: new Date().toLocaleString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // 봇 메시지 컨테이너 생성 (스트리밍용)
    const botMessageId = Date.now() + 1;
    const initialBotMessage = {
      id: botMessageId,
      sender: 'ai',
      content: '',
      timestamp: new Date().toLocaleString(),
      agentType: null,
      isStreaming: true
    };
    setMessages(prev => [...prev, initialBotMessage]);

    let currentContent = '';
    let agentType = 'unknown';
    let finalData = null;
    let hasError = false;

    try {
      const endpoint = 'http://localhost:8000/api/route/router';
      
      debugLog('스트리밍 API 호출', { endpoint, message: message.substring(0, 50) + '...' });
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: message
        })
      });

      console.log('🌐 API 응답 받음:', { status: response.status, ok: response.ok, headers: Object.fromEntries(response.headers.entries()) });
      debugLog('API 응답 받음', { status: response.status, ok: response.ok });

      if (!response.ok) {
        const errorText = await response.text();
        debugLog('API 오류 응답', { status: response.status, error: errorText });
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      // 일반 JSON 응답 처리
      const responseData = await response.json();
      console.log('📦 라우터 응답 받음:', responseData);
      debugLog('라우터 응답 받음', responseData);
      
      // 응답에서 에이전트 타입과 내용 추출
      if (responseData.success) {
        agentType = responseData.agent || 'unknown';
        currentContent = responseData.response || responseData.message || '응답을 처리했습니다.';
        finalData = responseData;
      } else {
        throw new Error(responseData.error || '라우터 처리 중 오류가 발생했습니다.');
      }
      
      // 최종 메시지 업데이트
      setMessages(prev => prev.map(msg => 
        msg.id === botMessageId 
          ? { ...msg, content: currentContent, agentType: agentType, isStreaming: false }
          : msg
      ));

    } catch (error) {
      debugLog('스트리밍 메시지 전송 오류', error);
      
      // 에러 메시지 표시 (하나의 메시지로 통합)
      let errorMessage = `죄송합니다. 오류가 발생했습니다: ${error.message}`;
      if (DEBUG_MODE) {
        errorMessage += `\n\n디버그 정보: ${error.stack || error.message}`;
      }
      
      setMessages(prev => prev.map(msg => 
        msg.id === botMessageId 
          ? { ...msg, content: errorMessage, isStreaming: false }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    if (window.confirm('모든 대화를 지우시겠습니까?')) {
      setMessages([{
        id: Date.now(),
        sender: 'ai',
        content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
        timestamp: new Date().toLocaleString(),
        agentType: null
      }]);
    }
  };

  // 링크 클릭 처리 함수
  const handleLinkClick = (url) => {
    window.open(url, '_blank');
  };

  // 메시지 내용에서 링크를 클릭 가능한 형태로 변환
  const renderMessageContent = (content) => {
    if (!content || typeof content !== 'string') {
      return content;
    }

    try {
      // 마크다운 링크 패턴: [텍스트](URL)
      const markdownLinkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
      
      // 일반 URL 패턴: http://로 시작하는 URL
      const urlPattern = /(https?:\/\/[^\s]+)/g;
      
      // 마크다운 링크를 찾아서 React 요소로 변환
      const parts = [];
      let lastIndex = 0;
      let match;
      
      // 마크다운 링크 처리
      while ((match = markdownLinkPattern.exec(content)) !== null) {
        // 링크 앞의 텍스트 추가
        if (match.index > lastIndex) {
          parts.push(content.slice(lastIndex, match.index));
        }
        
        // 링크 요소 생성
        parts.push(
          <a
            key={`link-${parts.length}`}
            href={match[2]}
            className="download-link"
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => {
              e.preventDefault();
              handleLinkClick(match[2]);
            }}
          >
            {match[1]}
          </a>
        );
        
        lastIndex = markdownLinkPattern.lastIndex;
      }
      
      // 남은 텍스트 추가
      if (lastIndex < content.length) {
        const remainingText = content.slice(lastIndex);
        
        // 남은 텍스트에서 일반 URL 처리
        const urlParts = remainingText.split(urlPattern);
        const processedParts = urlParts.map((part, index) => {
          if (urlPattern.test(part)) {
            return (
              <a
                key={`url-${index}`}
                href={part}
                className="download-link"
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => {
                  e.preventDefault();
                  handleLinkClick(part);
                }}
              >
                {part}
              </a>
            );
          }
          return part;
        });
        
        parts.push(...processedParts);
      }
      
      return parts.length > 0 ? parts : content;
      
    } catch (error) {
      console.error('링크 렌더링 오류:', error);
      return content;
    }
  };

  return (
    <div className="chat-screen">
      <div className="chat-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">Pharma-Helper</span>
          </div>
        </div>
        <div className="header-center">
        </div>
        <div className="header-right">
          <nav className="header-nav">
            <a href="#" className="nav-link" onClick={(e) => { e.preventDefault(); navigate('/'); }}>홈</a>
            <a href="#" className="nav-link active">AI 채팅</a>
            <a href="#" className="nav-link">고객/데이터 위키</a>
            <a href="#" className="nav-link">문서 생성</a>
            <a href="#" className="nav-link">실적 확인</a>
          </nav>
          <div className="header-actions">
            <button className="notification-btn">🔔</button>
            <div className="user-profile">
              <img src="https://via.placeholder.com/32x32" alt="User" />
            </div>
          </div>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-sidebar">
          <div className="chat-history">
            <h3>Chat</h3>
            <button className="new-chat-btn" onClick={clearChat}>+ New Chat</button>
          </div>
        </div>

        <div className="chat-main">
          
          <div className="messages-container">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender}-message ${message.isStreaming ? 'streaming' : ''}`}>
                <div className="message-content">
                  {renderMessageContent(message.content)}
                  {message.isStreaming && <span className="typing-indicator">...</span>}
                </div>
                {message.agentType && (
                  <div className="agent-badge">
                    {getAgentDisplayInfo(message.agentType).name}
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="message-input-container">
            <input
              type="text"
              placeholder="Type your message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              className="message-input"
              disabled={isLoading}
            />
            <button onClick={sendMessage} className="send-button" disabled={isLoading}>
              {isLoading ? '전송 중...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatScreen; 