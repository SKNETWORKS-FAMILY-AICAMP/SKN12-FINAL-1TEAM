import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import './ChatScreen.css';

const ChatScreen = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState('router');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const messagesEndRef = useRef(null);

  // 4개 에이전트 정보
  const agents = {
    router: {
      name: 'Router Agent',
      endpoint: '/api/router/router',
      description: '쿼리를 분석하고 적절한 에이전트로 자동 라우팅',
      color: '#3b82f6'
    },
    employee: {
      name: 'Employee Agent',
      endpoint: '/api/employee/analyze',
      description: '직원 실적 분석 및 평가',
      color: '#10b981'
    },
    client: {
      name: 'Client Agent',
      endpoint: '/api/client/analyze',
      description: '고객/거래처 분석 및 영업 전략',
      color: '#f59e0b'
    },
    docs: {
      name: 'Docs Agent',
      endpoint: '/api/docs/classify',
      description: '문서 분류 및 생성',
      color: '#8b5cf6'
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 초기 안내 메시지
  useEffect(() => {
    const initialMessage = {
      type: 'system',
      content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages([initialMessage]);
    
    // 로컬 스토리지에서 채팅 내역 불러오기
    const savedHistory = localStorage.getItem('chatHistory');
    if (savedHistory) {
      setChatHistory(JSON.parse(savedHistory));
    }
  }, []);

  // 새로운 채팅 시작
  const startNewChat = () => {
    const chatId = Date.now().toString();
    const initialMessage = {
      type: 'system',
      content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages([initialMessage]);
    setCurrentChatId(chatId);
    
    // 새 채팅을 히스토리에 추가
    const newChat = {
      id: chatId,
      title: `채팅 ${new Date().toLocaleString()}`,
      messages: [initialMessage],
      createdAt: new Date().toISOString()
    };
    
    const updatedHistory = [newChat, ...chatHistory];
    setChatHistory(updatedHistory);
    localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
  };

  // 채팅 내역 선택
  const selectChat = (chatId) => {
    const selectedChat = chatHistory.find(chat => chat.id === chatId);
    if (selectedChat) {
      setMessages(selectedChat.messages);
      setCurrentChatId(chatId);
    }
  };

  // 채팅 내역 초기화
  const clearAllChats = () => {
    if (window.confirm('모든 채팅 내역을 삭제하시겠습니까?')) {
      setChatHistory([]);
      localStorage.removeItem('chatHistory');
      startNewChat();
    }
  };

  // 메시지 저장 (채팅 내역 업데이트)
  const saveMessageToHistory = (newMessages) => {
    if (currentChatId) {
      const updatedHistory = chatHistory.map(chat => {
        if (chat.id === currentChatId) {
          return {
            ...chat,
            messages: newMessages,
            title: newMessages.length > 1 ? 
              newMessages[1].content.substring(0, 30) + '...' : 
              chat.title
          };
        }
        return chat;
      });
      setChatHistory(updatedHistory);
      localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString()
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);
    const currentQuery = inputValue;
    setInputValue('');

    try {
      const agent = agents[selectedAgent];
      let requestBody = {};
      
      // 에이전트별 요청 데이터 구성
      switch (selectedAgent) {
        case 'router':
          requestBody = { query: currentQuery };
          break;
        case 'employee':
          requestBody = {
            employee_name: "최수아",
            period: "202312~202403",
            save_report: false
          };
          break;
        case 'client':
          requestBody = {
            client_name: "서울의료센터",
            analysis_type: "종합분석",
            save_report: false
          };
          break;
        case 'docs':
          requestBody = {
            text: currentQuery,
            file_type: "auto"
          };
          break;
        default:
          requestBody = { query: currentQuery };
      }

      const response = await fetch(`http://localhost:8000${agent.endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      let botResponseContent = '';
      
      if (data.success) {
        // Router 에이전트에서 사용자 선택이 필요한 경우
        if (selectedAgent === 'router' && data.needs_user_selection) {
          const selectionMessage = {
            type: 'agent_selection',
            content: data.message,
            timestamp: new Date().toLocaleTimeString(),
            agent: 'Router Agent',
            query: currentQuery,
            available_agents: data.available_agents,
            agent_descriptions: data.agent_descriptions,
            agent_display_names: data.agent_display_names
          };
          
          const messagesWithSelection = [...newMessages, selectionMessage];
          setMessages(messagesWithSelection);
          saveMessageToHistory(messagesWithSelection);
          return;
        }
        
        switch (selectedAgent) {
          case 'router':
            botResponseContent = `🎯 라우팅 결과: ${data.agent}\n\n${data.response}\n\n분류 상세:\n• 선택된 에이전트: ${data.agent}\n• 라우팅 시도 횟수: ${data.routing_attempts}\n• 분류 결과: ${data.classification_result}`;
            break;
          case 'employee':
            botResponseContent = `📊 직원 실적 분석 완료!\n\n${data.report}`;
            break;
          case 'client':
            botResponseContent = `🏥 고객 분석 완료!\n\n${data.report}`;
            break;
          case 'docs':
            botResponseContent = `📄 문서 분류 완료!\n\n• 문서 타입: ${data.result?.document_type}\n• 신뢰도: ${(data.result?.confidence * 100).toFixed(1)}%\n• 키워드: ${data.result?.keywords?.join(', ')}\n• 제안 템플릿: ${data.result?.suggested_template}`;
            break;
          default:
            botResponseContent = data.message || '처리가 완료되었습니다.';
        }
      } else {
        botResponseContent = `❌ 오류 발생: ${data.error || data.message}`;
      }

      const botMessage = {
        type: 'bot',
        content: botResponseContent,
        timestamp: new Date().toLocaleTimeString(),
        agent: agent.name
      };

      const finalMessages = [...newMessages, botMessage];
      setMessages(finalMessages);
      saveMessageToHistory(finalMessages);

    } catch (error) {
      console.error('API 요청 오류:', error);
      const errorMessage = {
        type: 'bot',
        content: `❌ 연결 오류: ${error.message}\n\n백엔드 서버가 실행 중인지 확인해주세요. (http://localhost:8000)`,
        timestamp: new Date().toLocaleTimeString(),
        agent: 'System'
      };
      const finalMessages = [...newMessages, errorMessage];
      setMessages(finalMessages);
      saveMessageToHistory(finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  // 에이전트 선택 처리 함수
  const handleAgentSelection = async (query, selectedAgentKey) => {
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/router/select-agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          selected_agent: selectedAgentKey
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      let botResponseContent = '';
      if (data.success) {
        botResponseContent = `🎯 선택된 에이전트: ${data.agent}\n\n${data.response}\n\n처리 결과:\n• 에이전트: ${data.agent}\n• 상태: 사용자 직접 선택\n• 분류 결과: ${data.classification_result}`;
      } else {
        botResponseContent = `❌ 에이전트 선택 처리 오류: ${data.error || data.message}`;
      }

      const botMessage = {
        type: 'bot',
        content: botResponseContent,
        timestamp: new Date().toLocaleTimeString(),
        agent: 'Router Agent'
      };

      const updatedMessages = [...messages, botMessage];
      setMessages(updatedMessages);
      saveMessageToHistory(updatedMessages);

    } catch (error) {
      console.error('에이전트 선택 처리 오류:', error);
      const errorMessage = {
        type: 'bot',
        content: `❌ 에이전트 선택 처리 중 오류 발생: ${error.message}`,
        timestamp: new Date().toLocaleTimeString(),
        agent: 'System'
      };
      const updatedMessages = [...messages, errorMessage];
      setMessages(updatedMessages);
      saveMessageToHistory(updatedMessages);
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

  // 첫 번째 채팅이 없으면 자동으로 생성
  useEffect(() => {
    if (chatHistory.length === 0 && !currentChatId) {
      startNewChat();
    }
  }, []);

  return (
    <div className="chat-screen">
      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">Pharma-Helper</span>
          </div>
        </div>
        
        <div className="header-right">
          <nav className="header-nav">
            <Link to="/" className="nav-link">홈</Link>
            <button 
              className="nav-link ai-btn"
              style={{
                background: '#6c5ce7',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              AI 채팅
            </button>
            <Link to="/performance" className="nav-link">고객/데이터 위기</Link>
            <Link to="/" className="nav-link">문서 생성</Link>
            <Link to="/" className="nav-link">실적 확인</Link>
          </nav>
          
          <div className="header-actions">
            <button className="notification-btn" title="알림">
              🔔
            </button>
            <div className="user-profile">
              <img 
                src="https://via.placeholder.com/32x32.png?text=👤" 
                alt="사용자" 
                title="프로필"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="chat-container">
        {/* Sidebar */}
        <aside className="chat-sidebar">
          <div className="chat-history">
            <h3>Chat</h3>
            <button className="new-chat-btn" onClick={startNewChat}>
              + New Chat
            </button>
            
            <div className="chat-controls">
              <button 
                className="clear-chat-btn" 
                onClick={clearAllChats}
                title="모든 채팅 삭제"
              >
                🗑️ 전체 삭제
              </button>
            </div>
            
            <div className="chat-list">
              {chatHistory.map((chat) => (
                <div 
                  key={chat.id}
                  className={`chat-item ${currentChatId === chat.id ? 'active' : ''}`}
                  onClick={() => selectChat(chat.id)}
                >
                  <span className="chat-icon">💬</span>
                  <div className="chat-info">
                    <div className="chat-title-text">
                      {chat.title}
                    </div>
                    <div className="chat-date">
                      {new Date(chat.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="chat-main">
          <div className="chat-title">
            <h2>AI 채팅</h2>
            <div className="agent-selector">
              <label>에이전트 선택:</label>
              <select 
                value={selectedAgent} 
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="agent-select"
              >
                {Object.entries(agents).map(([key, agent]) => (
                  <option key={key} value={key}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="messages-container">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.type === 'user' ? 'user-message' : 'ai-message'}`}>
                <div className="message-header">
                  <span className="message-sender">
                    {message.type === 'user' ? '👤 사용자' : 
                     message.type === 'system' ? '🤖 시스템' : 
                     `🤖 ${message.agent || 'AI'}`}
                  </span>
                  <span className="message-time">{message.timestamp}</span>
                </div>
                <div className="message-content">
                  {message.type === 'agent_selection' ? (
                    <div>
                      <div style={{marginBottom: '15px'}}>
                        {message.content.split('\n').map((line, i) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                      <div style={{marginBottom: '10px', fontWeight: 'bold', color: '#666'}}>
                        다음 중 하나를 선택해주세요:
                      </div>
                      <div className="agent-selection-buttons">
                        {message.available_agents?.map((agentKey) => (
                          <button
                            key={agentKey}
                            className="agent-selection-btn"
                            onClick={() => handleAgentSelection(message.query, agentKey)}
                            disabled={isLoading}
                          >
                            <div className="agent-btn-title">
                              {message.agent_display_names?.[agentKey] || agentKey}
                            </div>
                            <div className="agent-btn-description">
                              {message.agent_descriptions?.[agentKey]?.substring(0, 100)}...
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    message.content.split('\n').map((line, i) => (
                      <div key={i}>{line}</div>
                    ))
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message ai-message">
                <div className="message-header">
                  <span className="message-sender">🤖 {agents[selectedAgent].name}</span>
                  <span className="message-time">처리 중...</span>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    처리 중<span>.</span><span>.</span><span>.</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="message-input-container">
            <div className="selected-agent-info">
              <span style={{ color: agents[selectedAgent].color }}>
                ● {agents[selectedAgent].name}
              </span>
              <span className="agent-description">
                {agents[selectedAgent].description}
              </span>
            </div>
            <div className="input-area">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="인사정보/거래처분석/실적분석/문서분류 중에 질문해주세요."
                disabled={isLoading}
                className="message-input"
                rows="1"
              />
              <button 
                onClick={sendMessage} 
                disabled={isLoading || !inputValue.trim()}
                className="send-button"
              >
                Send
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ChatScreen; 