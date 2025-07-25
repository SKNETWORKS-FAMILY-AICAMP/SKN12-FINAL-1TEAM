import React, { useState } from 'react';
import './DocsPage.css';

const DocsPage = () => {
  const [selectedDocType, setSelectedDocType] = useState('');
  const [docContent, setDocContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const docTypes = [
    { id: 'visit-report', name: '방문 보고서', icon: '📋' },
    { id: 'sales-report', name: '영업 실적 보고서', icon: '📊' },
    { id: 'proposal', name: '제안서', icon: '📝' },
    { id: 'contract', name: '계약서', icon: '📄' },
  ];

  const handleGenerate = async () => {
    if (!selectedDocType || !docContent.trim()) {
      alert('문서 유형과 내용을 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    // 실제 문서 생성 로직은 나중에 구현
    setTimeout(() => {
      setIsGenerating(false);
      alert('문서가 생성되었습니다!');
    }, 2000);
  };

  return (
    <div className="docs-page">
      <div className="docs-header">
        <h1>📄 문서 생성</h1>
        <p>AI를 활용하여 다양한 문서를 자동으로 생성하세요</p>
      </div>

      <div className="docs-container">
        <div className="docs-sidebar">
          <h3>문서 유형 선택</h3>
          <div className="doc-types">
            {docTypes.map((type) => (
              <div
                key={type.id}
                className={`doc-type ${selectedDocType === type.id ? 'selected' : ''}`}
                onClick={() => setSelectedDocType(type.id)}
              >
                <span className="doc-type-icon">{type.icon}</span>
                <span className="doc-type-name">{type.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="docs-main">
          <div className="doc-editor">
            <h3>문서 내용 입력</h3>
            <textarea
              value={docContent}
              onChange={(e) => setDocContent(e.target.value)}
              placeholder="문서 내용을 입력하거나 AI에게 요청사항을 설명하세요..."
              className="doc-textarea"
              rows="10"
            />
            
            <div className="doc-actions">
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !selectedDocType || !docContent.trim()}
                className="generate-button"
              >
                {isGenerating ? '생성 중...' : '문서 생성'}
              </button>
            </div>
          </div>

          <div className="doc-templates">
            <h3>템플릿 예시</h3>
            <div className="template-list">
              <div className="template-item">
                <h4>방문 보고서 템플릿</h4>
                <p>방문 일시, 방문 장소, 담당자, 논의 내용, 후속 조치사항을 포함한 보고서</p>
              </div>
              <div className="template-item">
                <h4>영업 실적 보고서 템플릿</h4>
                <p>월간/분기별 실적, 목표 대비 달성률, 주요 성과, 개선점을 포함한 보고서</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocsPage; 