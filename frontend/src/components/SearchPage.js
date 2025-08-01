import React, { useState, useEffect } from 'react';
import { getDocuments } from '../services/api';
import './SearchPage.css';

const SearchPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // 컴포넌트 마운트 시 문서 목록 가져오기
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const documents = await getDocuments();
      
      // 백엔드 응답을 프론트엔드 형식으로 변환
      const formattedDocuments = documents.map(doc => ({
        id: doc.doc_id,
        documentName: doc.doc_title,
        classification: '내부', // 기본값
        author: doc.uploader_name || `직원 ID: ${doc.uploader_id}`, // 이름이 있으면 이름, 없으면 ID
        creationDate: new Date(doc.created_at).toLocaleDateString('ko-KR'),
        aiSummary: doc.doc_type || '문서',
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

      <div className="search-container">
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
                  <th>AI 요약</th>
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
                    <tr key={result.id}>
                      <td>{result.documentName}</td>
                      <td>
                        <span className={`classification-tag ${result.classification === '내부' ? 'internal' : 'external'}`}>
                          {result.classification}
                        </span>
                      </td>
                      <td>{result.author}</td>
                      <td>{result.creationDate}</td>
                      <td>{result.aiSummary}</td>
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

export default SearchPage; 