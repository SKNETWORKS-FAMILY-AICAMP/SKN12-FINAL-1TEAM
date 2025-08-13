import React, { useState, useEffect } from 'react';
import { 
  getEmployeeList, 
  getEmployeePerformance, 
  getEmployeeTarget,
  analyzeEmployeePerformance 
} from '../services/api';
import './EmployeePerformance.css';

const EmployeePerformance = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [startPeriod, setStartPeriod] = useState('202401');
  const [endPeriod, setEndPeriod] = useState('202409');
  const [performanceData, setPerformanceData] = useState(null);
  const [targetData, setTargetData] = useState(null);
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('performance');

  // 컴포넌트 마운트 시 직원 목록 가져오기
  useEffect(() => {
    fetchEmployeeList();
  }, []);

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

  const handlePerformanceSearch = async () => {
    if (!selectedEmployee) {
      setError('직원을 선택해주세요.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const perfData = await getEmployeePerformance(selectedEmployee, startPeriod, endPeriod);
      setPerformanceData(perfData);
      setActiveTab('performance');
    } catch (error) {
      console.error('실적 조회 실패:', error);
      setError('실적 조회에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleTargetSearch = async () => {
    if (!selectedEmployee) {
      setError('직원을 선택해주세요.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const targetData = await getEmployeeTarget(selectedEmployee, startPeriod, endPeriod);
      setTargetData(targetData);
      setActiveTab('target');
    } catch (error) {
      console.error('목표 조회 실패:', error);
      setError('목표 조회에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalysis = async () => {
    if (!analysisQuery) {
      setError('분석할 내용을 입력해주세요.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await analyzeEmployeePerformance({
        query: analysisQuery,
        employee_name: selectedEmployee || null
      });
      setAnalysisResult(result);
      setActiveTab('analysis');
    } catch (error) {
      console.error('분석 실패:', error);
      setError('분석에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW'
    }).format(amount);
  };

  return (
    <div className="employee-performance">
      <h1>직원 실적 관리</h1>

      <div className="search-section">
        <div className="search-controls">
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

          <div className="control-group">
            <label>시작 기간</label>
            <input
              type="text"
              value={startPeriod}
              onChange={(e) => setStartPeriod(e.target.value)}
              placeholder="YYYYMM"
              className="period-input"
            />
          </div>

          <div className="control-group">
            <label>종료 기간</label>
            <input
              type="text"
              value={endPeriod}
              onChange={(e) => setEndPeriod(e.target.value)}
              placeholder="YYYYMM"
              className="period-input"
            />
          </div>

          <div className="button-group">
            <button onClick={handlePerformanceSearch} className="search-btn">
              실적 조회
            </button>
            <button onClick={handleTargetSearch} className="search-btn">
              목표 대비 조회
            </button>
          </div>
        </div>

        <div className="analysis-controls">
          <div className="control-group full-width">
            <label>자연어 분석</label>
            <input
              type="text"
              value={analysisQuery}
              onChange={(e) => setAnalysisQuery(e.target.value)}
              placeholder="예: 최수아의 2024년 3분기 실적을 분석해주세요"
              className="analysis-input"
            />
          </div>
          <button onClick={handleAnalysis} className="analysis-btn">
            분석하기
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading && (
        <div className="loading-message">
          데이터를 불러오는 중...
        </div>
      )}

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          실적 데이터
        </button>
        <button 
          className={`tab ${activeTab === 'target' ? 'active' : ''}`}
          onClick={() => setActiveTab('target')}
        >
          목표 대비
        </button>
        <button 
          className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          분석 결과
        </button>
      </div>

      <div className="results-section">
        {activeTab === 'performance' && performanceData && (
          <div className="performance-results">
            <div className="summary-card">
              <h3>실적 요약</h3>
              <div className="summary-grid">
                <div className="summary-item">
                  <span className="label">총 실적</span>
                  <span className="value">{formatCurrency(performanceData.summary.total_amount)}</span>
                </div>
                <div className="summary-item">
                  <span className="label">평균 실적</span>
                  <span className="value">{formatCurrency(performanceData.summary.average_amount)}</span>
                </div>
                <div className="summary-item">
                  <span className="label">데이터 개수</span>
                  <span className="value">{performanceData.summary.total_count}개월</span>
                </div>
              </div>
            </div>

            <div className="detail-grid">
              <div className="monthly-data">
                <h3>월별 실적</h3>
                <table>
                  <thead>
                    <tr>
                      <th>월</th>
                      <th>실적</th>
                    </tr>
                  </thead>
                  <tbody>
                    {performanceData.monthly_data.slice(0, 5).map((item, index) => (
                      <tr key={index}>
                        <td>{item.month}</td>
                        <td>{formatCurrency(item.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="product-data">
                <h3>제품별 실적</h3>
                <table>
                  <thead>
                    <tr>
                      <th>제품</th>
                      <th>실적</th>
                      <th>비율</th>
                    </tr>
                  </thead>
                  <tbody>
                    {performanceData.product_data.map((item, index) => (
                      <tr key={index}>
                        <td>{item.product}</td>
                        <td>{formatCurrency(item.amount)}</td>
                        <td>{item.percentage}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'target' && targetData && (
          <div className="target-results">
            <div className="summary-card">
              <h3>목표 달성 요약</h3>
              <div className="summary-grid">
                <div className="summary-item">
                  <span className="label">총 목표</span>
                  <span className="value">{formatCurrency(targetData.summary.total_target)}</span>
                </div>
                <div className="summary-item">
                  <span className="label">총 실적</span>
                  <span className="value">{formatCurrency(targetData.summary.total_actual)}</span>
                </div>
                <div className="summary-item">
                  <span className="label">달성률</span>
                  <span className="value achievement">{targetData.summary.overall_achievement}%</span>
                </div>
                <div className="summary-item">
                  <span className="label">평가 등급</span>
                  <span className="value grade">{targetData.summary.grade}</span>
                </div>
              </div>
            </div>

            <div className="monthly-target">
              <h3>월별 목표 대비 실적</h3>
              <table>
                <thead>
                  <tr>
                    <th>월</th>
                    <th>목표</th>
                    <th>실적</th>
                    <th>달성률</th>
                  </tr>
                </thead>
                <tbody>
                  {targetData.target_data.map((item, index) => (
                    <tr key={index}>
                      <td>{item.month}</td>
                      <td>{formatCurrency(item.target)}</td>
                      <td>{formatCurrency(item.actual)}</td>
                      <td className={item.achievement_rate >= 100 ? 'achieved' : 'not-achieved'}>
                        {item.achievement_rate}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && analysisResult && (
          <div className="analysis-results">
            <div className="analysis-header">
              <h3>실적 분석 결과</h3>
              <div className="analysis-summary">
                <span className="employee-name">{analysisResult.employee_name}</span>
                <span className="period">{analysisResult.period}</span>
                <span className={`grade grade-${analysisResult.summary.grade}`}>
                  {analysisResult.summary.grade}등급
                </span>
              </div>
            </div>

            <div className="analysis-report">
              <h4>상세 분석 보고서</h4>
              <div className="report-content">
                {analysisResult.report.split('\n').map((paragraph, index) => (
                  <p key={index}>{paragraph}</p>
                ))}
              </div>
            </div>

            {analysisResult.analysis_results && (
              <div className="analysis-details">
                <div className="detail-card">
                  <h4>종합 평가</h4>
                  <div className="evaluation">
                    <div className="eval-item">
                      <span>총점</span>
                      <strong>{analysisResult.analysis_results.comprehensive_evaluation.total_score}점</strong>
                    </div>
                    <div className="eval-item">
                      <span>등급</span>
                      <strong>{analysisResult.analysis_results.comprehensive_evaluation.grade}</strong>
                    </div>
                    <div className="eval-item">
                      <span>평가</span>
                      <strong>{analysisResult.analysis_results.comprehensive_evaluation.grade_description}</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmployeePerformance;