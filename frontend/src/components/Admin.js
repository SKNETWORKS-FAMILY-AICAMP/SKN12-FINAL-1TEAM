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
  const [accountCreationMessage, setAccountCreationMessage] = useState(''); // 계정 생성 모달 전용 메시지
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
      
      // documents가 배열인지 확인
      if (!documents || !Array.isArray(documents)) {
        console.warn('문서 목록이 비어있거나 형식이 올바르지 않습니다:', documents);
        setUploadedFiles([]);
        return;
      }
      
      // 빈 배열인 경우
      if (documents.length === 0) {
        console.log('문서가 없습니다');
        setUploadedFiles([]);
        return;
      }
      
      // 문서 데이터를 표시용 형식으로 변환
      const formattedDocs = documents.map(doc => ({
        id: String(doc.doc_id || ''), // doc_id를 문자열로 변환
        name: doc.doc_title || doc.file_path?.split('/').pop() || 'Untitled',
        size: doc.file_size ? `${(doc.file_size / 1024 / 1024).toFixed(2)}MB` : 'N/A',
        uploadDate: doc.upload_date || doc.created_at ? 
          new Date(doc.upload_date || doc.created_at).toLocaleDateString('ko-KR') : 'N/A'
      }));
      setUploadedFiles(formattedDocs);
    } catch (error) {
      console.error('문서 목록 조회 실패:', error);
      console.error('에러 상세:', error.message);
      setUploadedFiles([]); // 오류 시 빈 배열 설정
    }
  };

  // 컴포넌트 마운트 시 데이터 불러오기
  useEffect(() => {
    fetchEmployees();
    fetchDocuments();
  }, []);

  const fetchEmployees = async () => {
    try {
      // 두 API를 병렬로 호출
      const [accountData, employeeInfoData] = await Promise.all([
        getEmployees(),  // /user/employees/all - 계정 정보
        getEmployeeInfo()  // /employee-info - 인사 정보
      ]);
      
      console.log('계정 데이터:', accountData); // 디버깅용
      console.log('인사 정보 데이터:', employeeInfoData); // 디버깅용
      
      // 데이터가 배열인지 확인
      const accounts = Array.isArray(accountData) ? accountData : [];
      const employeeInfos = Array.isArray(employeeInfoData) ? employeeInfoData : [];
      
      // 계정 정보와 인사 정보를 합치기
      const formattedEmployees = employeeInfos.map(info => {
        // 해당 직원의 계정 정보 찾기 - employee_id로만 매칭
        const account = info.employee_id ? 
          accounts.find(acc => acc.employee_id === info.employee_id) : 
          null;
        
        return {
          id: info.employee_info_id || info.id,
          name: info.name,
          email: account?.email || '-',
          position: info.position || '-',
          branch_name: info.branch_name || '-',
          headquarters: info.headquarters || '-',
          department: info.department || '-',
          hasAccount: account ? '✓' : '✗',
          // 상세 정보
          employee_id: info.employee_id,
          employee_number: info.employee_number || '-',
          contact_number: info.contact_number || '-',
          base_salary: info.base_salary || 0,
          incentive_pay: info.incentive_pay || 0,
          latest_evaluation: info.latest_evaluation || '-',
          responsibilities: info.responsibilities || '-',
          approval_status: info.approval_status || 'approved',
          created_at: account?.created_at || info.created_at,
          role: account?.role || 'user',
          is_active: account?.is_active || false
        };
      });
      
      setEmployees(formattedEmployees);
    } catch (error) {
      console.error('직원 정보 조회 실패:', error);
      setMessage('직원 정보를 불러오는데 실패했습니다.');
    }
  };

  // 계정 생성 핸들러
  const handleCreateAccount = async () => {
    // 입력값 검증
    if (!accountFormData.email || !accountFormData.password) {
      setAccountCreationMessage('❌ 모든 필드를 입력해주세요.');
      return;
    }

    if (accountFormData.password !== accountFormData.confirmPassword) {
      setAccountCreationMessage('❌ 비밀번호가 일치하지 않습니다.');
      return;
    }

    if (accountFormData.password.length < 8) {
      setAccountCreationMessage('❌ 비밀번호는 8자 이상이어야 합니다.');
      return;
    }

    setIsLoading(true);
    setAccountCreationMessage('');

    try {
      const employeeData = {
        name: selectedEmployee.name,
        employee_number: selectedEmployee.employee_number,
        email: accountFormData.email,
        password: accountFormData.password,
        role: 'user'
      };

      await registerEmployee(employeeData);
      
      // 성공 시에만 모달 닫기
      setAccountCreationMessage('✅ 계정이 성공적으로 생성되었습니다.');
      
      // 직원 리스트 새로고침
      await fetchEmployees();
      
      // 업데이트된 직원 정보로 selectedEmployee 갱신
      const updatedEmployees = await getEmployeeInfo();
      const updatedEmployee = updatedEmployees.find(emp => 
        emp.employee_info_id === selectedEmployee.id
      );
      
      if (updatedEmployee) {
        // 계정 정보를 포함한 업데이트된 직원 정보 설정
        const accounts = await getEmployees();
        const account = updatedEmployee.employee_id ? 
          accounts.find(acc => acc.employee_id === updatedEmployee.employee_id) : 
          null;
          
        setSelectedEmployee({
          ...selectedEmployee,
          ...updatedEmployee,
          hasAccount: account ? '✓' : '✗',
          email: account?.email || '-',
          role: account?.role || 'user',
          is_active: account?.is_active || false
        });
      }
      
      // 2초 후 모달 닫기
      setTimeout(() => {
        setAccountFormData({ email: '', password: '', confirmPassword: '' });
        setShowAccountCreateModal(false);
        setAccountCreationMessage('');
        setMessage('✅ 계정이 성공적으로 생성되었습니다.');
        // 배경 스크롤 복원
        document.body.style.overflow = 'unset';
      }, 2000);
      
    } catch (error) {
      console.error('계정 생성 실패:', error);
      // 오류 메시지를 모달에 표시
      let errorMessage = '계정 생성에 실패했습니다';
      
      if (error.response && error.response.data) {
        errorMessage = error.response.data.detail || error.response.data.message || errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setAccountCreationMessage(`❌ ${errorMessage}`);
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
        // 배경 스크롤 방지
        document.body.style.overflow = 'hidden';
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
  
  // 목표 데이터 전용 업로드 핸들러
  const handleTargetDataUpload = async () => {
    if (selectedFiles.length === 0) {
      setMessage('❌ 목표 데이터 파일을 선택해주세요.');
      return;
    }
    
    const file = selectedFiles[0];
    const docTitle = documentTitle.trim() || `목표 데이터 - ${file.name.replace(/\.[^/.]+$/, '')}`;
    
    setIsLoading(true);
    setMessage('⏳ 목표 데이터 업로드 중...');
    
    try {
      // 목표 데이터 전용 API 엔드포인트 사용
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_title', docTitle);
      formData.append('uploader_id', currentUser?.employee_id || '1'); // 현재 사용자 ID
      
      // /documents/upload/employee-targets 엔드포인트 호출 (Database 백엔드 8010 포트)
      const token = localStorage.getItem('access_token') || localStorage.getItem('narutalk_token');
      const response = await fetch('http://localhost:8010/documents/upload/employee-targets', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const result = await response.json();
      
      if (response.ok && result.success) {
        setMessage(
          `✅ ${result.message}\n` +
          `  • 생성: ${result.created_count}건\n` +
          `  • 업데이트: ${result.updated_count}건\n` +
          `  • 건너뜀: ${result.skipped_count}건`
        );
        
        // 오류 상세 표시 (있는 경우)
        if (result.error_details && result.error_details.length > 0) {
          console.warn('목표 데이터 처리 중 일부 오류:', result.error_details);
        }
        
        // 파일 input 초기화
        const fileInput = document.getElementById('file-upload');
        if (fileInput) fileInput.value = '';
        setSelectedFiles([]);
        setDocumentTitle('');
        
        // 문서 목록 새로고침
        fetchDocuments();
      } else {
        throw new Error(result.message || result.detail || '업로드 실패');
      }
    } catch (error) {
      console.error('목표 데이터 업로드 실패:', error);
      setMessage(`❌ 목표 데이터 업로드 실패: ${error.message}`);
    } finally {
      setIsLoading(false);
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
    // 배경 스크롤 방지
    document.body.style.overflow = 'hidden';
  };

  const closeEmployeeModal = () => {
    setShowEmployeeModal(false);
    setSelectedEmployee(null);
    // 배경 스크롤 복원
    document.body.style.overflow = 'unset';
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
        <div className="admin-modal-overlay" onClick={closeEmployeeModal}>
          <div className="admin-modal-content" onClic아k={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h2>직원 상세 정보</h2>
              <button className="admin-modal-close" onClick={closeEmployeeModal}>✕</button>
            </div>
            <div className="admin-modal-body">
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
            <div className="admin-modal-footer">
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
                  setAccountCreationMessage(''); // 메시지 초기화
                  setShowAccountCreateModal(true);
                  // 배경 스크롤 방지
                  document.body.style.overflow = 'hidden';
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
        <div className="admin-modal-overlay" onClick={() => {
          setShowAccountCreateModal(false);
          setAccountCreationMessage('');
          // 배경 스크롤 복원
          document.body.style.overflow = 'unset';
        }}>
          <div className="admin-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h2>계정 생성</h2>
              <button className="admin-modal-close" onClick={() => {
                setShowAccountCreateModal(false);
                setAccountCreationMessage('');
                // 배경 스크롤 복원
                document.body.style.overflow = 'unset';
              }}>✕</button>
            </div>
            <div className="admin-modal-body">
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
              
              {/* 메시지 표시 영역 - 하단에 위치 */}
              {accountCreationMessage && (
                <div className={`message ${accountCreationMessage.includes('✅') ? 'success' : 'error'}`} style={{ marginTop: '15px', marginBottom: '0' }}>
                  {accountCreationMessage}
                </div>
              )}
            </div>
            <div className="admin-modal-footer">
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
        <div className="admin-modal-overlay" onClick={() => {
          setShowAccountInfoModal(false);
          // 배경 스크롤 복원
          document.body.style.overflow = 'unset';
        }}>
          <div className="admin-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h2>계정 정보</h2>
              <button className="admin-modal-close" onClick={() => {
                setShowAccountInfoModal(false);
                // 배경 스크롤 복원
                document.body.style.overflow = 'unset';
              }}>✕</button>
            </div>
            <div className="admin-modal-body">
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
            <div className="admin-modal-footer">
              <button className="btn-close" onClick={() => {
                setShowAccountInfoModal(false);
                // 배경 스크롤 복원
                document.body.style.overflow = 'unset';
              }}>닫기</button>
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
              {isLoading ? '업로드 중...' : '📁 파일 선택'}
            </label>
            <button 
              onClick={handleUpload} 
              className="upload-btn"
              disabled={isLoading || selectedFiles.length === 0}
            >
              {isLoading ? '업로드 중...' : '일반 문서 업로드'}
            </button>
            
            {/* 목표 데이터 업로드 버튼 - 같은 파일 선택 사용 */}
            <button 
              onClick={handleTargetDataUpload} 
              className="upload-btn"
              style={{ backgroundColor: '#28a745' }}
              disabled={isLoading || selectedFiles.length === 0}
            >
              {isLoading ? '업로드 중...' : '📊 목표 데이터 업로드'}
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