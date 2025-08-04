import React, { useState } from 'react';
import './Docs.css';

const Docs = () => {
  const [selectedDocument, setSelectedDocument] = useState('제품 설명회 결과 보고서');
  const [userMessage, setUserMessage] = useState('오늘 00 약국에서 00제품 설명회를 진행했어, 관련해서 결과 보고서를 작성해줘.');
  const [aiResponse, setAiResponse] = useState('네, 오늘 예정되어 있던 00 약국의 00 제품 설명회 정보와 고객 정보를 참고하여 결과 보고서 작성해 보겠습니다.');
  const [inputMessage, setInputMessage] = useState('');

  const existingDocuments = [];

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      // 실제로는 AI API 호출
      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="docs-page">
      {/* Left Sidebar */}
      <div className="docs-sidebar">
        <h2>문서 생성</h2>
        
        <button className="new-doc-btn">
          <span className="plus-icon">+</span>
          새로운 문서 생성
        </button>

        <div className="existing-docs">
          <h3>기존 문서</h3>
          {existingDocuments.length > 0 ? (
            existingDocuments.map((doc, index) => (
              <div key={index} className="doc-item">
                <span className="doc-icon">💬</span>
                <span className="doc-name">{doc}</span>
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
          <h1>{selectedDocument}</h1>
          <div className="document-body">
            {/* 문서 내용이 여기에 표시됩니다 */}
          </div>
        </div>
      </div>

      {/* Right Panel - AI Assistant */}
      <div className="docs-ai-panel">
        <h2>문서 생성 요청</h2>
        
        <div className="chat-container">
          {/* User Message */}
          <div className="message user-message">
            {userMessage}
          </div>

          {/* AI Response */}
          <div className="message ai-message">
            <div className="ai-avatar">👤</div>
            <div className="message-content">
              {aiResponse}
              <div className="ai-prompts">
                <p>제품설명회 세부 내역을 작성해주세요!</p>
                <ul>
                  <li>제품 설명회 주요 내용</li>
                  <li>참석 인원</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="input-area">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="질문을 입력해주세요"
            className="message-input"
          />
          <button 
            onClick={handleSendMessage}
            className="send-button"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
};

export default Docs; 