import React, { useState, useEffect, useRef } from 'react';
import './Docs.css';

const Docs = () => {
  const [selectedDocument, setSelectedDocument] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [requiresInterrupt, setRequiresInterrupt] = useState(false);
  const [interruptData, setInterruptData] = useState(null);
  const [documentOptions, setDocumentOptions] = useState([]);
  const [existingDocuments, setExistingDocuments] = useState([]);
  const [renderKey, setRenderKey] = useState(0); // 강제 리렌더링을 위한 키
  const chatContainerRef = useRef(null); // 채팅 컨테이너 ref
  const messagesEndRef = useRef(null); // 메시지 끝 부분 ref
  const [currentDocument, setCurrentDocument] = useState(null); // 현재 생성 중인 문서
  const [conversationHistory, setConversationHistory] = useState([]); // 대화 기록 저장
  const [activeConversationId, setActiveConversationId] = useState(null); // 현재 활성 대화 ID
  
  // localStorage에서 대화 기록 불러오기
  useEffect(() => {
    const savedHistory = localStorage.getItem('docsConversationHistory');
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setConversationHistory(parsed);
        setExistingDocuments(parsed.map(conv => ({
          id: conv.id,
          name: conv.title,
          created_at: conv.created_at,
          messages: conv.messages,
          document: conv.document,
          sessionId: conv.sessionId
        })));
      } catch (error) {
        console.error('대화 기록 불러오기 실패:', error);
      }
    }
  }, []);
  
  // messages 상태 변화 추적 및 자동 스크롤
  useEffect(() => {
    console.log('✨ messages 상태 변경됨!');
    console.log('✨ 현재 메시지 개수:', messages.length);
    console.log('✨ 메시지 내용:', messages);
    messages.forEach((msg, idx) => {
      console.log(`  ${idx}: [${msg.type}] ${msg.content?.substring(0, 50)}...`);
    });
    
    // 자동 스크롤 - 메시지가 추가될 때마다 맨 아래로
    scrollToBottom();
    
    // 현재 대화 저장 (메시지가 2개 이상일 때)
    if (messages.length >= 2 && activeConversationId) {
      updateConversationHistory(activeConversationId);
    }
  }, [messages]);
  
  // 스크롤을 맨 아래로 이동하는 함수
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  // 문서 내용 포맷팅 함수 (보고서 형식)
  const formatDocumentContent = (data, docType) => {
    if (!data) return '';
    
    // 문자열인 경우 (생성 중 메시지 또는 원본 문서 내용)
    if (typeof data === 'string') {
      // 문서 내용을 그대로 표시
      return (
        <div className="generated-document">
          <div className="document-content-text">
            {data}
          </div>
        </div>
      );
    }
    
    // 객체인 경우 (완성된 문서)
    const fieldNames = {
      '방문제목': '방문 제목',
      '방문날짜': '방문 날짜',
      'Client': '고객사명',
      '방문site': '방문 장소',
      '담당자성명': '고객사 담당자',
      '담당자소속': '담당자 소속',
      '담당자연락처': '담당자 연락처',
      '영업제공자성명': '영업 담당자',
      '영업제공자연락처': '영업 담당자 연락처',
      '방문자성명': '방문자',
      '방문자소속': '방문자 소속',
      '고객사개요': '고객사 개요',
      '프로젝트개요': '프로젝트 개요',
      '방문및협의내용': '방문 및 협의 내용',
      '향후계획및일정': '향후 계획 및 일정',
      '협조사항및공유사항': '협조사항 및 공유사항'
    };
    
    // 객체 데이터를 문서 형식으로 변환
    const documentTitle = docType || data['문서제목'] || '생성된 문서';
    
    // 문서 내용을 실제 문서처럼 포맷팅
    let documentContent = `${documentTitle}\n\n`;
    documentContent += '=' .repeat(50) + '\n\n';
    
    Object.entries(data).forEach(([key, value]) => {
      const displayName = fieldNames[key] || key;
      if (value && value !== '' && key !== '문서제목') {
        documentContent += `【${displayName}】\n`;
        documentContent += `${value}\n\n`;
      }
    });
    
    documentContent += '\n' + '=' .repeat(50) + '\n';
    documentContent += `작성일: ${new Date().toLocaleDateString('ko-KR')}\n`;
    
    return (
      <div className="generated-document">
        <pre className="document-content-text">
          {documentContent}
        </pre>
      </div>
    );
  };

  // API Base URL - 에이전트 서버로 요청 (8000 포트)
  const API_BASE_URL = 'http://localhost:8000';

  // 초기 문서 작성 요청
  const handleInitialRequest = async (message) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/docs/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        })
      });

      const data = await response.json();
      console.log('Docs API Response:', data);

      if (data.success) {
        // 문서 생성 완료
        setMessages(prev => [...prev, 
          { type: 'user', content: message },
          { type: 'ai', content: data.response, data: data.data }
        ]);
        
        // 최종 문서가 생성된 경우 (final_doc 또는 filled_data가 있는 경우)
        if (data.data?.final_doc || data.data?.filled_data) {
          const newDocument = {
            type: data.data.document_type || '생성된 문서',
            content: data.data.document_content,
            fields: data.data.filled_data
          };
          setCurrentDocument(newDocument);
          setSelectedDocument(data.data.document_type || '생성된 문서');
          
          // 대화와 문서를 함께 저장
          setTimeout(() => {
            const conversationId = Date.now();
            const newConversation = {
              id: conversationId,
              title: newDocument.type || '생성된 문서',
              messages: [
                { type: 'user', content: message },
                { type: 'ai', content: data.response, data: data.data }
              ],
              document: newDocument,
              sessionId: sessionId || null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            };
            
            const updatedHistory = [...conversationHistory, newConversation];
            setConversationHistory(updatedHistory);
            setExistingDocuments(prev => [...prev, {
              id: newConversation.id,
              name: newConversation.title,
              created_at: newConversation.created_at,
              messages: newConversation.messages,
              document: newConversation.document,
              sessionId: newConversation.sessionId
            }]);
            
            localStorage.setItem('docsConversationHistory', JSON.stringify(updatedHistory));
            setActiveConversationId(conversationId);
          }, 500);
        }
      } else if (data.requires_interrupt) {
        // 사용자 입력 필요
        setSessionId(data.session_id);
        setRequiresInterrupt(true);
        setInterruptData(data.data);
        
        setMessages(prev => [...prev, 
          { type: 'user', content: message },
          { type: 'ai', content: data.response, interrupt: true, data: data.data }
        ]);
        
        // 문서 선택 옵션이 있는 경우
        if (data.data?.options) {
          setDocumentOptions(data.data.options);
        }
      } else {
        // 오류 발생 또는 위반 메시지
        const displayMessage = data.response || data.error || '오류가 발생했습니다.';
        setMessages(prev => [...prev, 
          { type: 'user', content: message },
          { type: 'ai', content: displayMessage, error: !data.response }
        ]);
      }
    } catch (error) {
      console.error('API 호출 오류:', error);
      setMessages(prev => [...prev, 
        { type: 'user', content: message },
        { type: 'ai', content: '서버 연결에 실패했습니다. 다시 시도해주세요.', error: true }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // 인터럽트 처리 (세션 재개)
  const handleResumeSession = async (userReply, replyType = 'user_reply') => {
    console.log('=== handleResumeSession 시작 ===');
    console.log('sessionId:', sessionId);
    console.log('userReply:', userReply);
    console.log('replyType:', replyType);
    
    if (!sessionId) {
      console.error('세션 ID가 없습니다.');
      return;
    }

    // 사용자 메시지 즉시 표시
    setMessages(prev => [...prev, { type: 'user', content: userReply }]);
    setIsLoading(true);
    try {
      const requestBody = {
        user_reply: userReply,
        reply_type: replyType
      };
      console.log('Request Body:', requestBody);
      console.log('Request URL:', `${API_BASE_URL}/api/v1/docs/resume/${sessionId}`);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/docs/resume/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      console.log('Response Status:', response.status);
      const data = await response.json();
      console.log('Resume Response Data:', data);

      if (data.success) {
        console.log('처리 완료!');
        // 처리 완료
        setRequiresInterrupt(false);
        setInterruptData(null);
        
        // 대화 자동 저장 트리거
        if (!activeConversationId && messages.length > 0) {
          setTimeout(() => saveConversation(), 500);
        }
        
        // 사용자 메시지는 이미 추가했으므로 AI 응답만 추가
        setMessages(prev => [...prev, 
          { type: 'ai', content: data.response, data: data.data }
        ]);
        
        // 문서 경로 또는 filled_data가 있을 때 완성된 문서 표시
        if (data.data?.final_doc || data.data?.filled_data) {
          // 완성된 문서 표시
          const newDocument = {
            type: data.data.document_type || '생성된 문서',
            content: data.data.document_content,
            fields: data.data.filled_data
          };
          setCurrentDocument(newDocument);
          setSelectedDocument(data.data.document_type || '생성된 문서');
          
          // 세션 완료 처리 - 문서를 직접 전달
          if (data.data?.final_doc) {
            // 대화 저장
            if (!activeConversationId) {
              setTimeout(() => saveConversationWithDocument(newDocument), 500);
            } else {
              setTimeout(() => updateConversationHistoryWithDocument(activeConversationId, newDocument), 500);
            }
          }
        }
      } else if (data.requires_interrupt) {
        console.log('추가 인터럽트 발생!');
        console.log('data.response:', data.response);
        console.log('data.data:', data.data);
        
        // 추가 입력 필요
        setRequiresInterrupt(true);  // 인터럽트 상태 유지
        setSessionId(data.session_id || sessionId);  // 세션 ID 업데이트
        setInterruptData(data.data);
        
        // 메시지 추가 전 현재 메시지 배열 확인
        console.log('현재 메시지 개수:', messages.length);
        
        // 사용자 메시지는 이미 추가했으므로 AI 응답만 추가
        const aiMessage = { 
          type: 'ai', 
          content: data.response || '필수 입력 항목을 안내해드리겠습니다.', 
          interrupt: true, 
          data: data.data 
        };
        console.log('AI 메시지 추가:', aiMessage);
        console.log('AI 메시지 내용:', aiMessage.content);
        
        // 메시지 배열 업데이트
        setMessages(prev => {
          const newMessages = [...prev, aiMessage];
          console.log('업데이트된 메시지 배열 길이:', newMessages.length);
          console.log('마지막 메시지:', newMessages[newMessages.length - 1]);
          return newMessages;
        });
        
        // 문서 작성 중에는 중앙 화면에 아무것도 표시하지 않음
        // 최종 완성될 때만 표시
        
        // 강제 리렌더링
        setRenderKey(prev => prev + 1);
        
        if (data.data?.options) {
          setDocumentOptions(data.data.options);
        }
      } else {
        // 오류 또는 위반 메시지 (사용자 메시지는 이미 추가했으므로 AI 응답만 추가)
        const displayMessage = data.response || data.error || '오류가 발생했습니다.';
        setMessages(prev => [...prev, 
          { type: 'ai', content: displayMessage, error: !data.response }
        ]);
      }
    } catch (error) {
      console.error('Resume 오류:', error);
      // 사용자 메시지는 이미 추가했으므로 AI 응답만 추가
      setMessages(prev => [...prev, 
        { type: 'ai', content: '세션 재개에 실패했습니다.', error: true }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // 메시지 전송 처리
  const handleSendMessage = () => {
    if (inputMessage.trim() && !isLoading) {
      const message = inputMessage.trim();
      setInputMessage('');
      
      if (requiresInterrupt && sessionId) {
        // 인터럽트 상태에서는 세션 재개
        const replyType = interruptData?.interrupt_type === 'verification' ? 
          'verification_reply' : 'user_reply';
        handleResumeSession(message, replyType);
      } else {
        // 새로운 요청
        handleInitialRequest(message);
      }
    }
  };

  // 문서 타입 선택 처리
  const handleDocumentTypeSelect = (option) => {
    handleResumeSession(option.value, 'verification_reply');
  };

  // 대화 기록 업데이트
  const updateConversationHistory = (convId) => {
    const updatedHistory = conversationHistory.map(conv => {
      if (conv.id === convId) {
        return {
          ...conv,
          messages: messages,
          document: currentDocument,
          sessionId: sessionId,
          updated_at: new Date().toISOString()
        };
      }
      return conv;
    });
    
    setConversationHistory(updatedHistory);
    localStorage.setItem('docsConversationHistory', JSON.stringify(updatedHistory));
  };
  
  // 문서와 함께 대화 기록 업데이트
  const updateConversationHistoryWithDocument = (convId, document) => {
    const updatedHistory = conversationHistory.map(conv => {
      if (conv.id === convId) {
        return {
          ...conv,
          messages: messages,
          document: document,
          sessionId: sessionId,
          updated_at: new Date().toISOString()
        };
      }
      return conv;
    });
    
    setConversationHistory(updatedHistory);
    setExistingDocuments(prev => prev.map(doc => {
      if (doc.id === convId) {
        return {
          ...doc,
          document: document
        };
      }
      return doc;
    }));
    localStorage.setItem('docsConversationHistory', JSON.stringify(updatedHistory));
  };
  
  // 대화 저장
  const saveConversation = () => {
    if (messages.length === 0) return;
    
    const newConversation = {
      id: Date.now(),
      title: selectedDocument || currentDocument?.type || `대화 ${new Date().toLocaleDateString()}`,
      messages: messages,
      document: currentDocument,
      sessionId: sessionId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    const updatedHistory = [...conversationHistory, newConversation];
    setConversationHistory(updatedHistory);
    setExistingDocuments(prev => [...prev, {
      id: newConversation.id,
      name: newConversation.title,
      created_at: newConversation.created_at,
      messages: newConversation.messages,
      document: newConversation.document,
      sessionId: newConversation.sessionId
    }]);
    
    localStorage.setItem('docsConversationHistory', JSON.stringify(updatedHistory));
    setActiveConversationId(newConversation.id);
  };
  
  // 문서와 함께 대화 저장
  const saveConversationWithDocument = (document) => {
    if (messages.length === 0) return;
    
    const newConversation = {
      id: Date.now(),
      title: document?.type || selectedDocument || `대화 ${new Date().toLocaleDateString()}`,
      messages: messages,
      document: document,
      sessionId: sessionId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    const updatedHistory = [...conversationHistory, newConversation];
    setConversationHistory(updatedHistory);
    setExistingDocuments(prev => [...prev, {
      id: newConversation.id,
      name: newConversation.title,
      created_at: newConversation.created_at,
      messages: newConversation.messages,
      document: newConversation.document,
      sessionId: newConversation.sessionId
    }]);
    
    localStorage.setItem('docsConversationHistory', JSON.stringify(updatedHistory));
    setActiveConversationId(newConversation.id);
  };
  
  // 새 문서 생성
  const handleNewDocument = () => {
    // 현재 대화 저장
    if (messages.length > 0 && !activeConversationId) {
      saveConversation();
    }
    
    // 초기화
    setMessages([]);
    setSelectedDocument('');
    setSessionId(null);
    setRequiresInterrupt(false);
    setInterruptData(null);
    setDocumentOptions([]);
    setCurrentDocument(null);
    setActiveConversationId(null);
  };
  
  // 이전 대화 불러오기
  const loadConversation = (doc) => {
    console.log('대화 불러오기:', doc);
    console.log('문서 내용:', doc.document);
    console.log('문서 fields:', doc.document?.fields);
    console.log('문서 content:', doc.document?.content);
    
    // 현재 대화 저장
    if (messages.length > 0 && !activeConversationId) {
      saveConversation();
    }
    
    // 선택한 대화 불러오기
    setMessages(doc.messages || []);
    setSelectedDocument(doc.name);
    setCurrentDocument(doc.document || null);
    setSessionId(doc.sessionId || null);
    setActiveConversationId(doc.id);
    setRequiresInterrupt(false);
    setInterruptData(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="docs-page">
      {/* Left Sidebar */}
      <div className="docs-sidebar">
        <h2>문서 생성</h2>
        
        <button className="new-doc-btn" onClick={handleNewDocument}>
          <span className="plus-icon">+</span>
          새로운 문서 생성
        </button>

        <div className="existing-docs">
          <h3>
            기존 문서
            {existingDocuments.length > 0 && (
              <button 
                className="clear-history-btn"
                onClick={() => {
                  if (window.confirm('모든 대화 기록을 삭제하시겠습니까?')) {
                    setConversationHistory([]);
                    setExistingDocuments([]);
                    localStorage.removeItem('docsConversationHistory');
                    handleNewDocument();
                  }
                }}
              >
                전체 삭제
              </button>
            )}
          </h3>
          {existingDocuments.length > 0 ? (
            existingDocuments.map((doc) => (
              <div 
                key={doc.id} 
                className={`doc-item ${activeConversationId === doc.id ? 'active' : ''}`}
                onClick={() => loadConversation(doc)}
              >
                <span className="doc-icon">📄</span>
                <span className="doc-name">{doc.name}</span>
                <span className="doc-arrow">›</span>
              </div>
            ))
          ) : (
            <div className="no-docs">
              <p>기존 문서가 없습니다.</p>
            </div>
          )}
        </div>
      </div>

      {/* Center Content Area */}
      <div className="docs-main">
        <div className="document-content">
          {currentDocument ? (
            <>
              <h1>{selectedDocument || currentDocument?.type || '생성된 문서'}</h1>
              <div className="document-body">
                {currentDocument?.fields ? 
                  formatDocumentContent(currentDocument.fields, currentDocument.type) :
                  currentDocument?.content ? (
                    typeof currentDocument.content === 'string' ? 
                      <div className="generated-document">
                        <pre className="document-content-text">
                          {currentDocument.content}
                        </pre>
                      </div> :
                      formatDocumentContent(currentDocument.content, currentDocument.type)
                  ) : (
                    <div className="generated-document">
                      <pre className="document-content-text">
                        {JSON.stringify(currentDocument, null, 2)}
                      </pre>
                    </div>
                  )
                }
              </div>
            </>
          ) : (
            <div className="empty-document">
              <p>왼쪽에서 '새로운 문서 생성'을 클릭하거나</p>
              <p>오른쪽 패널에서 문서 작성을 시작해주세요.</p>
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - AI Assistant */}
      <div className="docs-ai-panel">
        <h2>문서 생성 요청</h2>
        
        <div className="docs-chat-container" ref={chatContainerRef} key={renderKey}>
          {messages.length === 0 ? (
            <div className="docs-initial-prompt">
              <p>문서 작성을 시작하려면 아래 예시를 참고하세요:</p>
              <ul>
                <li>"영업방문 결과보고서 작성해줘"</li>
                <li>"제품설명회 신청서를 만들어주세요"</li>
                <li>"제품설명회 결과보고서 작성"</li>
              </ul>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`docs-message docs-${msg.type}-message`}>
                {msg.type === 'ai' && <div className="docs-ai-avatar">🤖</div>}
                <div className="docs-message-content">
                  {msg.content}
                  
                  {/* 문서 타입 선택 옵션 표시 */}
                  {msg.interrupt && msg.data?.options && (
                    <div className="document-options">
                      {msg.data.options.map((option) => (
                        <button
                          key={option.value}
                          className="option-btn"
                          onClick={() => handleDocumentTypeSelect(option)}
                          disabled={isLoading}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  {/* 확인 버튼 (예/아니오) 표시 */}
                  {msg.interrupt && msg.data?.interrupt_type === 'verification' && !msg.data?.options && (
                    <div className="verification-buttons">
                      <button
                        className="verification-btn yes-btn"
                        onClick={() => handleResumeSession('네, 맞습니다', 'verification_reply')}
                        disabled={isLoading}
                      >
                        예
                      </button>
                      <button
                        className="verification-btn no-btn"
                        onClick={() => handleResumeSession('아니오, 다시 선택하겠습니다', 'verification_reply')}
                        disabled={isLoading}
                      >
                        아니오
                      </button>
                    </div>
                  )}
                  
                  {/* 성공 메시지 */}
                  {msg.data?.document_path && (
                    <div className="success-info">
                      <p>✅ 문서가 성공적으로 생성되었습니다!</p>
                      <p>파일 경로: {msg.data.document_path}</p>
                    </div>
                  )}
                  
                  {/* 오류 메시지 */}
                  {msg.error && (
                    <div className="error-info">
                      ⚠️ {msg.content}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          
          {/* 로딩 인디케이터 */}
          {isLoading && (
            <div className="docs-message docs-ai-message">
              <div className="docs-ai-avatar">🤖</div>
              <div className="docs-message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          {/* 스크롤 끝 지점 */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="docs-input-area">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={requiresInterrupt ? 
              "요청된 정보를 입력해주세요..." : 
              "문서 작성 요청을 입력해주세요..."}
            className="docs-message-input"
            disabled={isLoading}
            rows="3"
          />
          <button 
            onClick={handleSendMessage}
            className="docs-send-button"
            disabled={isLoading || !inputMessage.trim()}
          >
            {isLoading ? '처리 중...' : '전송'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Docs; 