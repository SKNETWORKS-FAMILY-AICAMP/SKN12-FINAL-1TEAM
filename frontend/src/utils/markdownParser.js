export const parseMarkdown = (text) => {
  if (!text) return '';
  
  let html = text;
  
  // 헤더 변환 (####부터 h4로 변환, 역순으로 처리)
  html = html.replace(/^###### (.*$)/gim, '<h6>$1</h6>');
  html = html.replace(/^##### (.*$)/gim, '<h5>$1</h5>');
  html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  
  // 굵은 글씨 변환 (**text** or __text__)
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
  
  // 기울임 글씨 변환 (*text* or _text_)
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
  
  // 리스트 변환 (- item or * item)
  html = html.replace(/^\* (.+)$/gim, '<li>$1</li>');
  html = html.replace(/^- (.+)$/gim, '<li>$1</li>');
  
  // 연속된 li 태그를 ul로 감싸기
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => {
    return '<ul>' + match + '</ul>';
  });
  
  // 숫자 리스트 변환 (1. item)
  html = html.replace(/^\d+\. (.+)$/gim, '<li>$1</li>');
  
  // 코드 블록 변환 (```code```)
  html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
  
  // 인라인 코드 변환 (`code`)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // 수평선 변환 (---)
  html = html.replace(/^---$/gim, '<hr>');
  
  // 인용구 변환 (> quote)
  html = html.replace(/^> (.+)$/gim, '<blockquote>$1</blockquote>');
  
  // 줄바꿈을 br 태그로 변환 (단, HTML 태그 내부가 아닌 경우)
  html = html.split('\n').map(line => {
    // HTML 태그로 시작하지 않는 일반 텍스트 라인에만 <p> 태그 추가
    if (line.trim() && !line.trim().match(/^<[^>]+>/)) {
      return `<p>${line}</p>`;
    }
    return line;
  }).join('\n');
  
  // 빈 p 태그 제거
  html = html.replace(/<p><\/p>/g, '');
  
  return html;
};