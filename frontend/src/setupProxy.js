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
  
  // 일반 API 프록시
  const apiProxy = createProxyMiddleware({
    target: 'http://backend:8000',
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
    
    // 일반 API 경로는 일반 프록시 사용
    if (path.startsWith('/user') || 
        path.startsWith('/admin') || 
        path.startsWith('/documents') || 
        path.startsWith('/employee-info') || 
        path.startsWith('/api')) {
      return apiProxy(req, res, next);
    }
    
    // 그 외는 다음 미들웨어로
    return next();
  });
};