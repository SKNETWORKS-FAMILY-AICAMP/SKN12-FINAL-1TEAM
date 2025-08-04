import React, { useState, useEffect } from 'react';
import { getDocuments } from '../services/api';
import './Search.css';

const Search = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

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

        <div className="search-filters">
          <button className="filter-button active">문서명</button>
          <button className="filter-button">최신순</button>
          <button className="filter-button">작성자</button>
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
                  <th>문서명</th>
                  <th>내/외부 구분</th>
                  <th>작성자</th>
                  <th>작성일</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.length === 0 && !isLoading && !error ? (
                  <tr>
                    <td colSpan="4" className="no-results">
                      업로드된 문서가 없습니다.
                    </td>
                  </tr>
                ) : (
                  searchResults.map((result) => (
                    <tr key={result.id}>
                      <td>{result.documentName}</td>
                      <td>
                        <span className={`classification-tag ${result.classification === '내부' ? 'internal' : 'external'}`}>
                          {result.classification}
                        </span>
                      </td>
                      <td>{result.author}</td>
                      <td>{result.creationDate}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Search; 