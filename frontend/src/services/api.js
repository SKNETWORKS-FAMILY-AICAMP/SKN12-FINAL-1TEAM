const API_BASE_URL = '';

// API 요청을 위한 기본 설정
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('narutalk_token');
  
  console.log('🌐 API 요청:', {
    url: url,
    method: options.method || 'GET',
    headers: options.headers,
    body: options.body
  });
  
  // FormData인지 확인
  const isFormData = options.body instanceof FormData;
  
  const defaultOptions = {
    headers: {
      // FormData가 아닐 때만 Content-Type 설정
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
  };

  const config = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  try {
    console.log('📤 실제 요청 설정:', config);
    const response = await fetch(url, config);
    console.log('📥 응답 상태:', response.status, response.statusText);
    
    const data = await response.json();
    console.log('📥 응답 데이터:', data);

    if (!response.ok) {
      throw new Error(data.detail || 'Request failed');
    }

    return data;
  } catch (error) {
    console.error('❌ API request failed:', error);
    throw error;
  }
};

// 사용자 로그인
export const loginUser = async (credentials) => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  return await apiRequest('/user/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });
};

// 토큰 검증
export const verifyToken = async () => {
  return await apiRequest('/user/me', {
    method: 'GET',
  });
};

// 로그아웃 (토큰 제거)
export const logoutUser = () => {
  localStorage.removeItem('narutalk_token');
  localStorage.removeItem('narutalk_user');
  localStorage.removeItem('narutalk_isLoggedIn');
};

// 직원 등록 (관리자 전용)
export const registerEmployee = async (employeeData) => {
  return await apiRequest('/admin/register-employee', {
    method: 'POST',
    body: JSON.stringify({
      email: employeeData.email,
      username: employeeData.username,
      password: employeeData.password,
      name: employeeData.name,
      role: employeeData.role || 'user'
    }),
  });
};

// 직원 리스트 조회
export const getEmployees = async () => {
  return await apiRequest('/user/employees/all', {
    method: 'GET',
  });
};

// 문서 업로드
export const uploadDocument = async (file, docTitle) => {
  // 현재 사용자 정보 가져오기
  const currentUser = await verifyToken();
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_title', docTitle);
  formData.append('uploader_id', currentUser.employee_id);
  // version 파라미터는 백엔드에서 선택사항이므로 제거
  
  return await apiRequest('/documents/upload', {
    method: 'POST',
    body: formData,
  });
};

// 문서 목록 조회
export const getDocuments = async () => {
  return await apiRequest('/documents/', {
    method: 'GET',
  });
};

// 문서 상세 조회
export const getDocumentDetail = async (docId) => {
  return await apiRequest(`/documents/${docId}`, {
    method: 'GET',
  });
};

// 문서 내용 조회
export const getDocumentContent = async (docId) => {
  return await apiRequest(`/documents/${docId}/content`, {
    method: 'GET',
  });
};

// Employee Performance API 함수들

// 직원 실적 목록 조회
export const getEmployeeList = async () => {
  return await apiRequest('/api/employee/list', {
    method: 'GET',
  });
};

// 직원 실적 조회
export const getEmployeePerformance = async (employeeName, startPeriod, endPeriod) => {
  const requestBody = {};
  
  // 날짜 형식 판단 (YYYY-MM-DD 또는 YYYYMM)
  if (startPeriod && startPeriod.includes('-')) {
    // YYYY-MM-DD 형식
    requestBody.start_date = startPeriod;
    requestBody.end_date = endPeriod;
  } else {
    // YYYYMM 형식
    requestBody.start_period = startPeriod;
    requestBody.end_period = endPeriod;
  }
  
  // 관리자가 특정 직원을 조회하는 경우에만 employee_name 추가
  if (employeeName) {
    requestBody.employee_name = employeeName;
  }
  
  return await apiRequest('/api/employee/performance', {
    method: 'POST',
    body: JSON.stringify(requestBody),
  });
};

// 직원 목표 대비 실적 조회
export const getEmployeeTarget = async (employeeName, startPeriod, endPeriod) => {
  const requestBody = {};
  
  // 날짜 형식 판단
  if (startPeriod && startPeriod.includes('-')) {
    requestBody.start_date = startPeriod;
    requestBody.end_date = endPeriod;
  } else {
    requestBody.start_period = startPeriod;
    requestBody.end_period = endPeriod;
  }
  
  if (employeeName) {
    requestBody.employee_name = employeeName;
  }
  
  return await apiRequest('/api/employee/target', {
    method: 'POST',
    body: JSON.stringify(requestBody),
  });
};

// 직원 실적 자연어 분석
export const analyzeEmployeePerformance = async (params) => {
  const requestBody = {};
  
  if (params.query) requestBody.query = params.query;
  if (params.start_date) requestBody.start_date = params.start_date;
  if (params.end_date) requestBody.end_date = params.end_date;
  if (params.start_period) requestBody.start_period = params.start_period;
  if (params.end_period) requestBody.end_period = params.end_period;
  if (params.employee_name) requestBody.employee_name = params.employee_name;
  
  return await apiRequest('/api/employee/analyze', {
    method: 'POST',
    body: JSON.stringify(requestBody),
  });
}; 