import React from 'react';
import ProcessProgressBar from './ProcessProgressBar';
import './BatchProcessProgressBar.css';

const BatchProcessProgressBar = ({
  totalFiles,
  currentFileIndex,
  successCount,
  failCount,
  currentFileName,
  currentStep,
  documentType,
  isCompleted,
  onConfirm,
  failedFiles = []
}) => {
  // 성공한 파일 수를 기반으로 진행률 계산 (현재 처리 중인 파일도 부분 반영)
  const completedCount = successCount + failCount;
  const overallProgress = totalFiles > 0 ? (completedCount / totalFiles) * 100 : 0;
  
  console.log('BatchProcessProgressBar props:', {
    totalFiles,
    currentFileIndex,
    successCount,
    failCount,
    completedCount,
    overallProgress
  });
  
  // 색상 계산 (노란색 → 초록색)
  const getProgressColor = (progress) => {
    const r = Math.round(255 - (progress * 1.27)); // 255 → 128
    const g = Math.round(200 + (progress * 0.55)); // 200 → 255
    const b = 0;
    return `rgb(${r}, ${g}, ${b})`;
  };

  return (
    <div className="batch-process-container">
      {/* 전체 진행률 바 */}
      <div className="overall-progress-section">
        <div className="overall-progress-header">
          <h3>📦 전체 업로드 진행률</h3>
          <div className="overall-stats">
            <span className="stat-item success">
              ✅ 성공: {successCount}
            </span>
            <span className="stat-item processing">
              ⏳ 처리중: {currentFileIndex > 0 && currentFileIndex <= totalFiles ? 1 : 0}
            </span>
            <span className="stat-item failed">
              ❌ 실패: {failCount}
            </span>
            <span className="stat-item total">
              📄 전체: {totalFiles}
            </span>
          </div>
        </div>
        
        <div className="overall-progress-bar-container">
          <div 
            className="overall-progress-bar"
            style={{
              width: `${overallProgress}%`,
              background: `linear-gradient(90deg, ${getProgressColor(0)}, ${getProgressColor(overallProgress)})`
            }}
          >
            <div className="progress-bar-shine"></div>
          </div>
          <div className="progress-text">
            {completedCount}/{totalFiles} 파일 ({Math.round(overallProgress)}%)
          </div>
        </div>

        {/* 파일별 상태 표시 */}
        <div className="files-status-grid">
          {Array.from({ length: totalFiles }).map((_, index) => {
            let status = 'pending';
            // 성공/실패한 파일 수를 기반으로 상태 결정
            const completedCount = successCount + failCount;
            if (index < completedCount) {
              // failedFiles 배열에 파일 인덱스가 있으면 failed, 아니면 success
              status = failedFiles.includes(index + 1) ? 'failed' : 'success';
            } else if (index === completedCount && currentFileIndex > completedCount) {
              // 현재 처리 중인 파일
              status = 'processing';
            }
            
            return (
              <div key={index} className={`file-status-dot ${status}`} title={`파일 ${index + 1}`}>
                {status === 'success' && '✓'}
                {status === 'failed' && '✗'}
                {status === 'processing' && <div className="mini-spinner"></div>}
              </div>
            );
          })}
        </div>
      </div>

      {/* 현재 파일 프로세스 바 */}
      {currentFileName && !isCompleted && (
        <div className="current-file-section">
          <h4>현재 처리 중인 파일</h4>
          <ProcessProgressBar
            currentStep={currentStep}
            documentType={documentType}
            fileName={currentFileName}
            isCompleted={false}
          />
        </div>
      )}

      {/* 완료 오버레이 */}
      {isCompleted && (
        <div className="batch-complete-overlay">
          <div className="batch-complete-content">
            <div className="complete-icon">🎉</div>
            <h2>배치 업로드 완료!</h2>
            <div className="batch-summary">
              <div className="summary-item success">
                <span className="summary-icon">✅</span>
                <span className="summary-label">성공</span>
                <span className="summary-value">{successCount}개</span>
              </div>
              {failCount > 0 && (
                <div className="summary-item failed">
                  <span className="summary-icon">❌</span>
                  <span className="summary-label">실패</span>
                  <span className="summary-value">{failCount}개</span>
                </div>
              )}
              <div className="summary-item total">
                <span className="summary-icon">📊</span>
                <span className="summary-label">전체</span>
                <span className="summary-value">{totalFiles}개</span>
              </div>
            </div>
            {failCount > 0 && (
              <p className="fail-message">
                일부 파일이 업로드에 실패했습니다. 로그를 확인해주세요.
              </p>
            )}
            <button className="batch-confirm-button" onClick={onConfirm}>
              확인
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchProcessProgressBar;