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
  const [selectedAgent, setSelectedAgent] = useState('router');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [sessionId, setSessionId] = useState(() => 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
  const [currentSessionAgent, setCurrentSessionAgent] = useState(null);
  const [isWaitingForDocsInput, setIsWaitingForDocsInput] = useState(false);
  const [docsInputType, setDocsInputType] = useState(null);
  const messagesEndRef = useRef(null);
  const DEBUG_MODE = true;

  // 디버깅 로그 함수
  const debugLog = (message, data = null) => {
    if (DEBUG_MODE) {
      console.log(`[DEBUG] ${message}`, data);
    }
  };

  // session_id 생성 함수
  const generateSessionId = () => {
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

  // 4개 에이전트 정보
  const agents = {
    router: {
      name: 'Router Agent',
      endpoint: '/api/chat',
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

  // 스크롤을 맨 아래로
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 백엔드에서 채팅 내역 불러오기
  const loadChatHistoryFromBackend = async () => {
    try {
      console.log('🔄 백엔드에서 모든 세션 불러오는 중...');
      const response = await fetch('http://localhost:8000/api/all-sessions');
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.sessions) {
          console.log(`✅ 백엔드에서 ${data.count}개 세션 불러옴`);
          
          // 세션 데이터를 채팅 히스토리 형식으로 변환
          const chatHistoryFromDB = data.sessions.map(session => ({
            id: session.id,
            sessionId: session.sessionId,
            title: session.title,
            messages: [], // 메시지는 선택할 때 로드
            createdAt: session.createdAt,
            messageCount: session.messageCount
          }));
          
          // localStorage의 기존 데이터와 병합 (중복 제거)
          const savedHistory = localStorage.getItem('chatHistory');
          let localHistory = [];
          if (savedHistory) {
            localHistory = JSON.parse(savedHistory);
          }
          
          // sessionId를 기준으로 중복 제거
          const mergedHistory = [...chatHistoryFromDB];
          localHistory.forEach(localChat => {
            if (!mergedHistory.find(dbChat => dbChat.sessionId === localChat.sessionId)) {
              mergedHistory.push(localChat);
            }
          });
          
          setChatHistory(mergedHistory);
          localStorage.setItem('chatHistory', JSON.stringify(mergedHistory));
          
          return mergedHistory;
        }
      }
      
      console.log('⚠️ 백엔드에서 세션 목록 없음, localStorage 사용');
      // 백엔드에 데이터가 없으면 localStorage 사용
      const savedHistory = localStorage.getItem('chatHistory');
      if (savedHistory) {
        const localHistory = JSON.parse(savedHistory);
        setChatHistory(localHistory);
        return localHistory;
      }
      
      return [];
    } catch (error) {
      console.error('❌ 세션 목록 불러오기 실패:', error);
      
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
      // 시스템 안내 메시지
      const systemMessage = {
        type: 'system',
        content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
        timestamp: new Date().toLocaleTimeString()
      };
      
      // 에이전트 선택 메시지 (H2H와 동일한 형태)
      const agentSelectionMessage = {
        type: 'agent_selection',
        content: `저희 시스템은 다음 기능을 제공합니다:
- 직원 실적/평가 조회
- 고객/거래처(병원,약국) 정보 관리
- 영업 데이터 검색
- 보고서/문서 자동 생성

원하시는 기능을 선택하시거나, 바로 질문을 입력하셔도 됩니다.`,
        timestamp: new Date().toLocaleTimeString(),
        agent: 'System',
        query: '',  // 초기 선택이므로 query 없음
        available_agents: ['employee_agent', 'client_agent', 'search_agent', 'create_document_agent'],
        agent_descriptions: {
          "employee_agent": "사내 직원에 대한 정보 제공을 담당합니다. 예: 개인 실적 조회, 인사 이력, 직책, 소속 부서, 조직도 확인, 성과 평가 등 직원 관련 질의 응답을 처리합니다.",
          "client_agent": "고객 및 거래처에 대한 정보를 제공합니다. 반드시 병원, 제약영업과 관련이 있는 질문에만 답변합니다.예: 특정 고객의 매출 추이, 거래 이력, 등급 분류, 잠재 고객 분석, 영업 성과 분석 등 외부 고객 관련 질문에 대응합니다.",
          "search_agent": "내부 데이터베이스에서 정보 검색을 수행합니다. 예: 문서 검색, 사내 규정, 업무 매뉴얼, 제품 정보, 교육 자료 등 특정 정보를 정제된 DB 또는 벡터DB 기반으로 검색합니다.",
          "create_document_agent": "문서 자동 생성 및 규정 검토를 담당합니다. 예: 보고서 초안 자동 생성, 전표/계획서 생성, 컴플라이언스 위반 여부 판단, 서식 분석 및 문서 오류 검토 등의 기능을 수행합니다."
        },
        agent_display_names: {
          "employee_agent": "직원 실적 분석",
          "client_agent": "고객/거래처 분석",
          "search_agent": "정보 검색",
          "create_document_agent": "문서 생성"
        }
      };
      
      // 백엔드에서 모든 세션 목록 불러오기
      const history = await loadChatHistoryFromBackend();
      
      // 세션이 있으면 첫 번째 세션 선택, 없으면 새 채팅 시작
      if (history.length > 0) {
        console.log(`📚 ${history.length}개의 세션 발견`);
        // 가장 최근 세션 선택
        const mostRecentSession = history[0];
        if (mostRecentSession.sessionId) {
          await selectChat(mostRecentSession.id);
        } else {
          // 기본 메시지 표시하고 새 채팅 시작
          setMessages([systemMessage, agentSelectionMessage]);
          startNewChat();
        }
      } else {
        console.log('📝 세션이 없음, 새 채팅 시작');
        // 기본 메시지 표시
        setMessages([systemMessage, agentSelectionMessage]);
        startNewChat();
      }
    };
    
    initializeChat();
  }, []);

  // 새로운 채팅 시작
  const startNewChat = () => {
    const chatId = Date.now().toString();
    const newSessionId = generateSessionId();
    
    // 시스템 메시지
    const systemMessage = {
      type: 'system',
      content: '안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?',
      timestamp: new Date().toLocaleTimeString()
    };
    
    // 에이전트 선택 메시지
    const agentSelectionMessage = {
      type: 'agent_selection',
      content: `저희 시스템은 다음 기능을 제공합니다:
- 직원 실적/평가 조회
- 고객/거래처(병원,약국) 정보 관리
- 영업 데이터 검색
- 보고서/문서 자동 생성

원하시는 기능을 선택하시거나, 바로 질문을 입력하셔도 됩니다.`,
      timestamp: new Date().toLocaleTimeString(),
      agent: 'System',
      query: '',
      available_agents: ['employee_agent', 'client_agent', 'search_agent', 'create_document_agent'],
      agent_descriptions: {
        "employee_agent": "사내 직원에 대한 정보 제공을 담당합니다. 예: 개인 실적 조회, 인사 이력, 직책, 소속 부서, 조직도 확인, 성과 평가 등 직원 관련 질의 응답을 처리합니다.",
        "client_agent": "고객 및 거래처에 대한 정보를 제공합니다. 반드시 병원, 제약영업과 관련이 있는 질문에만 답변합니다.예: 특정 고객의 매출 추이, 거래 이력, 등급 분류, 잠재 고객 분석, 영업 성과 분석 등 외부 고객 관련 질문에 대응합니다.",
        "search_agent": "내부 데이터베이스에서 정보 검색을 수행합니다. 예: 문서 검색, 사내 규정, 업무 매뉴얼, 제품 정보, 교육 자료 등 특정 정보를 정제된 DB 또는 벡터DB 기반으로 검색합니다.",
        "create_document_agent": "문서 자동 생성 및 규정 검토를 담당합니다. 예: 보고서 초안 자동 생성, 전표/계획서 생성, 컴플라이언스 위반 여부 판단, 서식 분석 및 문서 오류 검토 등의 기능을 수행합니다."
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
        // 백엔드에서 메시지 불러오기 - DB에서 직접 조회
        try {
          // sessionId가 있는지 확인
          if (!selectedChat.sessionId) {
            console.error('세션 ID가 없습니다:', selectedChat);
            setMessages(selectedChat.messages || []);
            return;
          }
          
          console.log(`🔄 세션 ${selectedChat.sessionId}의 메시지 불러오는 중...`);
          const response = await fetch(`http://localhost:8000/api/chat-history/${selectedChat.sessionId}`);
          
          if (response.ok) {
            const data = await response.json();
            if (data.success && data.messages && data.messages.length > 0) {
              console.log(`✅ ${data.count}개 메시지 불러옴`);
              
              // DB에서 가져온 메시지 형식을 프론트엔드 형식으로 변환
              const formattedMessages = data.messages.map(msg => ({
                type: msg.role === 'user' ? 'user' : msg.role === 'assistant' ? 'bot' : 'system',
                content: msg.content,
                timestamp: msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString(),
                agent: msg.metadata?.agent || 'System'
              }));
              
              setMessages(formattedMessages);
              
              // 채팅 히스토리 업데이트
              const updatedHistory = chatHistory.map(chat => 
                chat.id === chatId 
                  ? { ...chat, messages: formattedMessages }
                  : chat
              );
              setChatHistory(updatedHistory);
              localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
            } else {
              console.log('해당 세션에 메시지가 없습니다.');
              setMessages(selectedChat.messages || []);
            }
          } else {
            console.error('메시지 불러오기 실패:', response.status);
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

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);
    const currentQuery = inputMessage;
    setInputMessage('');
    
    // Docs Agent 입력 대기 상태 초기화
    setIsWaitingForDocsInput(false);
    setDocsInputType(null);

    try {
      // 항상 Router를 통해 전송하여 동적 라우팅 활성화
      const requestBody = { 
        session_id: sessionId,
        query: currentQuery 
      };

      const response = await fetch('http://localhost:8000/api/chat', {
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
      let responseAgent = 'Router Agent';
      
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
          
          // 입력 대기 상태로 설정
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
      } else {
        botResponseContent = `❌ 오류 발생: ${data.error || data.message}`;
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
      {/* 헤더 */}
      <div className="chat-header">
        <div className="header-left">
          <h1>NaruTalk</h1>
        </div>
        <div className="header-center">
          <div className="logo">
            <span className="logo-icon">🤖</span>
            <span className="logo-text">AI Assistant</span>
          </div>
        </div>
        <div className="header-right">
          <div className="header-nav">
            <button onClick={() => navigate('/')} className="nav-link">홈</button>
            <button onClick={() => navigate('/employee-performance')} className="nav-link">직원 실적</button>
            <button onClick={() => navigate('/admin')} className="nav-link">관리자</button>
          </div>
        </div>
      </div>

      {/* 메인 채팅 영역 */}
      <div className="chat-main">
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
                onClick={clearChat}
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
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.sender}-message ${message.isStreaming ? 'streaming' : ''}`}>
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
                                setInputMessage(example);
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
                    {message.input_type === 'yes_no' && (
                      <div style={{marginTop: '15px'}}>
                        <div style={{fontWeight: 'bold', marginBottom: '10px', color: '#4a5568'}}>
                          답변을 선택해주세요:
                        </div>
                        <div style={{display: 'flex', gap: '10px'}}>
                          <button
                            onClick={() => {
                              setInputMessage('예');
                              sendMessage();
                            }}
                            style={{
                              padding: '8px 16px',
                              border: '1px solid #e2e8f0',
                              borderRadius: '6px',
                              backgroundColor: '#f7fafc',
                              cursor: 'pointer',
                              transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.backgroundColor = '#edf2f7';
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.backgroundColor = '#f7fafc';
                            }}
                            disabled={isLoading}
                          >
                            예
                          </button>
                          <button
                            onClick={() => {
                              setInputMessage('아니오');
                              sendMessage();
                            }}
                            style={{
                              padding: '8px 16px',
                              border: '1px solid #e2e8f0',
                              borderRadius: '6px',
                              backgroundColor: '#f7fafc',
                              cursor: 'pointer',
                              transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.backgroundColor = '#edf2f7';
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.backgroundColor = '#f7fafc';
                            }}
                            disabled={isLoading}
                          >
                            아니오
                          </button>
                        </div>
                      </div>
                    )}
                    {message.input_type === 'multiple_choice' && message.options && (
                      <div style={{marginTop: '15px'}}>
                        <div style={{fontWeight: 'bold', marginBottom: '10px', color: '#4a5568'}}>
                          옵션을 선택해주세요:
                        </div>
                        <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
                          {message.options.map((option, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                setInputMessage((idx + 1).toString());
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
                              {option}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {message.input_type === 'data_input' && (
                      <div style={{
                        marginTop: '10px',
                        padding: '10px',
                        backgroundColor: '#f0f4f8',
                        borderRadius: '8px',
                        fontSize: '14px'
                      }}>
                        <div style={{color: '#555', marginBottom: '5px'}}>
                          📝 입력창에 필요한 정보를 입력해주세요
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  message.content.split('\n').map((line, i) => (
                    <div key={i}>{line}</div>
                  ))
                )}
              </div>
              {message.agentType && (
                <div className="agent-badge">
                  {AGENT_DISPLAY_NAMES[message.agentType] || message.agentType}
                </div>
              )}
            </div>
          ))}
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
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
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
              disabled={isLoading || !inputMessage.trim()}
              className="send-button"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatScreen; 