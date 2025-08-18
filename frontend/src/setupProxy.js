const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Docker 환경 감지 (컨테이너 내부에서는 서비스명 사용)
  const isDocker = process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.includes('backend');
  
  // 환경별 URL 설정
  const backendUrl = isDocker ? 'http://backend:8000' : 'http://localhost:8000';
  // Docker 내부에서는 host.docker.internal을 사용하여 호스트의 8010 포트에 접근
  const dbApiUrl = isDocker ? 'http://host.docker.internal:8010' : 'http://localhost:8010';
  
  console.log('🔧 Proxy Configuration:', {
    isDocker,
    backendUrl,
    dbApiUrl
  });

  // SSE 엔드포인트를 위한 특별한 프록시 설정
  const sseProxy = createProxyMiddleware({
    target: dbApiUrl,
    changeOrigin: true,
    logLevel: 'debug',
    onProxyReq: (proxyReq, req, res) => {
      // SSE를 위해 버퍼링 비활성화
      proxyReq.setHeader('X-Accel-Buffering', 'no');
    },
    onProxyRes: (proxyRes, req, res) => {
      // SSE 응답 헤더 설정
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('X-Accel-Buffering', 'no');
      
      // Content-Length 헤더 제거 (SSE는 스트리밍이므로)
      delete proxyRes.headers['content-length'];
    },
    selfHandleResponse: false
  });
  
  // Agent Server API 프록시 (8000 포트)
  const agentApiProxy = createProxyMiddleware({
    target: backendUrl,
    changeOrigin: true,
    logLevel: 'debug',
    ws: false,
    onProxyReq: (proxyReq, req, res) => {
      console.log(`➡️ Agent API Proxy: ${req.method} ${req.path} -> ${backendUrl}${req.path}`);
    },
    onError: (err, req, res) => {
      console.error('❌ Agent API Proxy Error:', err);
      // http-proxy-middleware가 자동으로 502 에러 응답 처리
      // 직접 응답을 설정하면 충돌 발생 가능
    }
  });
  
  // Database API 프록시 (8010 포트)
  const dbApiProxy = createProxyMiddleware({
    target: dbApiUrl,
    changeOrigin: true,
    logLevel: 'debug',
    ws: false,
    onProxyReq: (proxyReq, req, res) => {
      console.log(`➡️ Database API Proxy: ${req.method} ${req.path} -> ${dbApiUrl}${req.path}`);
    },
    onError: (err, req, res) => {
      console.error('❌ Database API Proxy Error:', err);
      console.error('Make sure Database API is running on port 8010');
      console.error('Run: cd database/docker && docker-compose up -d');
      // http-proxy-middleware가 자동으로 502 에러 응답 처리
    }
  });

  // Agent Server API 경로들 (8000 포트로)
  const agentPaths = [
    '/api/v1',      // Router, Docs, Client Agent APIs
    '/api/employee', // Employee Agent API
    '/api/all-sessions',
    '/api/session',
    '/api/reset-agent',
    '/api/select-agent',
    '/api/initial-agent-select'
  ];

  // Database API 경로들 (8010 포트로)
  const databasePaths = [
    '/user',
    '/admin',
    '/employee-info',
    '/branches',
    '/documents',
    '/qa',
    '/search',
    '/hybrid'
  ];

  // 미들웨어로 경로별 프록시 처리
  app.use((req, res, next) => {
    const path = req.path;
    
    // SSE 엔드포인트는 특별한 프록시 사용
    if (path.includes('upload-sse') || path.endsWith('-sse')) {
      console.log('🔄 SSE Request:', path);
      return sseProxy(req, res, next);
    }
    
    // Agent Server API 경로 확인
    const isAgentPath = agentPaths.some(prefix => 
      path.startsWith(prefix) || path === prefix
    );
    
    if (isAgentPath) {
      console.log('🤖 Agent API Request:', path);
      return agentApiProxy(req, res, next);
    }
    
    // Database API 경로 확인
    const isDatabasePath = databasePaths.some(prefix => 
      path.startsWith(prefix + '/') || path === prefix
    );
    
    if (isDatabasePath) {
      console.log('💾 Database API Request:', path);
      return dbApiProxy(req, res, next);
    }
    
    // 그 외는 다음 미들웨어로
    return next();
  });
};