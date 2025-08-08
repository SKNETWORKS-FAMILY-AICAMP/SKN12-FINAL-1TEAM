const API_BASE_URL = 'http://localhost:8000';

// API 요청을 위한 기본 설정
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('narutalk_token');
  
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
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      // 오류 메시지를 문자열로 변환
      let errorMessage = '요청에 실패했습니다.';
      
      if (data.detail) {
        errorMessage = data.detail;
      } else if (data.message) {
        errorMessage = data.message;
      } else if (typeof data === 'string') {
        errorMessage = data;
      } else if (data.error) {
        errorMessage = data.error;
      } else if (Array.isArray(data)) {
        // 배열인 경우 각 요소를 문자열로 변환
        errorMessage = data.map(item => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object') {
            return item.message || item.detail || item.error || JSON.stringify(item);
          }
          return String(item);
        }).join(', ');
      } else if (data && typeof data === 'object') {
        // 객체인 경우 JSON.stringify 사용
        errorMessage = JSON.stringify(data);
      }
      
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error('API request failed:', error);
    
    // 이미 Error 객체인 경우 그대로 던지기
    if (error instanceof Error) {
      throw error;
    }
    
    // 객체인 경우 문자열로 변환
    if (typeof error === 'object' && error !== null) {
      if (Array.isArray(error)) {
        const errorMessage = error.map(item => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object') {
            return item.message || item.detail || item.error || JSON.stringify(item);
          }
          return String(item);
        }).join(', ');
        throw new Error(errorMessage);
      }
      
      const errorMessage = error.message || error.detail || error.error || JSON.stringify(error);
      throw new Error(errorMessage);
    }
    
    // 문자열인 경우 그대로 던지기
    if (typeof error === 'string') {
      throw new Error(error);
    }
    
    // 기타 경우
    throw new Error('알 수 없는 오류가 발생했습니다.');
  }
};

// 사용자 로그인
export const loginUser = async (credentials) => {
  // Mock 로그인 모드 (개발용)
  if (process.env.REACT_APP_MOCK_LOGIN === 'true') {
    console.log('🔓 Mock API: loginUser 호출');
    return Promise.resolve({
      access_token: 'mock-jwt-token-' + Date.now(),
      token_type: 'bearer'
    });
  }

  // 실제 API 호출
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
  // Mock 로그인 모드 (개발용)
  if (process.env.REACT_APP_MOCK_LOGIN === 'true') {
    console.log('🔓 Mock API: verifyToken 호출');
    
    // LocalStorage에서 사용자 정보 가져오기
    const userData = localStorage.getItem('narutalk_user');
    if (userData) {
      return Promise.resolve(JSON.parse(userData));
    }
    
    // 기본 Mock 사용자 정보 반환
    return Promise.resolve({
      employee_id: 1,
      email: 'test@example.com',
      username: 'testuser',
      name: '테스트 사용자',
      role: 'user',
      is_active: true,
      created_at: new Date().toISOString()
    });
  }

  // 실제 API 호출
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