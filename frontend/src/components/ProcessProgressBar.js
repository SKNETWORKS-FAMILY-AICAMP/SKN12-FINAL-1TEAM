import React from 'react';
import './ProcessProgressBar.css';

const ProcessProgressBar = ({ 
  processSteps, 
  currentStep, 
  isCompleted, 
  onConfirm,
  documentType,
  fileName
}) => {
  // 문서 타입별 프로세스 단계 정의
  const getProcessSteps = (docType) => {
    const commonSteps = [
      { id: 'validating', label: '파일 검증', icon: '🔍' },
      { id: 'validated', label: '검증 완료', icon: '✓' },
      { id: 'detecting', label: '타입 감지', icon: '📋' },
      { id: 'detected', label: '타입 확인', icon: '✓' }
    ];

    const tableSteps = [
      ...commonSteps,
      { id: 'classifying', label: 'Text2SQL 분류', icon: '🤖' },
      { id: 'classified', label: '분류 완료', icon: '✓' }
    ];

    const textSteps = [
      ...commonSteps,
      { id: 'analyzing', label: '문서 분석', icon: '📊' },
      { id: 'analyzed', label: '분석 완료', icon: '✓' },
      { id: 'chunking', label: '청킹 처리', icon: '✂️' },
      { id: 'relation_analysis', label: '관계 분석', icon: '🔗' }
    ];

    const finalSteps = [
      { id: 'summarizing', label: '요약 생성', icon: '📝' },
      { id: 'summarized', label: '요약 완료', icon: '✓' },
      { id: 'uploading', label: 'S3 업로드', icon: '☁️' },
      { id: 'uploaded', label: '업로드 완료', icon: '✓' },
      { id: 'saving', label: 'DB 저장', icon: '💾' },
      { id: 'saved', label: '저장 완료', icon: '✓' }
    ];

    if (docType === 'table') {
      return [...tableSteps, ...finalSteps];
    } else if (docType === 'text') {
      return [...textSteps, ...finalSteps];
    }
    
    // 타입이 아직 결정되지 않은 경우 기본 단계만 표시
    return commonSteps;
  };

  const steps = processSteps || getProcessSteps(documentType);
  
  // 현재 단계의 인덱스 찾기
  const currentStepIndex = steps.findIndex(step => step.id === currentStep);
  const progress = currentStepIndex >= 0 ? ((currentStepIndex + 1) / steps.length) * 100 : 0;

  // 색상 계산 (노란색 → 초록색)
  const getProgressColor = (progress) => {
    const r = Math.round(255 - (progress * 1.27)); // 255 → 128
    const g = Math.round(200 + (progress * 0.55)); // 200 → 255
    const b = 0;
    return `rgb(${r}, ${g}, ${b})`;
  };

  // 단계 상태 확인
  const getStepStatus = (stepIndex) => {
    if (stepIndex < currentStepIndex) return 'completed';
    if (stepIndex === currentStepIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="process-progress-container">
      {fileName && (
        <div className="process-file-name">
          📄 {fileName}
        </div>
      )}
      
      <div className="process-steps">
        {steps.map((step, index) => {
          const status = getStepStatus(index);
          const isActive = status === 'active';
          const isCompleted = status === 'completed';
          
          return (
            <div key={step.id} className={`process-step ${status}`}>
              <div className="step-connector">
                {index > 0 && (
                  <div 
                    className={`connector-line ${isCompleted || isActive ? 'filled' : ''}`}
                    style={{
                      background: isCompleted || isActive 
                        ? getProgressColor((index / steps.length) * 100)
                        : '#e0e0e0'
                    }}
                  />
                )}
              </div>
              
              <div className="step-content">
                <div className={`step-icon ${status}`}>
                  {isActive && !step.id.includes('ed') ? (
                    <div className="spinner"></div>
                  ) : isCompleted || step.id.includes('ed') ? (
                    <span className="check-icon">✓</span>
                  ) : (
                    <span className="step-emoji">{step.icon}</span>
                  )}
                </div>
                <div className="step-label">{step.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="process-bar-container">
        <div 
          className="process-bar"
          style={{
            width: `${progress}%`,
            background: `linear-gradient(90deg, ${getProgressColor(0)}, ${getProgressColor(progress)})`
          }}
        >
          <div className="process-bar-glow"></div>
        </div>
      </div>

      <div className="process-info">
        <span className="progress-percentage">{Math.round(progress)}%</span>
        {currentStep && (
          <span className="current-step-text">
            {steps.find(s => s.id === currentStep)?.label || currentStep}
          </span>
        )}
      </div>

      {isCompleted && (
        <div className="process-complete-overlay">
          <div className="complete-content">
            <div className="complete-icon">✅</div>
            <h3>업로드 완료!</h3>
            <p>문서가 성공적으로 업로드되었습니다.</p>
            <button className="confirm-button" onClick={onConfirm}>
              확인
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessProgressBar;