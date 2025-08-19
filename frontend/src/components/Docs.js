import React, { useState } from 'react';
import { analyzeClient } from '../services/api';
import './Docs.css';

const Docs = () => {
  const [selectedDocType, setSelectedDocType] = useState('');
  const [formData, setFormData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [generatedDocument, setGeneratedDocument] = useState(null);
  const [error, setError] = useState('');
  const [documentHistory, setDocumentHistory] = useState(() => {
    // localStorage에서 문서 기록 불러오기
    const saved = localStorage.getItem('documentHistory');
    return saved ? JSON.parse(saved) : [];
  });
  
  // 동적 필드를 위한 상태 (직원 및 의료전문가)
  const [staffMembers, setStaffMembers] = useState([{ team: '', name: '' }]);
  const [medicalProfessionals, setMedicalProfessionals] = useState([{ institution: '', name: '' }]);

  // 문서 타입별 필드 정의 (templates.yaml과 일치)
  const documentTypes = {
    '영업방문 결과보고서': {
      fields: [
        { name: '방문제목', label: '방문제목', type: 'text', required: true, placeholder: '방문 목적 또는 제목' },
        { name: '방문일', label: '방문일', type: 'date', required: true },
        { name: '병원명', label: '병원명', type: 'text', required: true, placeholder: '병원명' },
        { name: '지역구', label: '지역구', type: 'text', required: true, placeholder: '병원 지역구' },
        { name: '원장명', label: '원장명', type: 'text', required: true, placeholder: '병원 원장 이름' },
        { name: '원장연락처', label: '원장연락처', type: 'text', required: true, placeholder: '병원 원장 연락처' },
        { name: '담당자성명', label: '담당자성명', type: 'text', required: true, placeholder: '고객사 담당자 이름' },
        { name: '담당자부서', label: '담당자부서', type: 'text', required: true, placeholder: '고객사 담당자 소속부서' },
        { name: '담당자연락처', label: '담당자연락처', type: 'text', required: true, placeholder: '고객사 담당자 연락처' },
        { name: '지점', label: '지점', type: 'text', required: true, placeholder: '담당자 소속 지점' },
        { name: '지점연락처', label: '지점연락처', type: 'text', required: true, placeholder: '담당자 소속 지점 연락처' },
        { name: '고객사개요', label: '고객사개요', type: 'textarea', required: true, placeholder: '고객사에 대한 간단한 설명' },
        { name: '프로젝트개요', label: '프로젝트개요', type: 'textarea', required: true, placeholder: '진행 중인 프로젝트 개요' },
        { name: '방문및협의내용', label: '방문및협의내용', type: 'textarea', required: true, placeholder: '방문 시 논의한 주요 내용' },
        { name: '향후계획및일정', label: '향후계획및일정', type: 'textarea', required: true, placeholder: '향후 진햄할 계획과 일정' },
        { name: '협조사항및공유사항', label: '협조사항및공유사항', type: 'textarea', required: false, placeholder: '협조가 필요한 사항이나 공유할 내용' }
      ]
    },
    '제품설명회 시행 신청서': {
      fields: [
        { name: '구분', label: '구분', type: 'text', required: true, placeholder: '제품설명회 구분' },
        { name: 'PM참석', label: 'PM참석', type: 'text', required: true, placeholder: '참석/불참석' },
        { name: '일시', label: '일시', type: 'datetime-local', required: true },
        { name: '장소', label: '장소', type: 'text', required: true, placeholder: '제품설명회 장소' },
        { name: '제품명', label: '제품명', type: 'text', required: true, placeholder: '설명할 제품명' },
        { name: '참석인원', label: '참석인원', type: 'text', required: false, placeholder: '예상 참석 인원수 (직접 명시)' },
        { name: '제품설명회시행목적', label: '제품설명회시행목적', type: 'textarea', required: true, placeholder: '제품설명회를 진행하는 목적' },
        { name: '제품설명회주요내용', label: '제품설명회주요내용', type: 'textarea', required: true, placeholder: '제품설명회에서 다룰 주요 내용' },
        { name: 'staff', label: '참석 직원', type: 'dynamic_staff', maxCount: 3 },
        { name: 'medical', label: '참석 의료전문가', type: 'dynamic_medical', maxCount: 4 }
      ]
    },
    '제품설명회 시행 결과보고서': {
      fields: [
        { name: '구분', label: '구분', type: 'text', required: true, placeholder: '제품설명회 구분' },
        { name: 'PM참석', label: 'PM참석', type: 'text', required: true, placeholder: '참석/불참석' },
        { name: '일시', label: '일시', type: 'datetime-local', required: true },
        { name: '장소', label: '장소', type: 'text', required: true, placeholder: '제품설명회 실시 장소' },
        { name: '제품명', label: '제품명', type: 'text', required: true, placeholder: '설명한 제품명' },
        { name: '참석인원', label: '참석인원', type: 'text', required: false, placeholder: '실제 참석 인원수 (직접 명시)' },
        { name: '제품설명회시행목적', label: '제품설명회시행목적', type: 'textarea', required: true, placeholder: '제품설명회를 진행한 목적' },
        { name: '제품설명회주요내용', label: '제품설명회주요내용', type: 'textarea', required: true, placeholder: '제품설명회에서 다룬 주요 내용' },
        { name: '지급내역', label: '지급내역', type: 'text', required: false, placeholder: '지급한 항목들 (직접 명시)' },
        { name: '금액', label: '금액', type: 'text', required: false, placeholder: '총 지급 금액' },
        { name: '메뉴', label: '메뉴', type: 'text', required: false, placeholder: '제공한 식사 메뉴' },
        { name: '주류', label: '주류', type: 'text', required: false, placeholder: '제공한 주류' },
        { name: '1인금액', label: '1인금액', type: 'text', required: false, placeholder: '1인당 지급된 금액' },
        { name: 'staff', label: '참석 직원', type: 'dynamic_staff', maxCount: 4 },
        { name: 'medical', label: '참석 의료전문가', type: 'dynamic_medical', maxCount: 8 }
      ]
    }
  };

  // 입력값 변경 핸들러
  const handleInputChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  // 문서 타입 선택 핸들러
  const handleDocTypeSelect = (docType) => {
    setSelectedDocType(docType);
    setFormData({});
    setGeneratedDocument(null);
    setError('');
    // 동적 필드 초기화
    setStaffMembers([{ team: '', name: '' }]);
    setMedicalProfessionals([{ institution: '', name: '' }]);
  };
  
  // 직원 추가/삭제 핸들러
  const handleAddStaff = () => {
    const maxCount = selectedDocType === '제품설명회 시행 신청서' ? 3 : 4;
    if (staffMembers.length < maxCount) {
      setStaffMembers([...staffMembers, { team: '', name: '' }]);
    }
  };
  
  const handleRemoveStaff = (index) => {
    setStaffMembers(staffMembers.filter((_, i) => i !== index));
  };
  
  const handleStaffChange = (index, field, value) => {
    const updated = [...staffMembers];
    updated[index][field] = value;
    setStaffMembers(updated);
  };
  
  // 의료전문가 추가/삭제 핸들러
  const handleAddMedical = () => {
    const maxCount = selectedDocType === '제품설명회 시행 신청서' ? 4 : 8;
    if (medicalProfessionals.length < maxCount) {
      setMedicalProfessionals([...medicalProfessionals, { institution: '', name: '' }]);
    }
  };
  
  const handleRemoveMedical = (index) => {
    setMedicalProfessionals(medicalProfessionals.filter((_, i) => i !== index));
  };
  
  const handleMedicalChange = (index, field, value) => {
    const updated = [...medicalProfessionals];
    updated[index][field] = value;
    setMedicalProfessionals(updated);
  };

  // 문서 기록 저장
  const saveToHistory = (docType, docData, generatedContent) => {
    const newDoc = {
      id: Date.now(),
      type: docType,
      title: docData['방문제목'] || docData['구분'] || `${docType} - ${new Date().toLocaleDateString('ko-KR')}`,
      date: new Date().toISOString(),
      data: docData,
      content: generatedContent
    };
    
    const updatedHistory = [newDoc, ...documentHistory].slice(0, 20); // 최대 20개 저장
    setDocumentHistory(updatedHistory);
    localStorage.setItem('documentHistory', JSON.stringify(updatedHistory));
  };

  // 이전 문서 불러오기
  const handleLoadDocument = (doc) => {
    setSelectedDocType(doc.type);
    setFormData(doc.data);
    setGeneratedDocument(doc.content);
    setError('');
  };

  // 문서 기록 삭제
  const handleDeleteHistory = (docId) => {
    const updatedHistory = documentHistory.filter(doc => doc.id !== docId);
    setDocumentHistory(updatedHistory);
    localStorage.setItem('documentHistory', JSON.stringify(updatedHistory));
  };

  // 전체 기록 삭제
  const handleClearHistory = () => {
    if (window.confirm('모든 문서 기록을 삭제하시겠습니까?')) {
      setDocumentHistory([]);
      localStorage.removeItem('documentHistory');
    }
  };

  // 보고서 생성 핸들러
  const handleGenerateDocument = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      // 필수 필드 검증
      const currentFields = documentTypes[selectedDocType].fields;
      const missingFields = currentFields
        .filter(field => {
          if (field.type === 'dynamic_staff' || field.type === 'dynamic_medical') {
            return false; // 동적 필드는 별도 처리
          }
          return field.required && !formData[field.name];
        })
        .map(field => field.label);
      
      if (missingFields.length > 0) {
        setError(`다음 필수 항목을 입력해주세요: ${missingFields.join(', ')}`);
        setIsLoading(false);
        return;
      }
      
      // 동적 필드 검증
      if (selectedDocType.includes('제품설명회')) {
        const hasValidStaff = staffMembers.some(s => s.team && s.name);
        const hasValidMedical = medicalProfessionals.some(m => m.institution && m.name);
        
        if (!hasValidStaff || !hasValidMedical) {
          setError('최소 한 명의 직원과 의료전문가 정보를 입력해주세요.');
          setIsLoading(false);
          return;
        }
      }

      // 폼 데이터를 딕셔너리 형태로 준비 (새 엔드포인트용)
      const documentData = {};
      currentFields.forEach(field => {
        if (field.type === 'dynamic_staff') {
          // 직원 데이터를 이중 리스트로 처리 [['영업팀', '손현성'], ['영업팀', '최문영']]
          const validStaff = staffMembers.filter(s => s.team && s.name);
          documentData['참석직원'] = validStaff.map(s => [s.team, s.name]);
        } else if (field.type === 'dynamic_medical') {
          // 의료전문가 데이터를 이중 리스트로 처리 [['서울아산병원', '김의사'], ['단국대병원', '이의사']]
          const validMedical = medicalProfessionals.filter(m => m.institution && m.name);
          documentData['참석의료전문가'] = validMedical.map(m => [m.institution, m.name]);
        } else {
          const value = formData[field.name] || '';
          // 날짜 필드 특별 처리
          if (field.type === 'date' && value) {
            const date = new Date(value);
            documentData[field.label] = date.toLocaleDateString('ko-KR');
          } else if (field.type === 'datetime-local' && value) {
            const date = new Date(value);
            documentData[field.label] = `${date.toLocaleDateString('ko-KR')} ${date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
          } else {
            documentData[field.label] = value;
          }
        }
      });

      // 문서 타입도 추가
      documentData['문서타입'] = selectedDocType;

      // 디버깅용 - 콘솔에 출력
      console.log('준비된 문서 데이터 (딕셔너리 형태):', documentData);
      
      // TODO: 새로운 엔드포인트가 준비되면 아래와 같이 호출
      // const response = await callNewDocumentAPI({
      //   document_type: selectedDocType,
      //   document_data: documentData
      // });

      // 임시로 기존 API 사용 (폼 데이터를 문자열로 변환)
      const formattedData = currentFields
        .map(field => {
          const value = formData[field.name] || '';
          if (field.type === 'date' && value) {
            const date = new Date(value);
            return `${field.label}: ${date.toLocaleDateString('ko-KR')}`;
          }
          if (field.type === 'datetime-local' && value) {
            const date = new Date(value);
            return `${field.label}: ${date.toLocaleDateString('ko-KR')} ${date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
          }
          return `${field.label}: ${value || '없음'}`;
        })
        .join('\n');

      const query = `다음 정보를 바탕으로 ${selectedDocType}를 작성해주세요:\n\n${formattedData}`;
      
      // API 호출 (기존 방식 - 임시)
      const response = await analyzeClient({
        query: query,
        generate_docs: true
      });
      
      if (response.status === 'success') {
        setGeneratedDocument(response);
        // 문서 기록에 저장
        saveToHistory(selectedDocType, formData, response);
      } else {
        setError(response.message || '문서 생성에 실패했습니다.');
      }
    } catch (error) {
      console.error('문서 생성 오류:', error);
      setError('문서 생성 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 새 문서 작성 시작
  const startNewDocument = () => {
    setSelectedDocType('');
    setFormData({});
    setGeneratedDocument(null);
    setError('');
  };

  return (
    <div className="docs-page">
      {/* 왼쪽 사이드바 - 문서 기록 */}
      <div className="docs-sidebar">
        <h2>문서 기록</h2>
        <button className="new-doc-btn" onClick={startNewDocument}>
          <span className="plus-icon">+</span>
          새 문서 작성
        </button>
        
        <div className="history-section">
          <div className="history-header">
            <h3>이전 문서</h3>
            {documentHistory.length > 0 && (
              <button className="clear-history-btn" onClick={handleClearHistory}>
                전체 삭제
              </button>
            )}
          </div>
          
          {documentHistory.length > 0 ? (
            <div className="history-list">
              {documentHistory.map(doc => (
                <div 
                  key={doc.id} 
                  className="history-item"
                  onClick={() => handleLoadDocument(doc)}
                >
                  <div className="history-item-header">
                    <span className="doc-type-badge">{doc.type}</span>
                    <button 
                      className="delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteHistory(doc.id);
                      }}
                    >
                      ×
                    </button>
                  </div>
                  <div className="history-item-title">{doc.title}</div>
                  <div className="history-item-date">
                    {new Date(doc.date).toLocaleDateString('ko-KR')}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-history">
              <p>저장된 문서가 없습니다</p>
            </div>
          )}
        </div>
      </div>

      {/* 메인 콘텐츠 영역 */}
      <div className="docs-main">
        <div className="docs-header">
          <h1>문서 생성</h1>
        </div>

        <div className="docs-content">
        {!selectedDocType ? (
          // 문서 타입 선택 화면
          <div className="doc-type-selection">
            <h2>생성할 문서를 선택하세요</h2>
            <div className="doc-type-cards">
              {Object.keys(documentTypes).map(docType => (
                <div 
                  key={docType}
                  className="doc-type-card"
                  onClick={() => handleDocTypeSelect(docType)}
                >
                  <h3>{docType}</h3>
                  <p>
                    {docType === '영업방문결과보고서' && '고객사 방문 후 작성하는 결과 보고서'}
                    {docType === '제품설명회신청서' && '제품 설명회 개최를 위한 신청서'}
                    {docType === '제품설명회결과보고서' && '제품 설명회 진행 후 작성하는 결과 보고서'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          // 폼 입력 화면
          <div className="doc-form-container">
            <h2>{selectedDocType} 작성</h2>
            <p className="form-description">
              {selectedDocType} 작성을 위해 다음 정보를 입력해주세요:
            </p>

            <form className="doc-form" onSubmit={(e) => { e.preventDefault(); handleGenerateDocument(); }}>
              {documentTypes[selectedDocType].fields.map(field => {
                // 동적 직원 필드
                if (field.type === 'dynamic_staff') {
                  return (
                    <div key={field.name} className="form-field dynamic-field">
                      <label>
                        {field.label}
                        <span className="required">*</span>
                        <span className="field-info"> (최대 {field.maxCount}명)</span>
                      </label>
                      <div className="dynamic-inputs">
                        {staffMembers.map((staff, index) => (
                          <div key={index} className="dynamic-input-row">
                            <input
                              type="text"
                              placeholder="팀명"
                              value={staff.team}
                              onChange={(e) => handleStaffChange(index, 'team', e.target.value)}
                              className="team-input"
                            />
                            <input
                              type="text"
                              placeholder="성명"
                              value={staff.name}
                              onChange={(e) => handleStaffChange(index, 'name', e.target.value)}
                              className="name-input"
                            />
                            {staffMembers.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveStaff(index)}
                                className="remove-btn"
                              >
                                −
                              </button>
                            )}
                          </div>
                        ))}
                        {staffMembers.length < field.maxCount && (
                          <button
                            type="button"
                            onClick={handleAddStaff}
                            className="add-btn"
                          >
                            + 직원 추가
                          </button>
                        )}
                      </div>
                    </div>
                  );
                }
                
                // 동적 의료전문가 필드
                if (field.type === 'dynamic_medical') {
                  return (
                    <div key={field.name} className="form-field dynamic-field">
                      <label>
                        {field.label}
                        <span className="required">*</span>
                        <span className="field-info"> (최대 {field.maxCount}명)</span>
                      </label>
                      <div className="dynamic-inputs">
                        {medicalProfessionals.map((medical, index) => (
                          <div key={index} className="dynamic-input-row">
                            <input
                              type="text"
                              placeholder="의료기관명"
                              value={medical.institution}
                              onChange={(e) => handleMedicalChange(index, 'institution', e.target.value)}
                              className="institution-input"
                            />
                            <input
                              type="text"
                              placeholder="전문가 성명"
                              value={medical.name}
                              onChange={(e) => handleMedicalChange(index, 'name', e.target.value)}
                              className="name-input"
                            />
                            {medicalProfessionals.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveMedical(index)}
                                className="remove-btn"
                              >
                                −
                              </button>
                            )}
                          </div>
                        ))}
                        {medicalProfessionals.length < field.maxCount && (
                          <button
                            type="button"
                            onClick={handleAddMedical}
                            className="add-btn"
                          >
                            + 의료전문가 추가
                          </button>
                        )}
                      </div>
                    </div>
                  );
                }
                
                // 일반 필드
                return (
                  <div key={field.name} className="form-field">
                    <label htmlFor={field.name}>
                      {field.label}
                      {field.required && <span className="required">*</span>}
                    </label>
                    {field.type === 'textarea' ? (
                      <textarea
                        id={field.name}
                        value={formData[field.name] || ''}
                        onChange={(e) => handleInputChange(field.name, e.target.value)}
                        placeholder={field.placeholder}
                        required={field.required}
                        rows={4}
                      />
                    ) : (
                      <input
                        type={field.type}
                        id={field.name}
                        value={formData[field.name] || ''}
                        onChange={(e) => handleInputChange(field.name, e.target.value)}
                        placeholder={field.placeholder}
                        required={field.required}
                      />
                    )}
                  </div>
                );
              })}

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <div className="form-actions">
                <button 
                  type="submit" 
                  className="generate-btn"
                  disabled={isLoading}
                >
                  {isLoading ? '문서 생성 중...' : '문서 생성'}
                </button>
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={startNewDocument}
                >
                  취소
                </button>
              </div>
            </form>

            {/* 생성된 문서 표시 */}
            {generatedDocument && (
              <div className="generated-document">
                <h3>생성된 문서</h3>
                <div className="document-content">
                  {generatedDocument.response || generatedDocument.message}
                </div>
                {generatedDocument.files_generated && (
                  <div className="generated-files">
                    <h4>생성된 파일:</h4>
                    <ul>
                      {generatedDocument.files_generated.map((file, index) => (
                        <li key={index}>{file}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

export default Docs;