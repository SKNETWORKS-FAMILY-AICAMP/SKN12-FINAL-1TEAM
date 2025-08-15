import React, { useState, useEffect } from 'react';
import { registerEmployee, getEmployeeInfo, getEmployees, uploadDocumentWithSSE, uploadDocumentsBatchWithSSE, getDocuments } from '../services/api';
import ProcessProgressBar from './ProcessProgressBar';
import BatchProcessProgressBar from './BatchProcessProgressBar';
import './Admin.css';

const Admin = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState('employees');
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showAccountCreateModal, setShowAccountCreateModal] = useState(false);
  const [showAccountInfoModal, setShowAccountInfoModal] = useState(false);
  const [accountInfo, setAccountInfo] = useState(null);
  const [accountFormData, setAccountFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [documentTitle, setDocumentTitle] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  const [fileStatuses, setFileStatuses] = useState({});
  const [currentStep, setCurrentStep] = useState('');
  const [documentType, setDocumentType] = useState(null); // 문서 타입 (table/text)
  const [showProcessBar, setShowProcessBar] = useState(false); // 프로세스 바 표시 여부
  const [isUploadCompleted, setIsUploadCompleted] = useState(false); // 업로드 완료 상태
  const [batchProgress, setBatchProgress] = useState({
    totalFiles: 0,
    currentFileIndex: 0,
    successCount: 0,
    failCount: 0,
    currentFileName: '',
    failedFiles: []
  });

  // 문서 목록 불러오기
  const fetchDocuments = async () => {
    try {
      const documents = await getDocuments();
      // 문서 데이터를 표시용 형식으로 변환
      const formattedDocs = documents.map(doc => ({
        id: doc.doc_id,
        name: doc.doc_title || doc.file_path?.split('/').pop() || 'Untitled',
        size: doc.file_size ? `${(doc.file_size / 1024 / 1024).toFixed(2)}MB` : 'N/A',
        uploadDate: new Date(doc.upload_date || doc.created_at).toLocaleDateString('ko-KR')
      }));
      setUploadedFiles(formattedDocs);
    } catch (error) {
      console.error('문서 목록 조회 실패:', error);
    }
  };

  // 컴포넌트 마운트 시 데이터 불러오기
  useEffect(() => {
    fetchEmployees();
    fetchDocuments();
  }, []);

  const fetchEmployees = async () => {
    try {
      const employeeInfoData = await getEmployeeInfo();
      console.log('직원 정보 데이터:', employeeInfoData); // 디버깅용
      
      // 관리자는 모든 정보를 볼 수 있으므로 필터 제거
      const formattedEmployees = employeeInfoData
        .map(emp => ({
          id: emp.employee_info_id,
          name: emp.name,
          position: emp.position || '-',
          branch_name: emp.branch_name || '-',
          headquarters: emp.headquarters || '-',
          department: emp.department || '-',
          hasAccount: emp.employee_id ? '✓' : '✗',  // 계정 유무
          // 상세 정보도 저장
          employee_number: emp.employee_number || '-',
          contact_number: emp.contact_number || '-',
          base_salary: emp.base_salary || 0,
          incentive_pay: emp.incentive_pay || 0,
          latest_evaluation: emp.latest_evaluation || '-',
          responsibilities: emp.responsibilities || '-',
          approval_status: emp.approval_status,
          created_at: emp.created_at
        }));
      setEmployees(formattedEmployees);
    } catch (error) {
      console.error('직원 정보 조회 실패:', error);
      setMessage('직원 정보를 불러오는데 실패했습니다.');
    }
  };

  // 계정 생성 핸들러
  const handleCreateAccount = async () => {
    if (!accountFormData.email || !accountFormData.password) {
      setMessage('❌ 모든 필드를 입력해주세요.');
      return;
    }

    if (accountFormData.password !== accountFormData.confirmPassword) {
      setMessage('❌ 비밀번호가 일치하지 않습니다.');
      return;
    }

    if (accountFormData.password.length < 8) {
      setMessage('❌ 비밀번호는 8자 이상이어야 합니다.');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const employeeData = {
        name: selectedEmployee.name,
        email: accountFormData.email,
        password: accountFormData.password,
        role: 'user'
      };

      await registerEmployee(employeeData);
      
      // 폼 초기화
      setAccountFormData({ email: '', password: '', confirmPassword: '' });
      setShowAccountCreateModal(false);
      
      // 직원 리스트 새로고침
      await fetchEmployees();
      
      setMessage('✅ 계정이 성공적으로 생성되었습니다.');
    } catch (error) {
      console.error('계정 생성 실패:', error);
      setMessage(`❌ 계정 생성에 실패했습니다: ${error.message || '알 수 없는 오류'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 계정 정보 조회 핸들러
  const handleViewAccountInfo = async () => {
    setIsLoading(true);
    try {
      const accounts = await getEmployees();
      const account = accounts.find(acc => 
        acc.name === selectedEmployee.name || 
        acc.employee_id === selectedEmployee.employee_id
      );
      
      if (account) {
        setAccountInfo(account);
        setShowAccountInfoModal(true);
      } else {
        setMessage('❌ 계정 정보를 찾을 수 없습니다.');
      }
    } catch (error) {
      console.error('계정 정보 조회 실패:', error);
      setMessage('❌ 계정 정보 조회에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
    setMessage('');
    
    // 파일 선택 피드백 - 성공 메시지로 처리
    if (files.length > 0) {
      const fileNames = files.map(file => file.name).join(', ');
      setMessage(`✅ ${files.length}개의 파일이 선택되었습니다: ${fileNames}`);
    }
  };
  
  // 프로세스 바 확인 버튼 핸들러
  const handleConfirmUpload = () => {
    setShowProcessBar(false);
    setIsUploadCompleted(false);
    setCurrentStep('');
    setDocumentType(null);
    setBatchProgress({
      totalFiles: 0,
      currentFileIndex: 0,
      successCount: 0,
      failCount: 0,
      currentFileName: '',
      failedFiles: []
    });
    setSelectedFiles([]);
    setDocumentTitle('');
    setFileStatuses({});
    // 파일 선택 input 초기화
    const fileInput = document.getElementById('file-upload');
    if (fileInput) {
      fileInput.value = '';
    }
    // 문서 목록 새로고침
    fetchDocuments();
  };

  const handleEmployeeClick = (employee) => {
    setSelectedEmployee(employee);
    setShowEmployeeModal(true);
  };

  const closeEmployeeModal = () => {
    setShowEmployeeModal(false);
    setSelectedEmployee(null);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setMessage('❌ 업로드할 파일을 선택해주세요.');
      return;
    }
    
    // 문서 제목이 없으면 파일명 사용
    const docTitle = documentTitle.trim() || selectedFiles[0]?.name.replace(/\.[^/.]+$/, '') || '제목 없음';
    
    setIsLoading(true);
    setMessage('');
    setUploadProgress({});
    setFileStatuses({});
    setCurrentStep('');
    setDocumentType(null);
    setShowProcessBar(true);
    setIsUploadCompleted(false);
    
    try {
      // SSE 방식으로만 업로드
      if (selectedFiles.length === 1) {
          // 단일 파일 SSE 업로드
          const file = selectedFiles[0];
          setFileStatuses({ [file.name]: 'processing' });
          
          await uploadDocumentWithSSE(file, docTitle, (data) => {
            console.log('진행 상황 업데이트:', data);
            setCurrentStep(data.step);
            
            // 문서 타입 감지
            if (data.docType) {
              setDocumentType(data.docType);
            }
            
            // 진행 단계별 처리
            switch(data.step) {
              case 'completed':
                setFileStatuses({ [file.name]: 'completed' });
                setIsUploadCompleted(true);
                setIsLoading(false);
                break;
              case 'error':
                setFileStatuses({ [file.name]: 'error' });
                setMessage(`❌ ${data.message}`);
                setShowProcessBar(false);
                setIsLoading(false);
                break;
              default:
                setFileStatuses({ [file.name]: 'processing' });
                break;
            }
          });
        } else {
          // 배치 SSE 업로드
          setBatchProgress({
            totalFiles: selectedFiles.length,
            currentFileIndex: 0,
            successCount: 0,
            failCount: 0,
            currentFileName: '',
            failedFiles: []
          });
          
          await uploadDocumentsBatchWithSSE(selectedFiles, docTitle, (data) => {
            console.log('배치 업로드 이벤트:', data.step, data);
            setCurrentStep(data.step);
            
            // 문서 타입 감지
            if (data.docType) {
              setDocumentType(data.docType);
            }
            
            // 배치 시작 시 total 설정
            if (data.step === 'batch_start' && data.total) {
              console.log('배치 시작 - 총 파일 수:', data.total);
              setBatchProgress(prev => {
                const newProgress = {
                  ...prev,
                  totalFiles: data.total
                };
                console.log('배치 진행 상태 업데이트 (batch_start):', newProgress);
                return newProgress;
              });
            }
            
            // progress 정보가 있을 때 항상 업데이트
            if (data.progress) {
              console.log('Progress 정보 수신:', data.progress);
              setBatchProgress(prev => {
                const newProgress = {
                  ...prev,
                  currentFileIndex: data.progress.current || prev.currentFileIndex,
                  successCount: data.progress.successful || 0,
                  failCount: data.progress.failed || 0
                };
                console.log('배치 진행 상태 업데이트:', newProgress);
                return newProgress;
              });
            }
            
            // 파일별 상태 업데이트
            if (data.fileName) {
              setBatchProgress(prev => ({
                ...prev,
                currentFileName: data.fileName
              }));
              
              switch(data.step) {
                case 'file_start':
                  setFileStatuses(prev => ({ ...prev, [data.fileName]: 'processing' }));
                  // file_start 시에도 progress 업데이트
                  if (data.progress) {
                    setBatchProgress(prev => ({
                      ...prev,
                      currentFileIndex: data.progress.current
                    }));
                  }
                  break;
                case 'file_completed':
                  setFileStatuses(prev => ({ ...prev, [data.fileName]: 'completed' }));
                  // file_completed 시에도 progress 업데이트 필수
                  if (data.progress) {
                    console.log('file_completed progress:', data.progress);
                    setBatchProgress(prev => {
                      const newProgress = {
                        ...prev,
                        currentFileIndex: data.progress.current,
                        successCount: data.progress.successful,
                        failCount: data.progress.failed || 0
                      };
                      console.log('file_completed 후 상태:', newProgress);
                      return newProgress;
                    });
                  }
                  break;
                case 'file_error':
                  setFileStatuses(prev => ({ ...prev, [data.fileName]: 'error' }));
                  setBatchProgress(prev => ({
                    ...prev,
                    failedFiles: [...prev.failedFiles, data.fileIndex]
                  }));
                  if (data.progress) {
                    setBatchProgress(prev => ({
                      ...prev,
                      currentFileIndex: data.progress.current,
                      successCount: data.progress.successful || 0,
                      failCount: data.progress.failed
                    }));
                  }
                  break;
                default:
                  break;
              }
            }
            
            if (data.step === 'batch_completed') {
              setIsUploadCompleted(true);
              setIsLoading(false);
            }
          });
      }
      
    } catch (error) {
      console.error('문서 업로드 실패:', error);
      let errorMessage = '문서 업로드에 실패했습니다.';
      
      // 다양한 오류 형태 처리
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error && typeof error === 'object') {
        if (error.response && error.response.data) {
          if (typeof error.response.data === 'string') {
            errorMessage = error.response.data;
          } else if (error.response.data.detail) {
            errorMessage = error.response.data.detail;
          } else if (error.response.data.message) {
            errorMessage = error.response.data.message;
          } else if (error.response.data.error) {
            errorMessage = error.response.data.error;
          }
        } else if (error.message) {
          errorMessage = error.message;
        } else if (error.detail) {
          errorMessage = error.detail;
        } else if (error.error) {
          errorMessage = error.error;
        }
      }
      
      setMessage(`❌ ${errorMessage}`);
      setShowProcessBar(false);
    } finally {
      setIsLoading(false);
    }
  };

  const renderEmployeeManagement = () => (
    <div className="employee-management">
      <h2>직원 관리</h2>
      
      {/* 메시지 표시 */}
      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {typeof message === 'string' ? message : '오류가 발생했습니다.'}
        </div>
      )}
      
      {/* 직원 리스트 */}
      <div className="employee-list">
        <h3>직원 정보 리스트</h3>
        <div className="employee-table">
          <table>
            <thead>
              <tr>
                <th>이름</th>
                <th>직급</th>
                <th>지점명</th>
                <th>본부</th>
                <th>부서</th>
                <th>계정유무</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee) => (
                <tr key={employee.id} onClick={() => handleEmployeeClick(employee)} style={{ cursor: 'pointer' }}>
                  <td>{employee.name}</td>
                  <td>{employee.position}</td>
                  <td>{employee.branch_name}</td>
                  <td>{employee.headquarters}</td>
                  <td>{employee.department}</td>
                  <td style={{ textAlign: 'center', fontWeight: 'bold', color: employee.hasAccount === '✓' ? 'green' : 'red' }}>
                    {employee.hasAccount}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 직원 상세 정보 모달 */}
      {showEmployeeModal && selectedEmployee && (
        <div className="modal-overlay" onClick={closeEmployeeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>직원 상세 정보</h2>
              <button className="modal-close" onClick={closeEmployeeModal}>✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h3>기본 정보</h3>
                <div className="detail-row">
                  <span className="detail-label">이름:</span>
                  <span className="detail-value">{selectedEmployee.name}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">사번:</span>
                  <span className="detail-value">{selectedEmployee.employee_number}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">직급:</span>
                  <span className="detail-value">{selectedEmployee.position}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">연락처:</span>
                  <span className="detail-value">{selectedEmployee.contact_number}</span>
                </div>
              </div>

              <div className="detail-section">
                <h3>조직 정보</h3>
                <div className="detail-row">
                  <span className="detail-label">지점:</span>
                  <span className="detail-value">{selectedEmployee.branch_name}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">본부:</span>
                  <span className="detail-value">{selectedEmployee.headquarters}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">부서:</span>
                  <span className="detail-value">{selectedEmployee.department}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">담당업무:</span>
                  <span className="detail-value">{selectedEmployee.responsibilities}</span>
                </div>
              </div>

              <div className="detail-section">
                <h3>급여 및 평가</h3>
                <div className="detail-row">
                  <span className="detail-label">기본급:</span>
                  <span className="detail-value">
                    {selectedEmployee.base_salary ? 
                      `₩${selectedEmployee.base_salary.toLocaleString()}` : '-'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">인센티브:</span>
                  <span className="detail-value">
                    {selectedEmployee.incentive_pay ? 
                      `₩${selectedEmployee.incentive_pay.toLocaleString()}` : '-'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">최근 평가:</span>
                  <span className="detail-value">{selectedEmployee.latest_evaluation}</span>
                </div>
              </div>

              <div className="detail-section">
                <h3>계정 상태</h3>
                <div className="detail-row">
                  <span className="detail-label">계정 유무:</span>
                  <span className="detail-value" style={{ 
                    fontWeight: 'bold', 
                    color: selectedEmployee.hasAccount === '✓' ? 'green' : 'red' 
                  }}>
                    {selectedEmployee.hasAccount === '✓' ? '계정 있음' : '계정 없음'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">승인 상태:</span>
                  <span className="detail-value">
                    {selectedEmployee.approval_status === 'approved' ? '승인됨' : 
                     selectedEmployee.approval_status === 'pending' ? '대기중' : '거부됨'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">등록일:</span>
                  <span className="detail-value">
                    {new Date(selectedEmployee.created_at).toLocaleDateString('ko-KR')}
                  </span>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              {selectedEmployee.hasAccount === '✓' ? (
                <button className="btn-account-info" onClick={handleViewAccountInfo}>
                  계정 정보 조회
                </button>
              ) : (
                <button className="btn-create-account" onClick={() => {
                  setAccountFormData({
                    email: '',
                    password: '',
                    confirmPassword: ''
                  });
                  setShowAccountCreateModal(true);
                }}>
                  계정 생성
                </button>
              )}
              <button className="btn-close" onClick={closeEmployeeModal}>닫기</button>
            </div>
          </div>
        </div>
      )}

      {/* 계정 생성 모달 */}
      {showAccountCreateModal && (
        <div className="modal-overlay" onClick={() => setShowAccountCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>계정 생성</h2>
              <button className="modal-close" onClick={() => setShowAccountCreateModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h3>직원 정보</h3>
                <div className="detail-row">
                  <span className="detail-label">이름:</span>
                  <span className="detail-value">{selectedEmployee?.name}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">사번:</span>
                  <span className="detail-value">{selectedEmployee?.employee_number}</span>
                </div>
              </div>
              
              <div className="detail-section">
                <h3>계정 정보 입력</h3>
                <div className="form-group">
                  <label>이메일</label>
                  <input
                    type="email"
                    placeholder="example@company.com"
                    value={accountFormData.email}
                    onChange={(e) => setAccountFormData({...accountFormData, email: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>비밀번호 (8자 이상)</label>
                  <input
                    type="password"
                    placeholder="비밀번호 입력"
                    value={accountFormData.password}
                    onChange={(e) => setAccountFormData({...accountFormData, password: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>비밀번호 확인</label>
                  <input
                    type="password"
                    placeholder="비밀번호 재입력"
                    value={accountFormData.confirmPassword}
                    onChange={(e) => setAccountFormData({...accountFormData, confirmPassword: e.target.value})}
                  />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-primary" 
                onClick={handleCreateAccount}
                disabled={isLoading}
              >
                {isLoading ? '생성 중...' : '계정 생성'}
              </button>
              <button className="btn-close" onClick={() => setShowAccountCreateModal(false)}>취소</button>
            </div>
          </div>
        </div>
      )}

      {/* 계정 정보 조회 모달 */}
      {showAccountInfoModal && accountInfo && (
        <div className="modal-overlay" onClick={() => setShowAccountInfoModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>계정 정보</h2>
              <button className="modal-close" onClick={() => setShowAccountInfoModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h3>계정 상세 정보</h3>
                <div className="detail-row">
                  <span className="detail-label">이메일:</span>
                  <span className="detail-value">{accountInfo.email}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">역할:</span>
                  <span className="detail-value">
                    {accountInfo.role === 'admin' ? '관리자' : '일반 사용자'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">계정 상태:</span>
                  <span className="detail-value" style={{
                    color: accountInfo.is_active ? 'green' : 'red',
                    fontWeight: 'bold'
                  }}>
                    {accountInfo.is_active ? '활성' : '비활성'}
                  </span>
                </div>
                {accountInfo.created_at && (
                  <div className="detail-row">
                    <span className="detail-label">계정 생성일:</span>
                    <span className="detail-value">
                      {new Date(accountInfo.created_at).toLocaleDateString('ko-KR')}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-close" onClick={() => setShowAccountInfoModal(false)}>닫기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderDocumentManagement = () => (
    <div className="document-management">
      <h2>문서 관리</h2>
      
      {/* 메시지 표시 */}
      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {typeof message === 'string' ? message : '오류가 발생했습니다.'}
        </div>
      )}
      
      {/* 문서 업로드 */}
      <div className="document-upload">
        <h3>문서 업로드</h3>
        <div className="upload-area">
          <div className="upload-form">
            <input
              type="text"
              placeholder="문서 제목을 입력하세요"
              value={documentTitle}
              onChange={(e) => setDocumentTitle(e.target.value)}
              className="document-title-input"
              disabled={isLoading}
            />
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.xlsx,.xls,.csv"
              onChange={handleFileSelect}
              id="file-upload"
              style={{ display: 'none' }}
              disabled={isLoading}
            />
            <label htmlFor="file-upload" className={`upload-btn ${isLoading ? 'disabled' : ''}`}>
              {isLoading ? '업로드 중...' : '📁 파일 선택하여 업로드'}
            </label>
            <button 
              onClick={handleUpload} 
              className="upload-btn"
              disabled={isLoading || selectedFiles.length === 0}
            >
              {isLoading ? '업로드 중...' : '파일 업로드'}
            </button>
          </div>
          <p className="upload-hint">PDF, DOC, DOCX, TXT, XLSX, XLS, CSV 파일만 업로드 가능합니다. (최대 10MB)</p>
          
          {/* 선택된 파일 목록 */}
          {selectedFiles.length > 0 && !showProcessBar && (
            <div className="selected-files">
              <h4>선택된 파일 ({selectedFiles.length}개):</h4>
              <ul>
                {selectedFiles.map((file, index) => (
                  <li key={index} className={`file-item ${fileStatuses[file.name] || ''}`}>
                    <span className="file-name">{file.name} ({(file.size / 1024 / 1024).toFixed(2)}MB)</span>
                    {fileStatuses[file.name] && (
                      <span className={`file-status-icon ${fileStatuses[file.name]}`}>
                        {fileStatuses[file.name] === 'processing' && '⏳'}
                        {fileStatuses[file.name] === 'completed' && '✅'}
                        {fileStatuses[file.name] === 'error' && '❌'}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* 새로운 프로세스 바 */}
          {showProcessBar && (
            <>
              {selectedFiles.length === 1 ? (
                // 단일 파일 업로드 프로세스 바
                <ProcessProgressBar
                  currentStep={currentStep}
                  documentType={documentType}
                  fileName={selectedFiles[0]?.name}
                  isCompleted={isUploadCompleted}
                  onConfirm={handleConfirmUpload}
                />
              ) : (
                // 배치 업로드 프로세스 바
                <BatchProcessProgressBar
                  totalFiles={batchProgress.totalFiles}
                  currentFileIndex={batchProgress.currentFileIndex}
                  successCount={batchProgress.successCount}
                  failCount={batchProgress.failCount}
                  currentFileName={batchProgress.currentFileName}
                  currentStep={currentStep}
                  documentType={documentType}
                  isCompleted={isUploadCompleted}
                  onConfirm={handleConfirmUpload}
                  failedFiles={batchProgress.failedFiles}
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* 업로드된 문서 리스트 */}
      <div className="document-list">
        <h3>업로드된 문서</h3>
        <div className="document-table">
          <table>
            <thead>
              <tr>
                <th>파일명</th>
                <th>크기</th>
                <th>업로드 날짜</th>
              </tr>
            </thead>
            <tbody>
              {uploadedFiles.map((file) => (
                <tr key={file.id}>
                  <td>{file.name}</td>
                  <td>{file.size}</td>
                  <td>{file.uploadDate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>시스템 관리</h1>
        
      </div>

      {/* 탭 네비게이션 */}
      <div className="admin-tabs">
        <button 
          className={`tab-btn ${activeTab === 'employees' ? 'active' : ''}`}
          onClick={() => setActiveTab('employees')}
        >
          👥 직원 관리
        </button>
        <button 
          className={`tab-btn ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          📄 문서 관리
        </button>
      </div>

      {/* 탭 컨텐츠 */}
      <div className="tab-content">
        {activeTab === 'employees' && renderEmployeeManagement()}
        {activeTab === 'documents' && renderDocumentManagement()}
      </div>
    </div>
  );
};

export default Admin; 