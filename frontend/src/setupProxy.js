const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // SSE 엔드포인트를 위한 특별한 프록시 설정
  const sseProxy = createProxyMiddleware({
    target: 'http://backend:8000',
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
  
  // 일반 API 프록시 (백엔드 에이전트 서버)
  const apiProxy = createProxyMiddleware({
    target: 'http://backend:8000',
    changeOrigin: true,
    logLevel: 'debug',
    ws: false
  });
  
  // Database API 프록시 (8010 포트)
  const dbApiProxy = createProxyMiddleware({
    target: 'http://fastapi-app:8000',  // Docker 내부에서는 서비스명:내부포트 사용
    changeOrigin: true,
    logLevel: 'debug',
    ws: false
  });

  // 미들웨어로 경로별 프록시 처리
  app.use((req, res, next) => {
    const path = req.path;
    
    // SSE 엔드포인트는 특별한 프록시 사용
    if (path === '/documents/upload-sse' || path === '/documents/upload-batch-sse') {
      return sseProxy(req, res, next);
    }
    
    // documents 경로는 Database 프록시 사용 (8010)
    if (path.startsWith('/documents')) {
      return dbApiProxy(req, res, next);
    }
    
    // 그 외 API 경로는 백엔드 프록시 사용 (8000)
    if (path.startsWith('/user') || 
        path.startsWith('/admin') || 
        path.startsWith('/employee-info') || 
        path.startsWith('/api')) {
      return apiProxy(req, res, next);
    }
    
    // 그 외는 다음 미들웨어로
    return next();
  });
};