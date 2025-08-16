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
      password: employeeData.password,
      name: employeeData.name,
      role: employeeData.role || 'user'
    }),
  });
};

// 직원 리스트 조회 (계정 정보)
export const getEmployees = async () => {
  return await apiRequest('/user/employees/all', {
    method: 'GET',
  });
};

// 직원 정보 리스트 조회 (인사 정보)
export const getEmployeeInfo = async () => {
  return await apiRequest('/employee-info', {
    method: 'GET',
  });
};

// 문서 업로드 (기존 방식)
export const uploadDocument = async (file, docTitle) => {
  // 현재 사용자 정보 가져오기
  const currentUser = await verifyToken();
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_title', docTitle);
  formData.append('uploader_id', String(currentUser.employee_id));
  // version 파라미터는 백엔드에서 선택사항이므로 제거
  
  console.log('📤 Upload request:', {
    doc_title: docTitle,
    uploader_id: currentUser.employee_id,
    file_name: file.name,
    file_size: file.size
  });
  
  return await apiRequest('/documents/upload', {
    method: 'POST',
    body: formData,
  });
};

// SSE 기반 단일 문서 업로드
export const uploadDocumentWithSSE = async (file, docTitle, onProgress) => {
  const currentUser = await verifyToken();
  const token = localStorage.getItem('narutalk_token');
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_title', docTitle || file.name);
  formData.append('uploader_id', String(currentUser.employee_id));
  
  return new Promise((resolve, reject) => {
    // fetch + ReadableStream 사용하여 SSE 처리
    fetch(`/documents/upload-sse`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })
    .then(async response => {
      console.log('SSE 응답 상태:', response.status);
      console.log('SSE 응답 헤더:', response.headers.get('content-type'));
      
      // 에러 상태 코드 확인
      if (!response.ok) {
        console.error('서버 에러:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('에러 내용:', errorText);
        throw new Error(`서버 에러: ${response.status} - ${errorText}`);
      }
      
      // Content-Type 확인
      if (!response.headers.get('content-type')?.includes('text/event-stream')) {
        // SSE가 아니면 일반 응답으로 처리
        console.log('일반 응답으로 처리');
        
        // 응답이 JSON인지 확인
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          const result = await response.json();
          onProgress({ step: 'completed', message: '업로드 완료', result });
          return resolve(result);
        } else {
          // JSON이 아니면 텍스트로 처리
          const text = await response.text();
          console.log('텍스트 응답:', text);
          throw new Error(`예상치 못한 응답 형식: ${text}`);
        }
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      const processStream = async () => {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            console.log('스트림 종료');
            break;
          }
          
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          console.log('받은 청크:', chunk);
          
          // 버퍼에서 완전한 라인들만 처리
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 마지막 불완전한 라인은 버퍼에 유지
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const dataStr = line.slice(6).trim();
                if (!dataStr) continue; // 빈 데이터는 무시
                
                console.log('SSE 데이터 파싱:', dataStr);
                const data = JSON.parse(dataStr);
                console.log('파싱된 데이터:', data);
                
                // onProgress 호출
                onProgress(data);
                
                if (data.step === 'completed') {
                  console.log('업로드 완료:', data.result);
                  resolve(data.result);
                  return;
                } else if (data.step === 'error') {
                  console.error('업로드 오류:', data.message);
                  reject(new Error(data.message));
                  return;
                }
              } catch (e) {
                console.error('SSE 파싱 오류:', e, '라인:', line);
              }
            }
          }
        }
      };
      
      processStream().catch(error => {
        console.error('스트림 처리 오류:', error);
        reject(error);
      });
    })
    .catch(error => {
      console.error('fetch 오류:', error);
      reject(error);
    });
  });
};

// SSE 기반 배치 문서 업로드
export const uploadDocumentsBatchWithSSE = async (files, documentTitle, onProgress) => {
  const currentUser = await verifyToken();
  const token = localStorage.getItem('narutalk_token');
  
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('uploader_id', String(currentUser.employee_id));
  
  return new Promise((resolve, reject) => {
    fetch(`/documents/upload-batch-sse`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })
    .then(async response => {
      console.log('배치 SSE 응답 상태:', response.status);
      console.log('배치 SSE 응답 헤더:', response.headers.get('content-type'));
      
      // 에러 상태 코드 확인
      if (!response.ok) {
        console.error('배치 서버 에러:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('배치 에러 내용:', errorText);
        throw new Error(`서버 에러: ${response.status} - ${errorText}`);
      }
      
      // Content-Type 확인
      if (!response.headers.get('content-type')?.includes('text/event-stream')) {
        // SSE가 아니면 일반 응답으로 처리
        console.log('배치 업로드 - 일반 응답으로 처리');
        
        // 응답이 JSON인지 확인
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          const result = await response.json();
          onProgress({ 
            step: 'batch_completed', 
            message: '배치 업로드 완료', 
            summary: result 
          });
          return resolve(result);
        } else {
          // JSON이 아니면 텍스트로 처리
          const text = await response.text();
          console.log('배치 텍스트 응답:', text);
          throw new Error(`예상치 못한 응답 형식: ${text}`);
        }
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      const processStream = async () => {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            console.log('배치 스트림 종료');
            break;
          }
          
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          console.log('배치 청크:', chunk);
          
          // 버퍼에서 완전한 라인들만 처리
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 마지막 불완전한 라인은 버퍼에 유지
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const dataStr = line.slice(6).trim();
                if (!dataStr) continue; // 빈 데이터는 무시
                
                console.log('배치 SSE 데이터 파싱:', dataStr);
                const data = JSON.parse(dataStr);
                console.log('파싱된 데이터:', data);
                
                // onProgress 호출
                onProgress(data);
                
                if (data.step === 'batch_completed') {
                  console.log('배치 업로드 완료:', data.summary);
                  resolve(data.summary);
                  return;
                }
              } catch (e) {
                console.error('배치 SSE 파싱 오류:', e, '라인:', line);
              }
            }
          }
        }
      };
      
      processStream().catch(error => {
        console.error('배치 스트림 처리 오류:', error);
        reject(error);
      });
    })
    .catch(error => {
      console.error('배치 fetch 오류:', error);
      reject(error);
    });
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

// 대시보드 통계 데이터 조회
export const getDashboardStats = async () => {
  return await apiRequest('/api/employee/dashboard-stats', {
    method: 'GET',
  });
};

// 거래처 분석 요청
export const analyzeClient = async (params) => {
  return await apiRequest('/api/v1/client/analyze', {
    method: 'POST',
    body: JSON.stringify({
      query: params.query,
      generate_docs: params.generate_docs !== false, // 기본값 true
      output_dir: params.output_dir || null
    }),
  });
};

// 거래처 분석 헬스 체크
export const getClientHealthCheck = async () => {
  return await apiRequest('/api/v1/client/health', {
    method: 'GET',
  });
}; 