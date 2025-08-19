import React, { useState, useEffect } from 'react';
import { analyzeClient, getClientHealthCheck } from '../services/api';
import { parseMarkdown } from '../utils/markdownParser';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';
import { saveAs } from 'file-saver';
import './ClientAnalysis.css';

const ClientAnalysis = ({ currentUser }) => {
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [error, setError] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [currentReport, setCurrentReport] = useState(null);
  const [serviceStatus, setServiceStatus] = useState(null);

  // 컴포넌트 마운트 시 서비스 상태 확인
  useEffect(() => {
    checkServiceHealth();
    loadAnalysisHistory();
  }, []);

  const checkServiceHealth = async () => {
    try {
      const health = await getClientHealthCheck();
      setServiceStatus(health);
      console.log('Client Agent 서비스 상태:', health);
    } catch (error) {
      console.error('서비스 상태 확인 실패:', error);
      setError('거래처 분석 서비스가 준비되지 않았습니다.');
    }
  };

  const loadAnalysisHistory = () => {
    // 사용자별 localStorage 키 생성
    const userId = currentUser?.employee_id || currentUser?.email || 'guest';
    const storageKey = `clientAnalysisHistory_${userId}`;
    
    // localStorage에서 분석 히스토리 불러오기
    const savedHistory = localStorage.getItem(storageKey);
    if (savedHistory) {
      try {
        const history = JSON.parse(savedHistory);
        setAnalysisHistory(history);
      } catch (error) {
        console.error('분석 히스토리 로드 실패:', error);
      }
    }
  };

  const saveAnalysisHistory = (newAnalysis) => {
    const userId = currentUser?.employee_id || currentUser?.email || 'guest';
    const storageKey = `clientAnalysisHistory_${userId}`;
    
    const updatedHistory = [newAnalysis, ...analysisHistory].slice(0, 10); // 최대 10개 저장
    setAnalysisHistory(updatedHistory);
    localStorage.setItem(storageKey, JSON.stringify(updatedHistory));
  };

  const handleAnalyze = async () => {
    if (!analysisQuery.trim()) return;
    
    const userMsg = analysisQuery.trim();
    setLoading(true);
    setError(null);
    setCurrentReport(null);
    
    try {
      // API 호출
      const response = await analyzeClient({
        query: userMsg,
        generate_docs: true
      });
      
      if (response.success) {
        // 현재 보고서 설정
        setCurrentReport(response);
        setSelectedAnalysis(`${response.company_name || '분석'} 보고서`);
        
        // 분석 히스토리에 추가
        const historyItem = {
          id: Date.now(),
          company_name: response.company_name,
          query: userMsg,
          timestamp: new Date().toISOString(),
          report: response.final_report,
          grade: response.grade_result
        };
        saveAnalysisHistory(historyItem);
        
        // 입력창 초기화
        setAnalysisQuery('');
      } else {
        throw new Error(response.error || '분석 실패');
      }
    } catch (error) {
      console.error('거래처 분석 실패:', error);
      setError(error.message || '거래처 분석 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleNewAnalysis = () => {
    setCurrentReport(null);
    setSelectedAnalysis(null);
    setError(null);
    setAnalysisQuery('');
  };

  const handleSelectHistory = (item) => {
    setSelectedAnalysis(`${item.company_name} 보고서`);
    setCurrentReport({
      company_name: item.company_name,
      final_report: item.report,
      grade_result: item.grade
    });
  };

  const handleDeleteHistory = (e, itemId) => {
    e.stopPropagation(); // 클릭 이벤트 전파 방지
    
    const userId = currentUser?.employee_id || currentUser?.email || 'guest';
    const storageKey = `clientAnalysisHistory_${userId}`;
    
    const updatedHistory = analysisHistory.filter(item => item.id !== itemId);
    setAnalysisHistory(updatedHistory);
    localStorage.setItem(storageKey, JSON.stringify(updatedHistory));
    
    // 현재 선택된 항목이 삭제된 경우 초기화
    const deletedItem = analysisHistory.find(item => item.id === itemId);
    if (deletedItem && currentReport?.company_name === deletedItem.company_name) {
      handleNewAnalysis();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleAnalyze();
    }
  };

  const handleDownloadReport = async () => {
    if (!currentReport) return;
    
    try {
      const doc = new Document({
        sections: [
          {
            properties: {},
            children: [
              // 제목
              new Paragraph({
                text: `${currentReport.company_name || '거래처'} 분석 보고서`,
                heading: HeadingLevel.TITLE,
                alignment: AlignmentType.CENTER,
              }),
              new Paragraph({
                text: `작성일: ${new Date().toLocaleDateString('ko-KR')}`,
                alignment: AlignmentType.CENTER,
                spacing: { after: 400 },
              }),
              
              // 등급 평가
              new Paragraph({
                text: '등급 평가',
                heading: HeadingLevel.HEADING_1,
                spacing: { before: 400, after: 200 },
              }),
              new Paragraph({
                children: [
                  new TextRun({ text: '최종 등급: ', bold: true }),
                  new TextRun(currentReport.grade_result?.final_grade || 'N/A'),
                ],
              }),
              new Paragraph({
                children: [
                  new TextRun({ text: '점수: ', bold: true }),
                  new TextRun(`${currentReport.grade_result?.total_score || 0}점`),
                ],
                spacing: { after: 400 },
              }),
              
              // 분석 보고서 내용
              new Paragraph({
                text: '분석 보고서',
                heading: HeadingLevel.HEADING_1,
                spacing: { before: 400, after: 200 },
              }),
              ...parseReportToDocx(currentReport.final_report || ''),
            ],
          },
        ],
      });
      
      const blob = await Packer.toBlob(doc);
      const fileName = `거래처분석보고서_${currentReport.company_name || '분석'}_${new Date().toISOString().slice(0, 10)}.docx`;
      saveAs(blob, fileName);
    } catch (error) {
      console.error('보고서 다운로드 실패:', error);
      setError('보고서 다운로드에 실패했습니다.');
    }
  };
  
  const parseReportToDocx = (reportText) => {
    if (!reportText) return [];
    
    const lines = reportText.split('\n');
    const paragraphs = [];
    
    lines.forEach(line => {
      const trimmedLine = line.trim();
      if (!trimmedLine) {
        paragraphs.push(new Paragraph({ text: '' }));
        return;
      }
      
      // 헤더 처리
      if (trimmedLine.startsWith('######')) {
        paragraphs.push(
          new Paragraph({
            text: trimmedLine.replace(/^######\s*/, ''),
            heading: HeadingLevel.HEADING_6,
            spacing: { before: 200, after: 100 },
          })
        );
      } else if (trimmedLine.startsWith('#####')) {
        paragraphs.push(
          new Paragraph({
            text: trimmedLine.replace(/^#####\s*/, ''),
            heading: HeadingLevel.HEADING_5,
            spacing: { before: 200, after: 100 },
          })
        );
      } else if (trimmedLine.startsWith('####')) {
        paragraphs.push(
          new Paragraph({
            text: trimmedLine.replace(/^####\s*/, ''),
            heading: HeadingLevel.HEADING_4,
            spacing: { before: 200, after: 100 },
          })
        );
      } else if (trimmedLine.startsWith('###')) {
        paragraphs.push(
          new Paragraph({
            text: trimmedLine.replace(/^###\s*/, ''),
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 200, after: 100 },
          })
        );
      } else if (trimmedLine.startsWith('##')) {
        paragraphs.push(
          new Paragraph({
            text: trimmedLine.replace(/^##\s*/, ''),
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 300, after: 150 },
          })
        );
      } else if (trimmedLine.startsWith('#')) {
        paragraphs.push(
          new Paragraph({
            text: trimmedLine.replace(/^#\s*/, ''),
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 400, after: 200 },
          })
        );
      }
      // 리스트 항목 처리
      else if (trimmedLine.startsWith('-') || trimmedLine.startsWith('*')) {
        paragraphs.push(
          new Paragraph({
            text: trimmedLine.replace(/^[-*]\s*/, ''),
            bullet: { level: 0 },
            spacing: { after: 100 },
          })
        );
      }
      // 일반 텍스트
      else {
        const children = [];
        let currentText = trimmedLine;
        
        // 간단한 굵은 글씨 처리
        const boldRegex = /\*\*(.+?)\*\*/g;
        let lastIndex = 0;
        let match;
        
        while ((match = boldRegex.exec(currentText)) !== null) {
          if (match.index > lastIndex) {
            children.push(new TextRun(currentText.substring(lastIndex, match.index)));
          }
          children.push(new TextRun({ text: match[1], bold: true }));
          lastIndex = match.index + match[0].length;
        }
        
        if (lastIndex < currentText.length) {
          children.push(new TextRun(currentText.substring(lastIndex)));
        }
        
        paragraphs.push(
          new Paragraph({
            children: children.length > 0 ? children : [new TextRun(trimmedLine)],
            spacing: { after: 100 },
          })
        );
      }
    });
    
    return paragraphs;
  };

  return (
    <div className="client-page">
      {/* Left Sidebar */}
      <div className="client-sidebar">
        <h2>거래처 분석</h2>
        
        <button className="new-analysis-btn" onClick={handleNewAnalysis}>
          <span className="plus-icon">+</span>
          새로운 거래처 분석
        </button>

        <div className="existing-analyses">
          <h3>분석 히스토리</h3>
          {analysisHistory.length > 0 ? (
            analysisHistory.map((item) => (
              <div 
                key={item.id} 
                className="analysis-item"
                onClick={() => handleSelectHistory(item)}
                style={{ cursor: 'pointer', position: 'relative' }}
              >
                <span className="analysis-icon">📊</span>
                <span className="analysis-name">
                  {item.company_name || '분석'} - {new Date(item.timestamp).toLocaleDateString()}
                </span>
                <button 
                  className="delete-btn"
                  onClick={(e) => handleDeleteHistory(e, item.id)}
                  title="삭제"
                >
                  ×
                </button>
              </div>
            ))
          ) : (
            <div className="no-analyses">
              <p>분석 히스토리가 없습니다.</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="client-main-full">
        <div className="analysis-content">
          <div className="content-header">
            <h1>{selectedAnalysis || '거래처 분석'}</h1>
            {currentReport && !loading && (
              <button 
                className="download-btn"
                onClick={handleDownloadReport}
                title="보고서 다운로드"
              >
                📥 보고서 다운로드
              </button>
            )}
          </div>
          
          {/* 입력 영역 */}
          {!loading && !currentReport && (
            <div className="input-section">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={analysisQuery}
                  onChange={(e) => setAnalysisQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="거래처명과 분석 기간을 입력하세요... (예: 서울대병원 2024년 1월부터 12월까지)"
                  className="analysis-input"
                  disabled={loading}
                />
                <button 
                  onClick={handleAnalyze}
                  className="analyze-button"
                  disabled={loading || !analysisQuery.trim()}
                >
                  분석 시작
                </button>
              </div>
              <div className="input-hint">
                <p>💡 예시: "서울대병원 2024년 분석해줘", "삼성전자 2024년 3분기 실적 분석"</p>
              </div>
            </div>
          )}

          {/* 로딩 스피너 */}
          {loading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p className="loading-text">거래처 분석 중입니다...</p>
              <p className="loading-subtext">잠시만 기다려주세요</p>
            </div>
          )}
          
          {/* 에러 메시지 */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          {/* 분석 결과 */}
          {currentReport && !loading && (
            <div className="analysis-body">
                <div className="report-container">
                {currentReport.final_report && (
                  <div className="report-section">
                    <h2>📋 분석 보고서</h2>
                    <div 
                      className="markdown-content"
                      dangerouslySetInnerHTML={{ __html: parseMarkdown(currentReport.final_report) }}
                    />
                  </div>
                )}
                
                {currentReport.grade_result && (
                  <div className="report-section">
                    <h2>📊 등급 평가</h2>
                    <div className="grade-info">
                      <p><strong>최종 등급:</strong> {currentReport.grade_result['최종등급'] || currentReport.grade_result.final_grade || 'N/A'}</p>
                      <p><strong>점수:</strong> {currentReport.grade_result['총점'] || currentReport.grade_result.total_score || 0}점</p>
                      {currentReport.grade_result['세부등급'] && (
                        <div className="grade-details">
                          <p><strong>세부 등급:</strong></p>
                          <ul>
                            {Object.entries(currentReport.grade_result['세부등급']).map(([key, value]) => (
                              <li key={key}>
                                {key}: {value.등급 || value.grade || 'N/A'}
                                {value.평균 && ` (평균: ${value.평균.toLocaleString()})`}
                                {value.비율 && ` (비율: ${value.비율}%)`}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {currentReport.grade_result['요약'] && (
                        <div className="grade-details">
                          <p><strong>실적 요약:</strong></p>
                          <ul>
                            <li>총 매출액: {currentReport.grade_result['요약']['총매출']?.toLocaleString() || 0}원</li>
                            <li>월평균 매출: {currentReport.grade_result['요약']['월평균매출']?.toLocaleString() || 0}원</li>
                            <li>평균 환자수: {currentReport.grade_result['요약']['평균환자수']?.toLocaleString() || 0}명</li>
                            <li>월평균 방문: {currentReport.grade_result['요약']['월평균방문'] || 0}회</li>
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClientAnalysis;