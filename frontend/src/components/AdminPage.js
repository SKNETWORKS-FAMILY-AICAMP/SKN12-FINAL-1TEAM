import React, { useState, useEffect } from 'react';
import { registerEmployee, getEmployees, uploadDocument } from '../services/api';
import './AdminPage.css';

const AdminPage = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState('employees');
  const [employees, setEmployees] = useState([]);
  const [newEmployee, setNewEmployee] = useState({ 
    name: '', 
    email: '', 
    username: '',
    password: '',
    team: '',
    role: 'user'
  });
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [documentTitle, setDocumentTitle] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);

  // 컴포넌트 마운트 시 직원 리스트 가져오기
  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const employeesData = await getEmployees();
      const formattedEmployees = employeesData
        .filter(emp => emp.role !== 'admin' && emp.is_active) // 관리자 제외, 활성 직원만
        .map(emp => ({
          id: emp.employee_id,
          name: emp.name,
          email: emp.email,
          username: emp.username,
          team: emp.role === 'manager' ? '매니저' : '영업부'
        }));
      setEmployees(formattedEmployees);
    } catch (error) {
      console.error('직원 리스트 조회 실패:', error);
      setMessage('직원 리스트를 불러오는데 실패했습니다.');
    }
  };

  const handleAddEmployee = async () => {
    if (!newEmployee.name || !newEmployee.email || !newEmployee.username || !newEmployee.password || !newEmployee.team) {
      setMessage('모든 필드를 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const employeeData = {
        name: newEmployee.name,
        email: newEmployee.email,
        username: newEmployee.username,
        password: newEmployee.password,
        role: newEmployee.role
      };

      const response = await registerEmployee(employeeData);
      
      // 폼 초기화
      setNewEmployee({ 
        name: '', 
        email: '', 
        username: '',
        password: '',
        team: '',
        role: 'user'
      });
      
      // 직원 리스트 새로고침
      await fetchEmployees();
      
      setMessage('직원이 성공적으로 등록되었습니다!');
    } catch (error) {
      console.error('직원 등록 실패:', error);
      setMessage(error.message || '직원 등록에 실패했습니다.');
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

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setMessage('❌ 업로드할 파일을 선택해주세요.');
      return;
    }
    
    if (!documentTitle.trim()) {
      setMessage('❌ 문서 제목을 입력해주세요.');
      return;
    }
    
    setIsLoading(true);
    setMessage('');
    
    try {
      // 각 파일을 개별적으로 업로드
      for (const file of selectedFiles) {
        await uploadDocument(file, documentTitle);
      }
      
      // 성공 메시지
      setMessage(`✅ ${selectedFiles.length}개의 문서가 성공적으로 업로드되었습니다!`);
      
      // 폼 초기화
      setDocumentTitle('');
      setSelectedFiles([]);
      
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
      
      {/* 직원 등록 */}
      <div className="employee-registration">
        <h3>새 직원 등록</h3>
        <div className="registration-form">
          <input
            type="text"
            placeholder="이름"
            value={newEmployee.name}
            onChange={(e) => setNewEmployee({...newEmployee, name: e.target.value})}
          />
          <input
            type="email"
            placeholder="이메일"
            value={newEmployee.email}
            onChange={(e) => setNewEmployee({...newEmployee, email: e.target.value})}
          />
          <input
            type="text"
            placeholder="아이디"
            value={newEmployee.username}
            onChange={(e) => setNewEmployee({...newEmployee, username: e.target.value})}
          />
          <input
            type="password"
            placeholder="비밀번호 (8자 이상)"
            value={newEmployee.password}
            onChange={(e) => setNewEmployee({...newEmployee, password: e.target.value})}
          />
          <select
            value={newEmployee.team}
            onChange={(e) => setNewEmployee({...newEmployee, team: e.target.value})}
          >
            <option value="">부서 선택</option>
            <option value="영업팀">영업</option>
            <option value="마케팅팀">마케팅</option>
            <option value="개발팀">개발</option>
            <option value="인사팀">인사</option>
          </select>
          <select
            value={newEmployee.role}
            onChange={(e) => setNewEmployee({...newEmployee, role: e.target.value})}
          >
            <option value="user">일반 사용자</option>
            <option value="admin">관리자</option>
          </select>
          <button 
            onClick={handleAddEmployee} 
            className="add-btn"
            disabled={isLoading}
          >
            {isLoading ? '등록 중...' : '직원 추가'}
          </button>
        </div>
      </div>

      {/* 직원 리스트 */}
      <div className="employee-list">
        <h3>직원 리스트</h3>
        <div className="employee-table">
          <table>
            <thead>
              <tr>
                <th>이름</th>
                <th>이메일</th>
                <th>아이디</th>
                <th>부서</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee) => (
                <tr key={employee.id}>
                  <td>{employee.name}</td>
                  <td>{employee.email}</td>
                  <td>{employee.username}</td>
                  <td>{employee.team}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
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
          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <h4>선택된 파일 ({selectedFiles.length}개):</h4>
              <ul>
                {selectedFiles.map((file, index) => (
                  <li key={index}>{file.name} ({(file.size / 1024 / 1024).toFixed(2)}MB)</li>
                ))}
              </ul>
            </div>
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

export default AdminPage; 