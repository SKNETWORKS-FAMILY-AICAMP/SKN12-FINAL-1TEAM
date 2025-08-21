import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatBot.css';

const ChatBot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [selectedAgent, setSelectedAgent] = useState('router');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [currentSessionAgent, setCurrentSessionAgent] = useState(null); // 현재 세션의 고정 에이전트
  const [isWaitingForDocsInput, setIsWaitingForDocsInput] = useState(false); // Docs Agent 입력 대기 상태
  const [docsInputType, setDocsInputType] = useState(null); // Docs Agent 입력 타입
  const messagesEndRef = useRef(null);

  // session_id 생성 함수 - 각 채팅방마다 고유 ID
  const generateSessionId = () => {
    // 새로운 세션 ID 생성 (각 채팅방마다 고유)
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    console.log('새 세션 ID 생성:', newSessionId);
    return newSessionId;
  };

  // 백엔드 에이전트 ID를 프론트엔드 키로 매핑
  const agentKeyMapping = {
    'employee_agent': 'employee',
    'client_agent': 'client',
    'search_agent': 'search',
    'create_document_agent': 'docs'
  };

  // 에이전트 표시 이름
  const AGENT_DISPLAY_NAMES = {
    'employee_agent': '직원 실적 분석',
    'client_agent': '고객/거래처 분석',
    'search_agent': '정보 검색',
    'create_document_agent': '문서 생성'
  };

  // 4개 에이전트 정보 - 기존 프로젝트 설정 유지 (/api/chat 사용)
  const agents = {
    router: {
      name: 'Router Agent',
      endpoint: '/api/chat',  // 기존 프로젝트 API 경로 유지
      description: '쿼리를 분석하고 적절한 에이전트로 자동 라우팅',
      color: '#3b82f6'
    },
    employee: {
      name: 'Employee Agent',
      endpoint: '/api/select-agent',
      description: '직원 실적 분석 및 평가',
      color: '#10b981',
      agentType: 'employee_agent'
    },
    client: {
      name: 'Client Agent',
      endpoint: '/api/select-agent',
      description: '고객/거래처 분석 및 영업 전략',
      color: '#f59e0b',
      agentType: 'client_agent'
    },
    search: {
      name: 'Search Agent',
      endpoint: '/api/select-agent',
      description: '정보 검색',
      color: '#06b6d4',
      agentType: 'search_agent'
    },
    docs: {
      name: 'Docs Agent',
      endpoint: '/api/select-agent',
      description: '문서 분류 및 생성',
      color: '#8b5cf6',
      agentType: 'create_document_agent'
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 로컬 스토리지와 백엔드 동시 사용 (하이브리드 방식)
  const loadChatHistoryFromLocal = () => {
    try {
      console.log('🔄 로컬 스토리지에서 채팅 내역 불러오는 중...');
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        const localHistory = JSON.parse(savedHistory);
        setChatHistory(localHistory);
        console.log(`✅ ${localHistory.length}개 채팅 내역 불러옴`);
        return localHistory;
      }
      return [];
    } catch (error) {
      console.error('❌ 채팅 내역 불러오기 실패:', error);
      return [];
    }
  };

  // 백엔드에서 채팅 내역 불러오기 (기존 코드 유지)
  const loadChatHistoryFromBackend = async () => {
    try {
      console.log('🔄 백엔드에서 모든 세션 불러오는 중...');
      const response = await fetch('/api/all-sessions');
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.sessions) {
          console.log(`✅ 백엔드에서 ${data.count}개 세션 불러옴`);
          
          // 세션 데이터를 채팅 히스토리 형식으로 변환
          const chatHistoryFromDB = data.sessions.map(session => ({
            id: session.id,
            sessionId: session.session_id,
            title: session.title || `채팅 ${session.created_at}`,
            messages: session.messages || [],
            createdAt: session.created_at,
            messageCount: session.message_count
          }));
          
          return chatHistoryFromDB;
        }
      }
      return [];
    } catch (error) {
      console.error('❌ 백엔드 세션 불러오기 실패:', error);
      return [];
    }
  };

  // 초기 안내 메시지
  useEffect(() => {
    const initializeChat = async () => {
      // 로컬 스토리지에서 먼저 불러오고, 없으면 백엔드 시도
      let history = loadChatHistoryFromLocal();
      
      if (history.length === 0) {
        // 로컬에 없으면 백엔드에서 시도
        history = await loadChatHistoryFromBackend();
        if (history.length > 0) {
          setChatHistory(history);
          localStorage.setItem('chatHistory', JSON.stringify(history));
        }
      }
      
      // 세션이 있으면 첫 번째 세션 선택, 없으면 새 채팅 시작
      if (history.length > 0) {
        console.log(`📚 ${history.length}개의 세션 발견`);
        // 가장 최근 세션 선택
        const mostRecentSession = history[0];
        if (mostRecentSession.sessionId) {
          await selectChat(mostRecentSession.id);
        } else {
          // 메시지를 비워두어 예시 프롬프트가 표시되도록 함
          setMessages([]);
        }
      } else {
        console.log('📝 세션이 없음, 새 채팅 시작');
        // 메시지를 비워두어 예시 프롬프트가 표시되도록 함
        setMessages([]);
        startNewChat();
      }
    };
    
    initializeChat();
  }, []);

  // 새로운 채팅 시작
  const startNewChat = () => {
    const chatId = Date.now().toString();
    const newSessionId = generateSessionId();
    
    // 메시지를 비워서 예시 프롬프트가 표시되도록 함
    setMessages([]);
    setCurrentChatId(chatId);
    setSessionId(newSessionId);
    
    // 새 채팅을 히스토리에 추가
    const newChat = {
      id: chatId,
      sessionId: newSessionId,
      title: `채팅 ${new Date().toLocaleString()}`,
      messages: [],
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
        // 백엔드에서 메시지 불러오기 시도
        try {
          if (selectedChat.sessionId) {
            const response = await fetch(`/api/session/${selectedChat.sessionId}/messages`);
            if (response.ok) {
              const data = await response.json();
              if (data.success && data.messages) {
                setMessages(data.messages);
                return;
              }
            }
          }
          
          // 백엔드 실패시 로컬 데이터 사용
          setMessages(selectedChat.messages || []);
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
            sessionId: sessionId || chat.sessionId, // sessionId 유지
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
    
    // Docs Agent 입력 대기 상태 초기화
    setIsWaitingForDocsInput(false);
    setDocsInputType(null);

    try {
      let response;
      let requestBody;
      
      // Check if we have an active thread_id (indicates we're in resume mode)
      const activeThreadId = sessionStorage.getItem(`thread_${sessionId}`);
      
      if (activeThreadId) {
        // Resume API call for interactive responses
        const interruptType = sessionStorage.getItem(`interrupt_type_${sessionId}`);
        let replyType = 'user_reply';
        if (interruptType === 'verification') {
          replyType = 'verification_reply';
        } else if (interruptType === 'manual_doc_selection') {
          replyType = 'verification_reply';
        }
        
        requestBody = {
          user_reply: currentQuery,
          reply_type: replyType
        };
        
        // JWT 토큰 가져오기
        const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
        
        // 기존 프로젝트 URL 사용 (8010 포트)
        response = await fetch(`/api/v1/resume/${sessionId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify(requestBody)
        });
      } else {
        // Normal chat API call - 기존 프로젝트 설정 사용
        requestBody = { 
          message: currentQuery,
          session_id: sessionId
        };

        // JWT 토큰 가져오기
        const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
        
        response = await fetch('/api/v1/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify(requestBody)
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      let botResponseContent = '';
      let responseAgent = 'Router Agent';
      
      // Handle interrupt responses first
      if (data.requires_interrupt && data.data?.thread_id) {
        // Store thread_id and interrupt_type for subsequent resume calls
        sessionStorage.setItem(`thread_${sessionId}`, data.data.thread_id);
        sessionStorage.setItem(`interrupt_type_${sessionId}`, data.data.interrupt_type || 'verification');
        
        // Check if this is a manual document type selection
        if (data.data.prompt_type === 'manual_doc_selection' && data.data.options) {
          sessionStorage.setItem(`interrupt_type_${sessionId}`, 'manual_doc_selection');
          
          const interactiveMessage = {
            type: 'interactive',
            content: data.response || '문서 타입을 선택해주세요.',
            timestamp: new Date().toLocaleTimeString(),
            agent: data.target_agent || 'Docs Agent',
            waiting_for_input: true,
            input_type: 'manual_selection',
            options: data.data.options.map(opt => opt.label),
            thread_id: data.data.thread_id
          };
          
          const messagesWithInteractive = [...newMessages, interactiveMessage];
          setMessages(messagesWithInteractive);
          saveMessageToHistory(messagesWithInteractive);
          
          setIsWaitingForDocsInput(true);
          setDocsInputType('manual_selection');
          setIsLoading(false);
          return;
        }
        
        // Regular interrupt handling
        let messageContent = data.response || '추가 정보가 필요합니다.';
        if (data.data.interrupt_type === 'data_input') {
          if (data.data.state_info?.template_content) {
            messageContent = data.data.state_info.template_content;
          } else if (data.data.template_content) {
            messageContent = data.data.template_content;
          }
        }
        
        const interactiveMessage = {
          type: 'interactive',
          content: messageContent,
          timestamp: new Date().toLocaleTimeString(),
          agent: data.target_agent || 'Docs Agent',
          waiting_for_input: true,
          input_type: data.data.interrupt_type || 'verification',
          thread_id: data.data.thread_id
        };
        
        const messagesWithInteractive = [...newMessages, interactiveMessage];
        setMessages(messagesWithInteractive);
        saveMessageToHistory(messagesWithInteractive);
        
        setIsWaitingForDocsInput(true);
        setDocsInputType(data.data.interrupt_type || 'verification');
        setIsLoading(false);
        return;
      }
      
      if (data.success) {
        // Router 에이전트에서 사용자 선택이 필요한 경우
        if (data.needs_user_selection) {
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
        
        // Clear thread_id and interrupt_type if task is completed
        if (!data.requires_interrupt && sessionStorage.getItem(`thread_${sessionId}`)) {
          sessionStorage.removeItem(`thread_${sessionId}`);
          sessionStorage.removeItem(`interrupt_type_${sessionId}`);
        }
        
        // Docs Agent의 대화형 응답 처리
        if (data.agent === 'docs_agent' && data.waiting_for_input) {
          const interactiveMessage = {
            type: 'interactive',
            content: data.response,
            timestamp: new Date().toLocaleTimeString(),
            agent: 'Docs Agent',
            waiting_for_input: true,
            input_type: data.input_type,
            options: data.options || null,
            step: data.step
          };
          
          const messagesWithInteractive = [...newMessages, interactiveMessage];
          setMessages(messagesWithInteractive);
          saveMessageToHistory(messagesWithInteractive);
          
          setIsWaitingForDocsInput(true);
          setDocsInputType(data.input_type);
          setIsLoading(false);
          return;
        }
        
        // 응답에서 실제 사용된 에이전트 정보 추출
        const usedAgent = data.agent || data.classification_result?.split(': ')[1];
        if (usedAgent) {
          responseAgent = AGENT_DISPLAY_NAMES[usedAgent] || usedAgent;
        }
        
        // 기본 응답 내용
        botResponseContent = data.response || data.message || '처리가 완료되었습니다.';
        
        // 종료 메시지 감지 - 위반사항은 제외
        const isTerminationMessage = (
          // 위반사항이 아닐 때만 종료로 처리
          !data.data?.violation &&
          data.data?.error_type !== 'policy_violation' &&
          (
            botResponseContent.includes('종료되었습니다') || 
            botResponseContent.includes('새로운 작업을 시작해주세요') ||
            botResponseContent.includes('문서 작성이 종료') ||
            data.data?.end_process === true ||
            data.data?.terminated === true ||
            data.data?.error_type === 'user_terminated' ||
            // 백엔드 응답에서 종료 상황 감지
            (data.response && data.response.includes('👋')) ||
            (data.message && data.message.includes('👋'))
          )
        );

        if (isTerminationMessage) {
          // 세션 관련 모든 스토리지 강제 정리
          sessionStorage.removeItem(`thread_${sessionId}`);
          sessionStorage.removeItem(`interrupt_type_${sessionId}`);
          
          // 새로운 세션 ID 생성하여 완전히 새로운 대화로 시작
          const newSessionId = generateSessionId();
          setSessionId(newSessionId);
          
          // 종료 메시지를 더 명확하게 표시
          if (!botResponseContent.includes('👋')) {
            botResponseContent = '👋 문서 작성이 종료되었습니다. 새로운 작업을 시작해주세요.';
          }
        }
        
        // 라우팅 정보가 있으면 추가
        if (data.classification_result) {
          botResponseContent += `\n\n[${data.classification_result}]`;
        }
        
        // Docs Agent 완료 메시지 처리
        if (data.agent === 'docs_agent' && data.step === 'completed') {
          if (data.document) {
            botResponseContent += '\n\n📄 생성된 문서:\n' + data.document;
          }
          if (data.file_path) {
            botResponseContent += `\n\n💾 파일 위치: ${data.file_path}`;
          }
        }
        
        // Handle completed data from resume endpoint
        if (data.data?.violation_blocked) {
          botResponseContent += '\n\n⚠️ 분석은 완료되었지만 규정 위반으로 파일 생성이 차단되었습니다.';
          
          if (data.data?.violation_details && data.data.violation_details.length > 0) {
            botResponseContent += '\n\n📋 위반 내용:';
            data.data.violation_details.forEach((violation, index) => {
              botResponseContent += `\n${index + 1}. ${violation}`;
            });
          }
          
          if (data.data?.filled_data) {
            botResponseContent += '\n\n📝 분석된 데이터:';
            Object.entries(data.data.filled_data).forEach(([key, value]) => {
              if (value) {
                botResponseContent += `\n- ${key}: ${value}`;
              }
            });
          }
        } else if (data.data?.final_doc) {
          botResponseContent += '\n\n📄 생성된 문서가 저장되었습니다.';
          if (data.data.final_doc) {
            botResponseContent += `\n💾 파일 위치: ${data.data.final_doc}`;
          }
        }
      } else {
        // 오류 메시지 처리
        const errorMsg = data.response || data.error || data.message || '알 수 없는 오류가 발생했습니다.';
        
        // 규정 위반을 먼저 체크
        if (data.data?.error_type === 'policy_violation' || data.data?.violation) {
          // response에 위반 메시지가 포함되어 있으면 그대로 사용
          if (data.response && data.response.includes('🚫')) {
            botResponseContent = data.response;
          } else {
            botResponseContent = `❌ ${errorMsg}`;
            
            if (data.data?.violation_details && data.data.violation_details.length > 0) {
              botResponseContent += '\n\n📋 위반 내용:';
              data.data.violation_details.forEach((violation, index) => {
                botResponseContent += `\n${index + 1}. ${violation}`;
              });
            } else if (data.data?.violation) {
              botResponseContent += `\n\n📋 위반 내용:\n${data.data.violation}`;
            }
            
            if (data.data?.filled_data) {
              botResponseContent += '\n\n📝 입력한 데이터:';
              Object.entries(data.data.filled_data).forEach(([key, value]) => {
                if (value) {
                  botResponseContent += `\n- ${key}: ${value}`;
                }
              });
            }
          }
          
          // 세션 관련 모든 스토리지 강제 정리
          sessionStorage.removeItem(`thread_${sessionId}`);
          sessionStorage.removeItem(`interrupt_type_${sessionId}`);
          
          // 새로운 세션 ID 생성
          const newSessionId = generateSessionId();
          setSessionId(newSessionId);
        }
        // 위반이 아닌 일반 종료의 경우
        else if (data.data?.error_type === 'user_terminated' || data.data?.terminated || data.data?.end_process) {
          botResponseContent = '👋 문서 작성이 종료되었습니다. 새로운 작업을 시작해주세요.';
          
          // 세션 관련 모든 스토리지 강제 정리
          sessionStorage.removeItem(`thread_${sessionId}`);
          sessionStorage.removeItem(`interrupt_type_${sessionId}`);
          
          // 새로운 세션 ID 생성
          const newSessionId = generateSessionId();
          setSessionId(newSessionId);
        } else {
          botResponseContent = `❌ ${errorMsg}`;
        }
      }

      const botMessage = {
        type: 'bot',
        content: botResponseContent,
        timestamp: new Date().toLocaleTimeString(),
        agent: responseAgent
      };

      const finalMessages = [...newMessages, botMessage];
      setMessages(finalMessages);
      saveMessageToHistory(finalMessages);

      // 성공적으로 완료된 경우 thread_id 정리
      if (data.success && !data.requires_interrupt) {
        sessionStorage.removeItem(`thread_${sessionId}`);
        sessionStorage.removeItem(`interrupt_type_${sessionId}`);
      }

    } catch (error) {
      console.error('API 요청 오류:', error);
      const errorMessage = {
        type: 'bot',
        content: `❌ 연결 오류: ${error.message}\n\n백엔드 서버가 실행 중인지 확인해주세요.`,
        timestamp: new Date().toLocaleTimeString(),
        agent: 'System'
      };
      const finalMessages = [...newMessages, errorMessage];
      setMessages(finalMessages);
      saveMessageToHistory(finalMessages);
    } finally {
      setIsLoading(false);
      setIsWaitingForDocsInput(false);
      setDocsInputType(null);
    }
  };

  // 에이전트 선택 처리 함수
  const handleAgentSelection = async (query, selectedAgentKey) => {
    setIsLoading(true);

    try {
      // 초기 화면에서 선택하는 경우
      const endpoint = query === '' ? '/api/initial-agent-select' : '/api/select-agent';
      
      const response = await fetch(`${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: query,
          session_id: sessionId,
          selected_agent: selectedAgentKey
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        if (data.needs_new_question) {
          // 예시 질문을 보여주는 특별한 메시지 타입
          const guideMessage = {
            type: 'agent_guide',
            content: data.message,
            timestamp: new Date().toLocaleTimeString(),
            agent: 'System',
            selected_agent: data.selected_agent,
            example_questions: data.example_questions
          };
          
          const updatedMessages = [...messages, guideMessage];
          setMessages(updatedMessages);
          saveMessageToHistory(updatedMessages);
        } else {
          // 실제 에이전트 응답
          const botMessage = {
            type: 'bot',
            content: data.response || data.message,
            timestamp: new Date().toLocaleTimeString(),
            agent: data.agent
          };
          
          const updatedMessages = [...messages, botMessage];
          setMessages(updatedMessages);
          saveMessageToHistory(updatedMessages);
        }
      } else {
        const errorMessage = {
          type: 'bot',
          content: `❌ 에이전트 선택 처리 오류: ${data.error || data.message}`,
          timestamp: new Date().toLocaleTimeString(),
          agent: 'System'
        };
        
        const updatedMessages = [...messages, errorMessage];
        setMessages(updatedMessages);
        saveMessageToHistory(updatedMessages);
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

  // 에이전트 초기화
  const resetAgent = async () => {
    if (!sessionId) return;
    
    if (!window.confirm('현재 에이전트를 초기화하시겠습니까?\n다음 질문부터 새로운 에이전트가 선택됩니다.')) {
      return;
    }

    try {
      const response = await fetch('/api/reset-agent', {
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
                      {chat.messageCount && (
                        <span style={{fontSize: '12px', color: '#999', marginLeft: '5px'}}>
                          ({chat.messageCount}개 메시지)
                        </span>
                      )}
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

        {/* Main Content */}
        <div className="chat-container">
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
            {messages.length === 0 ? (
              <div className="example-prompts-container">
                <h2 className="welcome-title">무엇을 도와드릴까요?</h2>
                <p className="welcome-subtitle">아래 예시를 클릭하거나 직접 질문해 주세요</p>
                <div className="example-prompts-grid">
                  <div className="prompt-card" onClick={() => setInputValue("최수아 직원의 이번달 실적을 분석해줘")}>
                    <div className="prompt-icon">👥</div>
                    <div className="prompt-text">최수아 직원의 이번달 실적을 분석해줘</div>
                    <div className="prompt-category">직원 실적</div>
                  </div>
                  <div className="prompt-card" onClick={() => setInputValue("미라클신경과 거래처 매출 추이를 보여줘")}>
                    <div className="prompt-icon">🏢</div>
                    <div className="prompt-text">미라클신경과 거래처 매출 추이를 보여줘</div>
                    <div className="prompt-category">거래처 분석</div>
                  </div>
                  <div className="prompt-card" onClick={() => setInputValue("영업방문 보고서를 작성해줘")}>
                    <div className="prompt-icon">📄</div>
                    <div className="prompt-text">영업방문 보고서를 작성해줘</div>
                    <div className="prompt-category">문서 작성</div>
                  </div>
                  <div className="prompt-card" onClick={() => setInputValue("영업 규정 및 가이드라인을 찾아줘")}>
                    <div className="prompt-icon">🔍</div>
                    <div className="prompt-text">영업 규정 및 가이드라인을 찾아줘</div>
                    <div className="prompt-category">정보 검색</div>
                  </div>
                  <div className="prompt-card" onClick={() => setInputValue("서부팀 전체 성과를 분석해줘")}>
                    <div className="prompt-icon">📊</div>
                    <div className="prompt-text">서부팀 전체 성과를 분석해줘</div>
                    <div className="prompt-category">팀 성과</div>
                  </div>
                  <div className="prompt-card" onClick={() => setInputValue("제품설명회 신청서를 만들어줘")}>
                    <div className="prompt-icon">📋</div>
                    <div className="prompt-text">제품설명회 신청서를 만들어줘</div>
                    <div className="prompt-category">문서 작성</div>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
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
                  {message.type === 'agent_guide' ? (
                    <div>
                      <div style={{marginBottom: '15px'}}>
                        {message.content.split('\n').map((line, i) => (
                          <div key={i} style={{marginBottom: '5px'}}>{line}</div>
                        ))}
                      </div>
                      {message.example_questions && (
                        <div style={{marginTop: '20px'}}>
                          <div style={{fontWeight: 'bold', marginBottom: '10px', color: '#4a5568'}}>
                            💡 예시 질문 클릭하여 사용:
                          </div>
                          <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
                            {message.example_questions.map((example, idx) => (
                              <button
                                key={idx}
                                onClick={() => {
                                  setInputValue(example);
                                  const frontendKey = agentKeyMapping[message.selected_agent] || message.selected_agent;
                                  setSelectedAgent(frontendKey);
                                }}
                                style={{
                                  textAlign: 'left',
                                  padding: '10px 15px',
                                  border: '1px solid #e2e8f0',
                                  borderRadius: '8px',
                                  backgroundColor: '#f7fafc',
                                  cursor: 'pointer',
                                  transition: 'all 0.2s',
                                  fontSize: '14px'
                                }}
                                onMouseEnter={(e) => {
                                  e.target.style.backgroundColor = '#edf2f7';
                                  e.target.style.borderColor = '#cbd5e0';
                                }}
                                onMouseLeave={(e) => {
                                  e.target.style.backgroundColor = '#f7fafc';
                                  e.target.style.borderColor = '#e2e8f0';
                                }}
                              >
                                {example}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : message.type === 'agent_selection' ? (
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
                  ) : message.type === 'interactive' ? (
                    <div>
                      <div style={{marginBottom: '15px'}}>
                        {message.content.split('\n').map((line, i) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                      {message.waiting_for_input && (
                        <div style={{marginTop: '15px'}}>
                          {message.input_type === 'verification' && (
                            <div className="verification-buttons" style={{display: 'flex', gap: '10px'}}>
                              <button
                                onClick={() => {
                                  setInputValue('예');
                                  sendMessage();
                                }}
                                style={{
                                  padding: '8px 20px',
                                  backgroundColor: '#4CAF50',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '5px',
                                  cursor: 'pointer'
                                }}
                                disabled={isLoading}
                              >
                                예
                              </button>
                              <button
                                onClick={() => {
                                  setInputValue('아니오');
                                  sendMessage();
                                }}
                                style={{
                                  padding: '8px 20px',
                                  backgroundColor: '#f44336',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '5px',
                                  cursor: 'pointer'
                                }}
                                disabled={isLoading}
                              >
                                아니오
                              </button>
                            </div>
                          )}
                          {message.input_type === 'manual_selection' && message.options && (
                            <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
                              {message.options.map((option, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => {
                                    setInputValue(option);
                                    sendMessage();
                                  }}
                                  style={{
                                    textAlign: 'left',
                                    padding: '10px 15px',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: '8px',
                                    backgroundColor: '#f7fafc',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                  }}
                                  onMouseEnter={(e) => {
                                    e.target.style.backgroundColor = '#edf2f7';
                                    e.target.style.borderColor = '#cbd5e0';
                                  }}
                                  onMouseLeave={(e) => {
                                    e.target.style.backgroundColor = '#f7fafc';
                                    e.target.style.borderColor = '#e2e8f0';
                                  }}
                                  disabled={isLoading}
                                >
                                  {idx + 1}. {option}
                                </button>
                              ))}
                            </div>
                          )}
                          {message.input_type === 'data_input' && (
                            <div style={{
                              marginTop: '10px',
                              padding: '15px',
                              backgroundColor: '#f0f4f8',
                              borderRadius: '8px',
                              fontSize: '14px'
                            }}>
                              <div style={{color: '#666', fontSize: '13px', fontStyle: 'italic'}}>
                                위 항목들에 맞춰 정보를 입력해주세요.
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <ReactMarkdown
                      children={message.content}
                      components={{
                        h1: ({children}) => <h1 style={{fontSize: '1.5rem', fontWeight: 'bold', marginTop: '1rem', marginBottom: '0.5rem'}}>{children}</h1>,
                        h2: ({children}) => <h2 style={{fontSize: '1.3rem', fontWeight: 'bold', marginTop: '1rem', marginBottom: '0.5rem'}}>{children}</h2>,
                        h3: ({children}) => <h3 style={{fontSize: '1.1rem', fontWeight: 'bold', marginTop: '0.8rem', marginBottom: '0.4rem'}}>{children}</h3>,
                        p: ({children}) => <p style={{marginBottom: '0.5rem', lineHeight: '1.6'}}>{children}</p>,
                        ul: ({children}) => <ul style={{marginLeft: '1.5rem', marginBottom: '0.5rem'}}>{children}</ul>,
                        ol: ({children}) => <ol style={{marginLeft: '1.5rem', marginBottom: '0.5rem'}}>{children}</ol>,
                        li: ({children}) => <li style={{marginBottom: '0.25rem'}}>{children}</li>,
                        strong: ({children}) => <strong style={{fontWeight: 'bold'}}>{children}</strong>,
                        em: ({children}) => <em style={{fontStyle: 'italic'}}>{children}</em>,
                        blockquote: ({children}) => <blockquote style={{borderLeft: '3px solid #ddd', paddingLeft: '1rem', marginLeft: '0', color: '#666'}}>{children}</blockquote>,
                        code: ({inline, children}) => inline ? 
                          <code style={{backgroundColor: '#f4f4f4', padding: '2px 4px', borderRadius: '3px', fontSize: '0.9em'}}>{children}</code> :
                          <pre style={{backgroundColor: '#f4f4f4', padding: '0.5rem', borderRadius: '5px', overflowX: 'auto'}}><code>{children}</code></pre>,
                        table: ({children}) => <table style={{borderCollapse: 'collapse', width: '100%', marginBottom: '0.5rem'}}>{children}</table>,
                        th: ({children}) => <th style={{border: '1px solid #ddd', padding: '8px', backgroundColor: '#f4f4f4', fontWeight: 'bold'}}>{children}</th>,
                        td: ({children}) => <td style={{border: '1px solid #ddd', padding: '8px'}}>{children}</td>
                      }}
                    />
                  )}
                </div>
              </div>
            )))}
            
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
              <span style={{ color: agents.router.color }}>
                ● {agents.router.name}
              </span>
              <span className="agent-description">
                질문에 따라 자동으로 적절한 에이전트가 선택됩니다
              </span>
            </div>
            <div className="input-area">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isWaitingForDocsInput ? 
                  (docsInputType === 'verification' ? "예/아니오로 답변해주세요" :
                   docsInputType === 'manual_selection' ? "번호를 입력해주세요 (1, 2, 3)" :
                   docsInputType === 'data_input' ? "필요한 정보를 입력해주세요" :
                   "응답을 입력해주세요") :
                  "인사정보/거래처분석/실적분석/문서분류 중에 질문해주세요."}
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

export default ChatBot;