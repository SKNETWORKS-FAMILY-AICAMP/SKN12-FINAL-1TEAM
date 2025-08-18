import React, { useState, useEffect } from 'react';
import { getDocuments, getDocumentDetail, getDocumentContent, getEmployeeInfo, getBranches } from '../services/api';
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
  const [selectedCategory, setSelectedCategory] = useState('전체');
  const [selectedSubCategory, setSelectedSubCategory] = useState('');
  const [filteredResults, setFilteredResults] = useState([]);
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [employeeList, setEmployeeList] = useState([]);
  const [branchList, setBranchList] = useState([]);
  const [showDataList, setShowDataList] = useState(false);
  const [dataListType, setDataListType] = useState('');

  // 컴포넌트 마운트 시 문서 목록 가져오기
  useEffect(() => {
    fetchDocuments();
    fetchEmployeeInfo();
    fetchBranches();
  }, []);

  // 직원 정보 가져오기
  const fetchEmployeeInfo = async () => {
    try {
      const data = await getEmployeeInfo();
      if (Array.isArray(data)) {
        setEmployeeList(data);
      }
    } catch (error) {
      console.error('직원 정보 조회 실패:', error);
    }
  };

  // 지점 정보 가져오기
  const fetchBranches = async () => {
    try {
      const data = await getBranches();
      if (Array.isArray(data)) {
        setBranchList(data);
      }
    } catch (error) {
      console.error('지점 정보 조회 실패:', error);
    }
  };

  // 카테고리 정의
  const categories = {
    '인사': {
      icon: '👥',
      subCategories: [
        { name: '직원 정보', keywords: ['직원', '사원', '인사', '채용', '퇴직', '승진', '평가', '급여', '연봉'] },
        { name: '지점 정보', keywords: ['지점', '지사', '본사', '영업점', '사무소', '조직', '부서'] }
      ]
    },
    '규정': {
      icon: '📋',
      subCategories: [
        { name: '운영규정', keywords: ['운영', '운영규정', '내규'] },
        { name: '인사규정', keywords: ['인사규정', '인사규칙', '취업규칙'] },
        { name: '보안정책', keywords: ['보안', '정보보호', '개인정보'] },
        { name: '업무지침', keywords: ['지침', '가이드', '업무지침', '매뉴얼'] },
        { name: '준법규정', keywords: ['컴플라이언스', '준법', '법규'] }
      ]
    },
    '문서': {
      icon: '📄',
      subCategories: [
        { name: '계약서', keywords: ['계약', '계약서', '협약', '협약서'] },
        { name: '보고서', keywords: ['보고서', '리포트', '업무보고'] },
        { name: '제안서', keywords: ['제안', '제안서', '기획서'] },
        { name: '회의록', keywords: ['회의', '회의록', '미팅'] },
        { name: '공문서', keywords: ['공문', '공식문서', '공지'] }
      ]
    }
  };

  // 카테고리 확장/축소 토글
  const toggleCategoryExpansion = (category) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
      // 축소할 때 하위 카테고리 선택 초기화
      if (selectedCategory === category) {
        setSelectedSubCategory('');
      }
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  // 카테고리 선택 핸들러
  const handleCategorySelect = (category, subCategory = '') => {
    setSelectedCategory(category);
    setSelectedSubCategory(subCategory);
    
    // 직원 정보 또는 지점 정보 하위 카테고리를 선택했을 때
    if (category === '인사' && subCategory === '직원 정보') {
      setShowDataList(true);
      setDataListType('employee');
    } else if (category === '인사' && subCategory === '지점 정보') {
      setShowDataList(true);
      setDataListType('branch');
    } else {
      setShowDataList(false);
      setDataListType('');
    }
    
    // 하위 카테고리를 선택했을 때만 확장
    if (subCategory && !expandedCategories.has(category)) {
      toggleCategoryExpansion(category);
    }
  };

  // 카테고리 필터링
  useEffect(() => {
    if (selectedCategory === '전체') {
      setFilteredResults(searchResults);
    } else {
      const filtered = searchResults.filter(doc => {
        const docTitleLower = doc.documentName.toLowerCase();
        const docTypeLower = doc.docType?.toLowerCase() || '';
        
        // 하위 카테고리가 선택된 경우
        if (selectedSubCategory) {
          const category = categories[selectedCategory];
          if (category) {
            const subCat = category.subCategories.find(sub => sub.name === selectedSubCategory);
            if (subCat) {
              return subCat.keywords.some(keyword => 
                docTitleLower.includes(keyword.toLowerCase()) ||
                docTypeLower.includes(keyword.toLowerCase())
              );
            }
          }
        } else {
          // 메인 카테고리만 선택된 경우
          const category = categories[selectedCategory];
          if (category) {
            return category.subCategories.some(subCat =>
              subCat.keywords.some(keyword =>
                docTitleLower.includes(keyword.toLowerCase()) ||
                docTypeLower.includes(keyword.toLowerCase())
              )
            );
          }
        }
        return false;
      });
      setFilteredResults(filtered);
    }
  }, [selectedCategory, selectedSubCategory, searchResults]);

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
      
      // documents가 배열인지 확인
      if (!Array.isArray(documents)) {
        console.warn('문서 목록이 비어있거나 형식이 올바르지 않습니다');
        setSearchResults([]);
        setIsLoading(false);
        return;
      }
      
      // 백엔드 응답을 프론트엔드 형식으로 변환
      const formattedDocuments = documents.map(doc => ({
        id: String(doc.doc_id || ''), // doc_id를 문자열로 변환
        documentName: doc.doc_title || 'Untitled',
        classification: determineClassification(doc.doc_type, doc.doc_title),
        author: '관리자', // 임시로 관리자로 표시
        creationDate: doc.created_at ? new Date(doc.created_at).toLocaleDateString('ko-KR') : 'N/A',
        docType: doc.doc_type || '-'
      }));
      
      setSearchResults(formattedDocuments);
    } catch (error) {
      console.error('문서 목록 조회 실패:', error);
      // 오류가 발생해도 앱이 정상 동작하도록 빈 배열 설정
      setSearchResults([]);
      setError('');
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
      // 토큰 가져오기
      const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
      if (!token) {
        setDetailError('문서를 조회하려면 로그인이 필요합니다.');
        setDetailLoading(false);
        return;
      }

      // 문서 상세 정보 가져오기 (8010 포트 직접 호출)
      const response = await fetch(`http://localhost:8010/documents/${docId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`문서 조회 실패: ${response.status}`);
      }

      const documentDetail = await response.json();
      
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
    setSelectAll(newSelectedItems.size === filteredResults.length && filteredResults.length > 0);
  };

  // 전체 선택 체크박스 핸들러
  const handleSelectAllChange = () => {
    if (selectAll) {
      setSelectedItems(new Set());
    } else {
      const allIds = filteredResults.map(doc => doc.id);
      setSelectedItems(new Set(allIds));
    }
    setSelectAll(!selectAll);
  };

  // 단일 문서 삭제
  const handleDeleteSingle = async (docId) => {
    if (!window.confirm('이 문서를 삭제하시겠습니까?')) {
      return;
    }

    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    
    try {
      const response = await fetch(`http://localhost:8010/documents/${docId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        alert('✅ 문서가 삭제되었습니다.');
        // 성공적으로 삭제된 문서를 목록에서 제거
        setSearchResults(prevResults => 
          prevResults.filter(doc => doc.id !== docId)
        );
        // 선택 항목에서도 제거
        setSelectedItems(prev => {
          const newSet = new Set(prev);
          newSet.delete(docId);
          return newSet;
        });
      } else {
        const error = await response.text();
        alert(`❌ 문서 삭제 실패: ${error}`);
      }
    } catch (error) {
      console.error('문서 삭제 오류:', error);
      alert(`❌ 문서 삭제 중 오류가 발생했습니다.`);
    }
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

    const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
    const selectedIds = Array.from(selectedItems);
    let successCount = 0;
    let failCount = 0;
    
    // 각 문서를 순차적으로 삭제
    for (const docId of selectedIds) {
      try {
        const response = await fetch(`http://localhost:8010/documents/${docId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          successCount++;
          // 성공적으로 삭제된 문서를 목록에서 제거
          setSearchResults(prevResults => 
            prevResults.filter(doc => doc.id !== docId)
          );
        } else {
          failCount++;
          console.error(`문서 ${docId} 삭제 실패:`, response.status);
        }
      } catch (error) {
        failCount++;
        console.error(`문서 ${docId} 삭제 오류:`, error);
      }
    }
    
    // 결과 메시지 표시
    if (successCount > 0 && failCount === 0) {
      alert(`✅ ${successCount}개의 문서가 삭제되었습니다.`);
    } else if (successCount > 0 && failCount > 0) {
      alert(`⚠️ ${successCount}개 삭제 성공, ${failCount}개 삭제 실패`);
    } else {
      alert(`❌ 문서 삭제에 실패했습니다.`);
    }
    
    // 삭제 후 선택 초기화
    setSelectedItems(new Set());
    setSelectAll(false);
  };

  return (
    <div className="search-page">
      <div className="search-header">
        <h1>내/외부 문서 검색</h1>
      </div>

      <div className="search-container-with-sidebar">
        {/* 카테고리 사이드바 */}
        <div className="category-sidebar">
          <h3 className="sidebar-title">카테고리</h3>
          <ul className="category-list">
            {/* 전체 카테고리 */}
            <li 
              className={selectedCategory === '전체' ? 'active' : ''}
              onClick={() => handleCategorySelect('전체')}
            >
              <span className="category-icon">📁</span>
              <span className="category-name">전체</span>
              <span className="category-count">{searchResults.length}</span>
            </li>
            
            {/* 메인 카테고리들 */}
            {Object.entries(categories).map(([categoryName, categoryData]) => {
              const categoryCount = searchResults.filter(doc => {
                const docTitleLower = doc.documentName.toLowerCase();
                const docTypeLower = doc.docType?.toLowerCase() || '';
                return categoryData.subCategories.some(subCat =>
                  subCat.keywords.some(keyword =>
                    docTitleLower.includes(keyword.toLowerCase()) ||
                    docTypeLower.includes(keyword.toLowerCase())
                  )
                );
              }).length;

              return (
                <React.Fragment key={categoryName}>
                  <li 
                    className={`category-item ${selectedCategory === categoryName && !selectedSubCategory ? 'active' : ''} ${expandedCategories.has(categoryName) ? 'expanded' : ''}`}
                  >
                    <div 
                      className="category-main"
                      onClick={() => handleCategorySelect(categoryName)}
                    >
                      <span className="category-icon">{categoryData.icon}</span>
                      <span className="category-name">{categoryName}</span>
                      <span className="category-count">{categoryCount}</span>
                    </div>
                    <button
                      className="expand-button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleCategoryExpansion(categoryName);
                      }}
                    >
                      {expandedCategories.has(categoryName) ? '▼' : '▶'}
                    </button>
                  </li>
                  
                  {/* 하위 카테고리 */}
                  {expandedCategories.has(categoryName) && (
                    <ul className="sub-category-list">
                      {categoryData.subCategories.map(subCat => {
                        const subCount = searchResults.filter(doc => {
                          const docTitleLower = doc.documentName.toLowerCase();
                          const docTypeLower = doc.docType?.toLowerCase() || '';
                          return subCat.keywords.some(keyword =>
                            docTitleLower.includes(keyword.toLowerCase()) ||
                            docTypeLower.includes(keyword.toLowerCase())
                          );
                        }).length;

                        return (
                          <li
                            key={subCat.name}
                            className={selectedCategory === categoryName && selectedSubCategory === subCat.name ? 'active' : ''}
                            onClick={() => handleCategorySelect(categoryName, subCat.name)}
                          >
                            <span className="sub-category-name">{subCat.name}</span>
                            <span className="sub-category-count">{subCount}</span>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </React.Fragment>
              );
            })}
          </ul>
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
          {/* 직원/지점 정보 리스트 표시 */}
          {showDataList && dataListType === 'employee' && (
            <div className="data-list-container">
              <h3>직원 정보 목록</h3>
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>이름</th>
                      <th>사번</th>
                      <th>직급</th>
                      <th>지점</th>
                      <th>연락처</th>
                      <th>평가</th>
                    </tr>
                  </thead>
                  <tbody>
                    {employeeList.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="no-results">
                          직원 정보가 없습니다.
                        </td>
                      </tr>
                    ) : (
                      employeeList.map((employee) => (
                        <tr key={employee.employee_info_id}>
                          <td>{employee.name}</td>
                          <td>{employee.employee_number || '-'}</td>
                          <td>{employee.position || '-'}</td>
                          <td>{employee.branch_name || '-'}</td>
                          <td>{employee.contact_number || '-'}</td>
                          <td>
                            <span className={`evaluation-badge ${employee.latest_evaluation?.toLowerCase()}`}>
                              {employee.latest_evaluation || '-'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {showDataList && dataListType === 'branch' && (
            <div className="data-list-container">
              <h3>지점 정보 목록</h3>
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>지점명</th>
                      <th>본부</th>
                      <th>부서</th>
                      <th>연락처</th>
                      <th>상태</th>
                      <th>비고</th>
                    </tr>
                  </thead>
                  <tbody>
                    {branchList.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="no-results">
                          지점 정보가 없습니다.
                        </td>
                      </tr>
                    ) : (
                      branchList.map((branch) => (
                        <tr key={branch.branch_id}>
                          <td>{branch.branch_name}</td>
                          <td>{branch.headquarters || '-'}</td>
                          <td>{branch.department || '-'}</td>
                          <td>{branch.contact_number || '-'}</td>
                          <td>
                            <span className={`status-badge ${branch.status}`}>
                              {branch.status === 'active' ? '활성' : '비활성'}
                            </span>
                          </td>
                          <td>{branch.notes || '-'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 기존 문서 리스트 표시 */}
          {!showDataList && (
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
                  <th>관리</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.length === 0 && !isLoading && !error ? (
                  <tr>
                    <td colSpan="6" className="no-results">
                      {selectedCategory !== '전체' 
                        ? `${selectedCategory} 카테고리에 문서가 없습니다.`
                        : '업로드된 문서가 없습니다.'}
                    </td>
                  </tr>
                ) : (
                  filteredResults.map((result) => (
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
                      <td>
                        <button
                          className="delete-icon-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSingle(result.id);
                          }}
                          title="삭제"
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '1.2rem',
                            padding: '5px',
                            color: '#dc3545'
                          }}
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          )}
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
                    <label>업로드 시간:</label>
                    <span>{new Date(selectedDocument.created_at).toLocaleString('ko-KR')}</span>
                  </div>
                  {selectedDocument.uploader_id && (
                    <div className="detail-item">
                      <label>업로더 ID:</label>
                      <span>{selectedDocument.uploader_id}</span>
                    </div>
                  )}
                  {selectedDocument.summary && (
                    <div className="detail-item">
                      <label>문서 요약:</label>
                      <div style={{ 
                        padding: '10px', 
                        backgroundColor: '#f8f9fa', 
                        borderRadius: '5px',
                        marginTop: '5px' 
                      }}>
                        {selectedDocument.summary}
                      </div>
                    </div>
                  )}
                  {selectedDocument.version && (
                    <div className="detail-item">
                      <label>버전:</label>
                      <span>{selectedDocument.version}</span>
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
    </div>
  );
};

export default Search;