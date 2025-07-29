import React, { useState, useEffect, useRef } from 'react';
import './ChatScreen.css';

const ChatScreen = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState('router');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [currentSessionAgent, setCurrentSessionAgent] = useState(null); // 현재 세션의 고정 에이전트
  const messagesEndRef = useRef(null);

  // session_id 생성 함수
  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

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

  // 백엔드에서 채팅 내역 불러오기
  const loadChatHistoryFromBackend = async () => {
    try {
      console.log('🔄 백엔드에서 채팅 내역 불러오는 중...');
      const response = await fetch('http://localhost:8000/api/router/chat-history');
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.chatHistory) {
          console.log(`✅ 백엔드에서 ${data.count}개 채팅 불러옴`);
          setChatHistory(data.chatHistory);
          
          // localStorage와 동기화
          localStorage.setItem('chatHistory', JSON.stringify(data.chatHistory));
          
          return data.chatHistory;
        }
      }
      
      console.log('⚠️ 백엔드에서 채팅 내역 없음, localStorage 사용');
      // 백엔드에 데이터가 없으면 localStorage 사용
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        const localHistory = JSON.parse(savedHistory);
        setChatHistory(localHistory);
        return localHistory;
      }
      
      return [];
    } catch (error) {
      console.error('❌ 채팅 내역 불러오기 실패:', error);
      
      // 오류 시 localStorage 폴백
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        const localHistory = JSON.parse(savedHistory);
        setChatHistory(localHistory);
        return localHistory;
      }
      
      return [];
    }
  };

  // 초기 안내 메시지
  useEffect(() => {
    const initializeChat = async () => {
      const initialMessage = {
        type: 'system',
        content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages([initialMessage]);
      
      // 백엔드에서 채팅 내역 불러오기
      const history = await loadChatHistoryFromBackend();
      
      // 채팅 내역이 없으면 새 채팅 시작
      if (history.length === 0) {
        console.log('📝 새 채팅 시작');
        startNewChat();
      }
    };
    
    initializeChat();
  }, []);

  // 새로운 채팅 시작
  const startNewChat = () => {
    const chatId = Date.now().toString();
    const newSessionId = generateSessionId();
    const initialMessage = {
      type: 'system',
      content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages([initialMessage]);
    setCurrentChatId(chatId);
    setSessionId(newSessionId);
    
    // 새 채팅을 히스토리에 추가
    const newChat = {
      id: chatId,
      sessionId: newSessionId,
      title: `채팅 ${new Date().toLocaleString()}`,
      messages: [initialMessage],
      createdAt: new Date().toISOString()
    };
    
    const updatedHistory = [newChat, ...chatHistory];
    setChatHistory(updatedHistory);
    localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
  };

  // 채팅 내역 선택
  const selectChat = async (chatId) => {
    const selectedChat = chatHistory.find(chat => chat.id === chatId);
    if (selectedChat) {
      setCurrentChatId(chatId);
      setSessionId(selectedChat.sessionId);
      
      // 메시지가 이미 로드되어 있으면 바로 사용
      if (selectedChat.messages && selectedChat.messages.length > 0) {
        setMessages(selectedChat.messages);
      } else {
        // 백엔드에서 메시지 불러오기
        try {
          console.log(`🔄 세션 ${selectedChat.sessionId}의 메시지 불러오는 중...`);
          const response = await fetch(`http://localhost:8000/api/router/sessions/${selectedChat.sessionId}/messages`);
          
          if (response.ok) {
            const data = await response.json();
            if (data.success && data.messages) {
              console.log(`✅ ${data.count}개 메시지 불러옴`);
              setMessages(data.messages);
              
              // 채팅 히스토리 업데이트
              const updatedHistory = chatHistory.map(chat => 
                chat.id === chatId 
                  ? { ...chat, messages: data.messages }
                  : chat
              );
              setChatHistory(updatedHistory);
              localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
            }
          } else {
            console.error('메시지 불러오기 실패');
            setMessages(selectedChat.messages || []);
          }
        } catch (error) {
          console.error('메시지 불러오기 오류:', error);
          setMessages(selectedChat.messages || []);
        }
      }
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
          requestBody = { 
            session_id: sessionId,
            query: currentQuery 
          };
          break;
        case 'employee':
          requestBody = {
            session_id: sessionId,
            employee_name: "최수아",
            period: "202312~202403",
            save_report: false
          };
          break;
        case 'client':
          requestBody = {
            session_id: sessionId,
            client_name: "서울의료센터",
            analysis_type: "종합분석",
            save_report: false
          };
          break;
        case 'docs':
          requestBody = {
            user_input: currentQuery  // text -> user_input으로 변경
          };
          break;
        default:
          requestBody = { 
            session_id: sessionId,
            query: currentQuery 
          };
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
            botResponseContent = `📄 문서 분류 완료!\n\n• 문서 타입: ${data.state?.doc_type}\n• 상태: 분류 성공\n• 템플릿: ${data.state?.template_content ? '준비됨' : '준비 중'}`;
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

      // 에이전트가 새로 선택되었거나 변경된 경우 현재 에이전트 정보 갱신
      if (data.agent_selected || data.agent_fixed) {
        checkCurrentAgent(sessionId);
      }

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
          session_id: sessionId,
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

      // 에이전트가 선택된 경우 현재 에이전트 정보 갱신
      if (data.success) {
        checkCurrentAgent(sessionId);
      }

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

  // 현재 세션의 선택된 에이전트 확인
  const checkCurrentAgent = async (sessionId) => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/router/current-agent/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.has_selected_agent) {
          setCurrentSessionAgent(data.agent_info);
          console.log(`✅ 현재 세션 에이전트: ${data.agent_info.agent_name}`);
        } else {
          setCurrentSessionAgent(null);
          console.log('📝 현재 세션에 고정된 에이전트 없음');
        }
      }
    } catch (error) {
      console.error('❌ 현재 에이전트 확인 실패:', error);
    }
  };

  useEffect(() => {
    checkCurrentAgent(sessionId);
  }, [sessionId]);

  // 에이전트 초기화
  const resetAgent = async () => {
    if (!sessionId) return;
    
    if (!window.confirm('현재 에이전트를 초기화하시겠습니까?\n다음 질문부터 새로운 에이전트가 선택됩니다.')) {
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/router/reset-agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setCurrentSessionAgent(null);
          
          // 시스템 메시지 추가
          const resetMessage = {
            type: 'system',
            content: data.message,
            timestamp: new Date().toLocaleTimeString(),
            agent: 'System'
          };
          
          const updatedMessages = [...messages, resetMessage];
          setMessages(updatedMessages);
          saveMessageToHistory(updatedMessages);
          
          console.log('✅ 에이전트 초기화 완료');
        }
      }
    } catch (error) {
      console.error('❌ 에이전트 초기화 실패:', error);
    }
  };

  return (
    <div className="chat-screen">
      {/* Main Content */}
      <div className="chat-container">
        {/* Chat Management Panel */}
        <aside className="chat-panel">
          <div className="chat-management">
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
            
            {/* 현재 세션 에이전트 표시 */}
            {currentSessionAgent ? (
              <div className="current-agent-info">
                <div className="agent-badge">
                  🎯 <strong>{currentSessionAgent.agent_name}</strong> (고정됨)
                </div>
                <button 
                  className="reset-agent-btn"
                  onClick={resetAgent}
                  title="에이전트 초기화"
                >
                  🔄 초기화
                </button>
              </div>
            ) : (
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
            )}
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