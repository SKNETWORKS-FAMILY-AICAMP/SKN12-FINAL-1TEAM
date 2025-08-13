import React, { useState, useEffect } from 'react';
import { getDocuments, getDocumentDetail, getDocumentContent } from '../services/api';
import './Search.css';

const Search = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);

  // 컴포넌트 마운트 시 문서 목록 가져오기
  useEffect(() => {
    fetchDocuments();
  }, []);

  // 내부/외부 구분 로직
  const determineClassification = (docType, docTitle) => {
    // 외부 문서 키워드들
    const externalKeywords = [
      '계약서', '협약서', '제휴', '파트너십', '외부', '고객', '공급업체',
      'vendor', 'supplier', 'contract', 'agreement', 'partnership'
    ];
    
    // 내부 문서 키워드들
    const internalKeywords = [
      '규정', '정책', '매뉴얼', '가이드라인', '절차', '내규', '운영규정',
      'policy', 'manual', 'guideline', 'procedure', 'regulation'
    ];
    
    const searchText = (docTitle + ' ' + docType).toLowerCase();
    
    // 외부 키워드가 포함되어 있으면 외부
    for (const keyword of externalKeywords) {
      if (searchText.includes(keyword.toLowerCase())) {
        return '외부';
      }
    }
    
    // 내부 키워드가 포함되어 있으면 내부
    for (const keyword of internalKeywords) {
      if (searchText.includes(keyword.toLowerCase())) {
        return '내부';
      }
    }
    
    // 기본값은 내부
    return '내부';
  };

  const fetchDocuments = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const documents = await getDocuments();
      
      // 백엔드 응답을 프론트엔드 형식으로 변환
      const formattedDocuments = documents.map(doc => ({
        id: doc.doc_id,
        documentName: doc.doc_title,
        classification: determineClassification(doc.doc_type, doc.doc_title),
        author: '관리자', // 임시로 관리자로 표시
        creationDate: new Date(doc.created_at).toLocaleDateString('ko-KR'),
        docType: doc.doc_type,
        filePath: doc.file_path
      }));
      
      setSearchResults(formattedDocuments);
    } catch (error) {
      console.error('문서 목록 조회 실패:', error);
      setError('문서 목록을 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    // 실제 검색 로직은 나중에 구현
    console.log('Searching for:', searchQuery);
  };

  // 문서 상세 조회
  const handleDocumentClick = async (docId) => {
    setDetailLoading(true);
    setDetailError('');
    setIsDetailModalOpen(true);
    
    try {
      // 로그인 여부 확인
      const token = localStorage.getItem('narutalk_token');
      if (!token) {
        setDetailError('문서를 조회하려면 로그인이 필요합니다.');
        setDetailLoading(false);
        return;
      }

      // 문서 상세 정보 가져오기
      const documentDetail = await getDocumentDetail(docId);
      
      // 문서 내용 가져오기 (API가 있는 경우에만)
      let documentContent = {};
      try {
        documentContent = await getDocumentContent(docId);
      } catch (contentError) {
        console.log('문서 내용 API가 없거나 접근 불가:', contentError);
        // 내용을 가져올 수 없어도 상세 정보는 표시
      }
      
      // 문서 상세 정보와 내용을 합치기
      const fullDocument = {
        ...documentDetail,
        ...documentContent
      };
      
      setSelectedDocument(fullDocument);
    } catch (error) {
      console.error('문서 상세 조회 실패:', error);
      if (error.message?.includes('Not authenticated')) {
        setDetailError('문서를 조회하려면 로그인이 필요합니다.');
      } else if (error.message?.includes('Forbidden')) {
        setDetailError('문서 조회 권한이 없습니다. 관리자 권한이 필요합니다.');
      } else {
        setDetailError('문서 상세 정보를 불러오는데 실패했습니다.');
      }
    } finally {
      setDetailLoading(false);
    }
  };

  // 모달 닫기
  const handleCloseModal = () => {
    setIsDetailModalOpen(false);
    setSelectedDocument(null);
    setDetailError('');
  };

  // 개별 체크박스 핸들러
  const handleCheckboxChange = (id) => {
    const newSelectedItems = new Set(selectedItems);
    if (newSelectedItems.has(id)) {
      newSelectedItems.delete(id);
    } else {
      newSelectedItems.add(id);
    }
    setSelectedItems(newSelectedItems);
    
    // 전체 선택 체크박스 상태 업데이트
    setSelectAll(newSelectedItems.size === searchResults.length && searchResults.length > 0);
  };

  // 전체 선택 체크박스 핸들러
  const handleSelectAllChange = () => {
    if (selectAll) {
      setSelectedItems(new Set());
    } else {
      const allIds = searchResults.map(doc => doc.id);
      setSelectedItems(new Set(allIds));
    }
    setSelectAll(!selectAll);
  };

  // 선택된 항목 삭제
  const handleDeleteSelected = async () => {
    if (selectedItems.size === 0) {
      alert('삭제할 문서를 선택해주세요.');
      return;
    }

    if (!window.confirm(`선택한 ${selectedItems.size}개의 문서를 삭제하시겠습니까?`)) {
      return;
    }

    // TODO: 실제 삭제 API 호출
    console.log('삭제할 문서 ID:', Array.from(selectedItems));
    alert('문서 삭제 기능은 아직 구현되지 않았습니다.');
    
    // 삭제 후 선택 초기화
    setSelectedItems(new Set());
    setSelectAll(false);
  };

  return (
    <div className="search-page">
      <div className="search-header">
        <h1>내/외부 문서 검색</h1>
      </div>

      <div className="document-search-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <div className="search-input-wrapper">
              <i className="search-icon">🔍</i>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="검색어를 입력하세요..."
                className="search-input"
              />
            </div>
            <button type="submit" className="search-button">
              검색
            </button>
          </div>
        </form>

        <div className="search-toolbar">
          <div className="toolbar-left">
            {selectedItems.size > 0 && (
              <>
                <button 
                  className="delete-button"
                  onClick={handleDeleteSelected}
                  title="선택 삭제"
                >
                  🗑️ 삭제
                </button>
                <span className="selected-count">
                  {selectedItems.size}개 선택됨
                </span>
              </>
            )}
          </div>
          <div className="search-filters">
            <button className="filter-button active">문서명</button>
            <button className="filter-button">최신순</button>
            <button className="filter-button">작성자</button>
          </div>
        </div>

        {/* 로딩 및 오류 메시지 */}
        {isLoading && (
          <div className="loading-message">
            문서 목록을 불러오는 중...
          </div>
        )}
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="search-results">
          <div className="results-table">
            <table>
              <thead>
                <tr>
                  <th className="checkbox-column">
                    <input
                      type="checkbox"
                      checked={selectAll}
                      onChange={handleSelectAllChange}
                    />
                  </th>
                  <th>문서명</th>
                  <th>내/외부 구분</th>
                  <th>작성자</th>
                  <th>작성일</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.length === 0 && !isLoading && !error ? (
                  <tr>
                    <td colSpan="5" className="no-results">
                      업로드된 문서가 없습니다.
                    </td>
                  </tr>
                ) : (
                  searchResults.map((result) => (
                    <tr 
                      key={result.id} 
                      className={`document-row ${selectedItems.has(result.id) ? 'selected' : ''}`}
                    >
                      <td className="checkbox-column" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedItems.has(result.id)}
                          onChange={() => handleCheckboxChange(result.id)}
                        />
                      </td>
                      <td onClick={() => handleDocumentClick(result.id)}>
                        {result.documentName}
                      </td>
                      <td onClick={() => handleDocumentClick(result.id)}>
                        <span className={`classification-tag ${result.classification === '내부' ? 'internal' : 'external'}`}>
                          {result.classification}
                        </span>
                      </td>
                      <td onClick={() => handleDocumentClick(result.id)}>
                        {result.author}
                      </td>
                      <td onClick={() => handleDocumentClick(result.id)}>
                        {result.creationDate}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 문서 상세 조회 모달 */}
      {isDetailModalOpen && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>문서 상세 정보</h2>
              <button className="modal-close" onClick={handleCloseModal}>
                ✕
              </button>
            </div>
            
            <div className="modal-body">
              {detailLoading && (
                <div className="loading-message">
                  문서 정보를 불러오는 중...
                </div>
              )}
              
              {detailError && (
                <div className="error-message">
                  {detailError}
                </div>
              )}
              
              {selectedDocument && !detailLoading && (
                <div className="document-detail">
                  <div className="detail-item">
                    <label>문서 ID:</label>
                    <span>{selectedDocument.doc_id}</span>
                  </div>
                  <div className="detail-item">
                    <label>문서명:</label>
                    <span>{selectedDocument.doc_title}</span>
                  </div>
                  <div className="detail-item">
                    <label>문서 타입:</label>
                    <span>{selectedDocument.doc_type}</span>
                  </div>
                  <div className="detail-item">
                    <label>파일 경로:</label>
                    <span>{selectedDocument.file_path}</span>
                  </div>
                  <div className="detail-item">
                    <label>업로드 시간:</label>
                    <span>{new Date(selectedDocument.created_at).toLocaleString('ko-KR')}</span>
                  </div>
                  {selectedDocument.uploader_id && (
                    <div className="detail-item">
                      <label>업로더 ID:</label>
                      <span>{selectedDocument.uploader_id}</span>
                    </div>
                  )}
                  
                  {/* 파일 다운로드 링크 */}
                  {selectedDocument.file_path && (
                    <div className="detail-item">
                      <label>파일 다운로드:</label>
                      <a 
                        href={selectedDocument.file_path} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ 
                          color: '#6f42c1', 
                          textDecoration: 'none',
                          fontWeight: '500'
                        }}
                      >
                        📄 파일 다운로드
                      </a>
                    </div>
                  )}
                  
                  {/* 문서 내용 표시 (있는 경우에만) */}
                  {selectedDocument.content && (
                    <div className="detail-item document-content">
                      <label>문서 내용:</label>
                      <div className="content-display">
                        <pre>{selectedDocument.content}</pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Search;