import React, { useState, useEffect, useRef } from 'react';
import { 
  getEmployeeList, 
  analyzeEmployeePerformance,
  getDashboardStats 
} from '../services/api';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';
import { saveAs } from 'file-saver';
import './EmployeePerformance.css';

const EmployeePerformance = ({ currentUser }) => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // 분석 히스토리 관련 상태
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  
  // 채팅 형식의 메시지 관련 상태
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);
  
  // 대시보드 통계 상태
  const [dashboardStats, setDashboardStats] = useState(null);
  const [reportStats, setReportStats] = useState(null); // 보고서 생성 시 업데이트될 통계
  const [gradeDetails, setGradeDetails] = useState(null); // 등급 상세 정보
  
  // 중복 직원 선택을 위한 상태
  const [showEmployeeSelection, setShowEmployeeSelection] = useState(false);
  const [employeeCandidates, setEmployeeCandidates] = useState([]);
  const [pendingQuery, setPendingQuery] = useState(null);
  
  const isAdmin = currentUser?.role === 'admin';

  // 사용자별 localStorage 키 생성 함수
  const getUserHistoryKey = () => {
    if (!currentUser) return 'employeeAnalysisHistory_guest';
    // 사용자 ID나 이메일을 기반으로 고유 키 생성
    const userId = currentUser.employee_id || currentUser.email || currentUser.username || 'unknown';
    return `employeeAnalysisHistory_${userId}`;
  };

  // 컴포넌트 마운트 시 직원 목록 가져오기 (관리자만)
  useEffect(() => {
    console.log('EmployeePerformance - Current User:', currentUser);
    console.log('EmployeePerformance - Is Admin:', isAdmin);
    
    if (isAdmin) {
      fetchEmployeeList();
    } else if (currentUser) {
      setSelectedEmployee(currentUser.name || currentUser.username || currentUser.email);
      console.log('Set selected employee to:', currentUser.name || currentUser.username || currentUser.email);
    }
    
    // 대시보드 통계 가져오기
    fetchDashboardStats();
    
    // localStorage에서 사용자별 분석 히스토리 불러오기
    if (currentUser) {
      const userHistoryKey = getUserHistoryKey();
      const savedHistory = localStorage.getItem(userHistoryKey);
      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          setAnalysisHistory(parsed);
        } catch (error) {
          console.error('분석 히스토리 불러오기 실패:', error);
        }
      } else {
        // 새 사용자의 경우 빈 히스토리로 초기화
        setAnalysisHistory([]);
      }
    }
  }, [isAdmin, currentUser]);

  // 메시지 변경 시 자동 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchEmployeeList = async () => {
    try {
      const data = await getEmployeeList();
      setEmployees(data.employees || []);
      if (data.employees && data.employees.length > 0) {
        setSelectedEmployee(data.employees[0].name);
      }
    } catch (error) {
      console.error('직원 목록 조회 실패:', error);
      setError('직원 목록을 불러오는데 실패했습니다.');
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const data = await getDashboardStats();
      console.log('Dashboard stats:', data);
      setDashboardStats(data);
    } catch (error) {
      console.error('대시보드 통계 조회 실패:', error);
      // 실패해도 기본값으로 표시
      setDashboardStats({
        stats: [
          {
            title: "목표 달성률",
            value: "0%",
            change: "0%",
            trend: "neutral",
            period: "이번 달"
          },
          {
            title: "매출 증감률",
            value: "0%",
            change: "₩0",
            trend: "neutral",
            period: "전월 대비"
          },
          {
            title: "분기 총 실적",
            value: "₩0",
            change: "0개 거래처",
            trend: "neutral",
            period: "최근 3개월"
          }
        ]
      });
    }
  };

  // 보고서에서 통계 추출
  const extractStatsFromReport = (result) => {
    if (!result) return null;
    
    const stats = [];
    let gradeDetails = null;
    
    // 1. 목표 달성률
    const achievementRate = result.summary?.achievement_rate || 
                           result.target_data?.achievement_rate || 
                           result.analysis_results?.achievement_analysis?.achievement_rate || 0;
    
    if (achievementRate !== undefined && achievementRate !== null) {
      stats.push({
        title: "목표 달성률",
        value: `${achievementRate.toFixed(1)}%`,
        change: result.summary?.evaluation || result.target_data?.evaluation || "평가 중",
        trend: achievementRate >= 100 ? "up" : achievementRate >= 80 ? "neutral" : "down",
        period: result.period || "분석 기간"
      });
    }
    
    // 2. 실적 등급 - 등급 상세 정보 포함
    const grade = result.summary?.grade || 
                 result.target_data?.grade || 
                 result.analysis_results?.achievement_analysis?.grade;
    
    if (grade && grade !== "N/A") {
      const gradeToTrend = {
        'S': 'up',
        'A': 'up',
        'B': 'neutral',
        'C': 'down',
        'D': 'down'
      };
      
      // 등급 상세 정보 추출
      const comprehensiveEval = result.analysis_results?.comprehensive_evaluation;
      let gradeDetail = "";
      if (comprehensiveEval) {
        const scoreBreakdown = comprehensiveEval.score_breakdown || {};
        gradeDetail = `총점: ${comprehensiveEval.total_score || 0}점 (달성률 ${scoreBreakdown.achievement || 0}점 + 성장률 ${scoreBreakdown.growth || 0}점 + 안정성 ${scoreBreakdown.stability || 0}점)`;
      }
      
      stats.push({
        title: "실적 등급",
        value: grade,
        change: result.summary?.evaluation || result.target_data?.evaluation || "종합 평가",
        trend: gradeToTrend[grade] || 'neutral',
        period: gradeDetail || "현재 평가"
      });
    }
    
    // 3. 총 실적 금액
    const totalPerformance = result.target_data?.total_performance || 
                            result.analysis_results?.achievement_analysis?.total_performance || 0;
    
    if (totalPerformance > 0) {
      stats.push({
        title: "총 실적",
        value: `₩${totalPerformance.toLocaleString()}`,
        change: "실적 금액",
        trend: "neutral",
        period: result.period || "분석 기간"
      });
    }
    
    // 통계가 없으면 null 반환 (기본 대시보드 통계 유지)
    return stats.length > 0 ? { stats } : null;
  };

  const handleAnalysis = async () => {
    if (!analysisQuery) {
      setError('분석할 내용을 입력해주세요.');
      return;
    }

    setLoading(true);
    setError('');
    
    // 디버깅용 로그
    console.log('Current User:', currentUser);
    console.log('Is Admin:', isAdmin);
    console.log('Selected Employee:', selectedEmployee);
    
    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: analysisQuery,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    try {
      console.log('Current User:', currentUser);
      console.log('Is Admin:', isAdmin);
      console.log('Original Query:', analysisQuery);
      
      // 관리자인 경우에만 직원명 전달, 일반 사용자는 백엔드에서 자동 처리
      let requestData = {
        query: analysisQuery
      };
      
      // 관리자가 특정 직원을 선택한 경우에만 employee_name 추가
      if (isAdmin && selectedEmployee) {
        requestData.employee_name = selectedEmployee;
        console.log('Admin selected employee:', selectedEmployee);
      }
      
      console.log('Request data:', requestData);
      
      const result = await analyzeEmployeePerformance(requestData);
      
      // 중복 직원 선택 필요 여부 확인
      if (result.status === 'requires_selection') {
        // 중복 직원 발견 - 선택 모달 표시
        setEmployeeCandidates(result.candidates);
        setPendingQuery(requestData); // 나중에 재요청할 쿼리 저장
        setShowEmployeeSelection(true);
        setLoading(false);
        return;
      }
      
      // AI 응답 메시지 추가
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: result.report || JSON.stringify(result, null, 2),
        data: result,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
      
      // 현재 분석 결과 저장
      setCurrentAnalysis(result);
      
      // 보고서에서 통계 추출 및 업데이트
      const extractedData = extractStatsFromReport(result);
      if (extractedData) {
        setReportStats({ stats: extractedData.stats });
        setGradeDetails(extractedData.gradeDetails);
      }
      
      // 히스토리에 추가
      const newHistoryItem = {
        id: Date.now(),
        title: `${isAdmin ? selectedEmployee : currentUser?.name} - ${new Date().toLocaleString('ko-KR')}`,
        query: analysisQuery,
        result: result,
        messages: [...messages, userMessage, aiMessage],
        timestamp: new Date().toISOString()
      };
      
      const updatedHistory = [...analysisHistory, newHistoryItem];
      setAnalysisHistory(updatedHistory);
      setActiveHistoryId(newHistoryItem.id);
      
      // 사용자별 localStorage에 저장
      const userHistoryKey = getUserHistoryKey();
      localStorage.setItem(userHistoryKey, JSON.stringify(updatedHistory));
      
    } catch (error) {
      console.error('분석 실패:', error);
      
      // 에러 메시지 처리
      let errorContent = '분석 중 오류가 발생했습니다.';
      
      // 서버에서 전달된 에러 메시지 확인
      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail || '';
        
        if (status === 403) {
          // 권한 오류 - 다른 직원 데이터 접근 시도
          errorContent = '본인의 실적 데이터만 조회할 수 있습니다.\n다른 직원의 이름을 언급하지 말고 본인의 실적을 조회해주세요.';
        } else if (status === 404 || detail.includes('실적 데이터가 없습니다')) {
          // 실적 데이터 없음
          errorContent = '실적 데이터가 없습니다.\n데이터가 입력되지 않았거나 해당 기간에 실적이 없을 수 있습니다.';
        } else if (status === 400) {
          // 잘못된 요청
          errorContent = detail || '잘못된 요청입니다. 쿼리를 확인해주세요.';
        } else {
          // 기타 오류
          errorContent = detail || '분석 중 오류가 발생했습니다.';
        }
      }
      
      setError(errorContent);
      
      // 에러 메시지 추가
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: errorContent,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setAnalysisQuery('');
    }
  };

  // 히스토리 항목 선택
  const selectHistory = (historyItem) => {
    setActiveHistoryId(historyItem.id);
    setMessages(historyItem.messages || []);
    setCurrentAnalysis(historyItem.result);
    
    // 선택한 히스토리의 보고서에서 통계 추출
    const extractedData = extractStatsFromReport(historyItem.result);
    if (extractedData) {
      setReportStats({ stats: extractedData.stats });
      setGradeDetails(extractedData.gradeDetails);
    }
  };

  // 새 분석 시작
  const startNewAnalysis = () => {
    setActiveHistoryId(null);
    setMessages([]);
    setCurrentAnalysis(null);
    setReportStats(null); // 보고서 통계 초기화
    setGradeDetails(null); // 등급 상세 정보 초기화
  };

  // 히스토리 삭제
  const deleteHistory = (historyId) => {
    const updatedHistory = analysisHistory.filter(item => item.id !== historyId);
    setAnalysisHistory(updatedHistory);
    const userHistoryKey = getUserHistoryKey();
    localStorage.setItem(userHistoryKey, JSON.stringify(updatedHistory));
    
    if (activeHistoryId === historyId) {
      startNewAnalysis();
    }
  };

  // 보고서 다운로드 (DOCX)
  const downloadReport = async () => {
    if (!currentAnalysis) {
      alert('다운로드할 보고서가 없습니다.');
      return;
    }
    
    // 문서 생성
    const doc = new Document({
      sections: [{
        properties: {},
        children: [
          // 제목
          new Paragraph({
            text: "직원 실적 분석 보고서",
            heading: HeadingLevel.TITLE,
            alignment: AlignmentType.CENTER,
            spacing: { after: 400 }
          }),
          
          // 기본 정보
          new Paragraph({
            text: "기본 정보",
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 400, after: 200 }
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "생성일시: ", bold: true }),
              new TextRun(new Date().toLocaleString('ko-KR'))
            ],
            spacing: { after: 100 }
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "분석 대상: ", bold: true }),
              new TextRun(isAdmin ? selectedEmployee : currentUser?.name || '')
            ],
            spacing: { after: 100 }
          }),
          new Paragraph({
            children: [
              new TextRun({ text: "분석 기간: ", bold: true }),
              new TextRun(currentAnalysis.period || '')
            ],
            spacing: { after: 300 }
          }),
          
          // 분석 결과
          new Paragraph({
            text: "분석 결과",
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 400, after: 200 }
          }),
          ...(currentAnalysis.report ? 
            currentAnalysis.report.split('\n').filter(line => line.trim()).map(line => 
              new Paragraph({
                text: line,
                spacing: { after: 100 }
              })
            ) : [new Paragraph({ text: "분석 결과가 없습니다." })]),
          
          // 통계 요약
          new Paragraph({
            text: "통계 요약",
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 400, after: 200 }
          }),
          ...(reportStats?.stats?.map(stat => 
            new Paragraph({
              children: [
                new TextRun({ text: `${stat.title}: `, bold: true }),
                new TextRun(stat.value),
                new TextRun(` (${stat.change})`)
              ],
              spacing: { after: 100 }
            })
          ) || [new Paragraph({ text: "통계 정보가 없습니다." })]),
          
          // 평가 등급
          ...(currentAnalysis.summary?.grade ? [
            new Paragraph({
              text: "종합 평가",
              heading: HeadingLevel.HEADING_1,
              spacing: { before: 400, after: 200 }
            }),
            new Paragraph({
              children: [
                new TextRun({ text: "등급: ", bold: true }),
                new TextRun({ text: currentAnalysis.summary.grade, size: 28, bold: true }),
                new TextRun(` (${currentAnalysis.summary.evaluation || '평가'})`)
              ],
              spacing: { after: 100 }
            })
          ] : []),
          
          // 푸터
          new Paragraph({
            text: "Generated by Narutalk Employee Performance System",
            alignment: AlignmentType.CENTER,
            spacing: { before: 600 },
            style: "footer"
          })
        ]
      }]
    });
    
    // 문서를 Blob으로 변환하고 다운로드
    try {
      const blob = await Packer.toBlob(doc);
      const fileName = `실적분석보고서_${isAdmin ? selectedEmployee : currentUser?.name}_${new Date().toISOString().slice(0, 10)}.docx`;
      saveAs(blob, fileName);
    } catch (error) {
      console.error('문서 생성 실패:', error);
      alert('문서 생성에 실패했습니다.');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW'
    }).format(amount);
  };

  // 중복 직원 선택 처리
  const handleEmployeeSelection = async (selectedEmployeeId) => {
    setShowEmployeeSelection(false);
    setLoading(true);
    
    try {
      // pendingQuery에 선택한 employee_info_id 추가
      const requestData = {
        ...pendingQuery,
        employee_info_id: selectedEmployeeId
      };
      
      console.log('Retrying with selected employee:', requestData);
      
      const result = await analyzeEmployeePerformance(requestData);
      
      // AI 응답 메시지 추가
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: result.report || JSON.stringify(result, null, 2),
        data: result,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);
      
      // 현재 분석 결과 저장
      setCurrentAnalysis(result);
      
      // 보고서에서 통계 추출 및 업데이트
      const extractedData = extractStatsFromReport(result);
      if (extractedData) {
        setReportStats({ stats: extractedData.stats });
        setGradeDetails(extractedData.gradeDetails);
      }
      
      // 히스토리에 추가
      const newHistoryItem = {
        id: Date.now(),
        title: `${result.employee_name} - ${new Date().toLocaleString('ko-KR')}`,
        query: pendingQuery.query,
        result: result,
        messages: [...messages, aiMessage],
        timestamp: new Date().toISOString()
      };
      
      const updatedHistory = [...analysisHistory, newHistoryItem];
      setAnalysisHistory(updatedHistory);
      setActiveHistoryId(newHistoryItem.id);
      
      // localStorage에 저장
      const userHistoryKey = getUserHistoryKey();
      localStorage.setItem(userHistoryKey, JSON.stringify(updatedHistory));
      
    } catch (error) {
      console.error('재분석 실패:', error);
      setError('재분석에 실패했습니다.');
    } finally {
      setLoading(false);
      setPendingQuery(null);
    }
  };

  return (
    <div className="employee-performance">
      {/* 중복 직원 선택 모달 */}
      {showEmployeeSelection && (
        <div className="modal-overlay" onClick={() => setShowEmployeeSelection(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>직원 선택</h2>
              <button 
                className="modal-close" 
                onClick={() => setShowEmployeeSelection(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <p className="modal-message">
                '{employeeCandidates[0]?.name}' 이름을 가진 직원이 {employeeCandidates.length}명 있습니다.
                <br />
                분석할 직원을 선택해주세요.
              </p>
              <div className="employee-selection-list">
                {employeeCandidates.map((candidate) => (
                  <div 
                    key={candidate.employee_info_id}
                    className={`employee-selection-item ${!candidate.has_sales_data ? 'disabled' : ''}`}
                    onClick={() => {
                      if (!candidate.has_sales_data) {
                        alert(`${candidate.name} (${candidate.employee_number}) 직원은 실적 데이터가 없습니다.`);
                        return;
                      }
                      handleEmployeeSelection(candidate.employee_info_id);
                    }}
                  >
                    <div className="employee-info">
                      <div className="employee-name">{candidate.name}</div>
                      <div className="employee-details">
                        <span className="employee-number">사번: {candidate.employee_number}</span>
                        {candidate.department && (
                          <span className="employee-department"> | {candidate.department}</span>
                        )}
                        {candidate.position && (
                          <span className="employee-position"> | {candidate.position}</span>
                        )}
                      </div>
                      <div className="employee-data-status">
                        {candidate.has_sales_data ? (
                          <span className="has-data">✓ 실적 데이터 있음</span>
                        ) : (
                          <span className="no-data">실적 데이터 없음</span>
                        )}
                      </div>
                    </div>
                    <div className="selection-arrow">→</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="performance-header">
        <h1>실적 분석</h1>
      </div>

      <div className="performance-layout">
        {/* 왼쪽: 메모리 세션 (히스토리) */}
        <div className="history-sidebar">
          <div className="sidebar-header">
            <h3>분석 히스토리</h3>
            <button className="new-analysis-btn" onClick={startNewAnalysis}>
              + 새 분석
            </button>
          </div>
          <div className="history-list">
            {analysisHistory.length === 0 ? (
              <div className="empty-history">
                아직 분석 기록이 없습니다
              </div>
            ) : (
              analysisHistory.map(item => (
                <div 
                  key={item.id}
                  className={`history-item ${activeHistoryId === item.id ? 'active' : ''}`}
                  onClick={() => selectHistory(item)}
                >
                  <div className="history-title">{item.title}</div>
                  <div className="history-date">
                    {new Date(item.timestamp).toLocaleDateString('ko-KR')}
                  </div>
                  <button 
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistory(item.id);
                    }}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 가운데: 메인 콘텐츠 */}
        <div className="performance-main-content">
          <div className="search-section">
            {isAdmin && (
              <div className="control-group">
                <label>직원 선택</label>
                <select 
                  value={selectedEmployee} 
                  onChange={(e) => setSelectedEmployee(e.target.value)}
                  className="employee-select"
                >
                  <option value="">직원을 선택하세요</option>
                  {employees.map((emp) => (
                    <option key={emp.employee_id} value={emp.name}>
                      {emp.name} (사번: {emp.사번})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="analysis-controls">
              <div className="control-group query-group">
                <label>실적 분석 쿼리</label>
                <input
                  type="text"
                  value={analysisQuery}
                  onChange={(e) => setAnalysisQuery(e.target.value)}
                  placeholder={isAdmin ? "예: 2024년 1월부터 6월까지 실적 분석" : "예: 2024년 1월부터 6월까지 내 실적 분석"}
                  className="analysis-input"
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalysis()}
                />
              </div>
              <div className="button-group">
                <button onClick={handleAnalysis} className="analysis-btn" disabled={loading}>
                  {loading ? '분석 중...' : '🔍 분석하기'}
                </button>
                {currentAnalysis && (
                  <button onClick={downloadReport} className="download-btn">
                    📥 보고서 다운로드
                  </button>
                )}
              </div>
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* 로딩 스피너 */}
          {loading && (
            <div className="loading-overlay">
              <div className="loading-container">
                <div className="spinner"></div>
                <p>실적 데이터를 분석하는 중...</p>
              </div>
            </div>
          )}

          {/* 실적 요약 카드 - 보고서 생성 시 업데이트, 없으면 대시보드 통계 표시 */}
          {!loading && (reportStats || dashboardStats) && (
            <>
              <div className="performance-summary-cards">
                {(reportStats?.stats || dashboardStats?.stats || []).map((stat, index) => (
                  <div key={index} className="summary-card">
                    <div className="card-title">{stat.title}</div>
                    <div className="card-value">
                      {stat.value}
                    </div>
                    <div className={`card-change ${stat.trend === 'up' ? 'positive' : stat.trend === 'down' ? 'negative' : ''}`}>
                      {stat.change}
                    </div>
                    <div className="card-period">
                      {stat.period}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* 실적 추이 그래프 */}
          {currentAnalysis && (
            <div className="performance-charts-section">
              <h3>실적 추이 분석</h3>
              
              {/* 월별 실적 추이 차트 */}
              {currentAnalysis.analysis_results?.performance_data?.monthly_breakdown && (
                <div className="chart-container">
                  <h4>월별 실적 추이</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart 
                      data={currentAnalysis.analysis_results.performance_data.monthly_breakdown.map(item => ({
                        month: item.month.substring(4) + '월',
                        실적: item.amount
                      }))}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis tickFormatter={(value) => `₩${(value/10000).toFixed(0)}만`} />
                      <Tooltip formatter={(value) => `₩${value.toLocaleString()}`} />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="실적" 
                        stroke="#6c5ce7" 
                        strokeWidth={2}
                        dot={{ fill: '#6c5ce7', r: 5 }}
                        activeDot={{ r: 8 }} 
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* 제품별 실적 차트 */}
              {currentAnalysis.analysis_results?.performance_data?.product_breakdown && 
               currentAnalysis.analysis_results.performance_data.product_breakdown.length > 0 && (
                <div className="chart-container">
                  <h4>제품별 실적 (상위 5개)</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart 
                      data={currentAnalysis.analysis_results.performance_data.product_breakdown.slice(0, 5).map(item => ({
                        제품: item.name.length > 10 ? item.name.substring(0, 10) + '...' : item.name,
                        실적: item.amount
                      }))}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="제품" />
                      <YAxis tickFormatter={(value) => `₩${(value/10000).toFixed(0)}만`} />
                      <Tooltip formatter={(value) => `₩${value.toLocaleString()}`} />
                      <Legend />
                      <Bar dataKey="실적">
                        {currentAnalysis.analysis_results.performance_data.product_breakdown.slice(0, 5).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={['#5a4fcf', '#7c68ee', '#9b88f5', '#b8acf6', '#d4ccff'][index]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default EmployeePerformance;