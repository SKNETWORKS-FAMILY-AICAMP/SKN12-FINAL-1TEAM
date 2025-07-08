#!/usr/bin/env pwsh
# Narutalk 의료업계 QA 챗봇 시스템 통합 실행 스크립트

Write-Host "🏥 Narutalk 의료업계 QA 챗봇 시스템을 시작합니다..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Yellow

# 현재 디렉토리 확인
$currentDir = Get-Location
Write-Host "현재 디렉토리: $currentDir" -ForegroundColor Blue

# 가상환경 활성화 확인
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "❌ 가상환경이 없습니다. 먼저 가상환경을 생성하세요." -ForegroundColor Red
    Write-Host "python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# 가상환경 활성화
Write-Host "🔄 가상환경을 활성화합니다..." -ForegroundColor Blue
& .\.venv\Scripts\Activate.ps1

# Node.js 모듈 설치 (처음만)
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Node.js 의존성을 설치합니다..." -ForegroundColor Blue
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm install 실패" -ForegroundColor Red
        exit 1
    }
}

# 백그라운드 작업 리스트
$jobs = @()

try {
    # Django 백엔드 실행
    Write-Host "🌐 Django 백엔드를 시작합니다 (포트 8000)..." -ForegroundColor Blue
    $djangoJob = Start-Job -ScriptBlock {
        param($workingDir)
        Set-Location $workingDir
        & .\.venv\Scripts\python.exe manage.py runserver --noreload
    } -ArgumentList $currentDir
    $jobs += $djangoJob
    
    # FastAPI 마이크로서비스 실행
    Write-Host "⚡ FastAPI 검색 서비스를 시작합니다 (포트 8001)..." -ForegroundColor Blue
    $fastapiJob = Start-Job -ScriptBlock {
        param($workingDir)
        Set-Location "$workingDir\service_8001_search"
        & ..\..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001
    } -ArgumentList $currentDir
    $jobs += $fastapiJob
    
    # React 프론트엔드 실행
    Write-Host "⚛️ React 프론트엔드를 시작합니다 (포트 5173)..." -ForegroundColor Blue
    $reactJob = Start-Job -ScriptBlock {
        param($workingDir)
        Set-Location $workingDir
        npx vite --host 0.0.0.0 --port 5173
    } -ArgumentList $currentDir
    $jobs += $reactJob
    
    # 잠시 대기
    Start-Sleep 5
    
    # 실행 상태 확인
    Write-Host "=================================================" -ForegroundColor Yellow
    Write-Host "🎉 Narutalk 시스템이 성공적으로 시작되었습니다!" -ForegroundColor Green
    Write-Host "📱 접속 URL:" -ForegroundColor Blue
    Write-Host "  - 메인 웹사이트: http://localhost:5173" -ForegroundColor Cyan
    Write-Host "  - Django API: http://localhost:8000" -ForegroundColor Cyan  
    Write-Host "  - FastAPI 서비스: http://localhost:8001" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Yellow
    Write-Host "🛑 종료하려면 Ctrl+C를 누르세요" -ForegroundColor Red
    
    # 무한 대기 (사용자가 Ctrl+C로 종료할 때까지)
    while ($true) {
        Start-Sleep 1
    }
}
catch {
    Write-Host "❌ 오류가 발생했습니다: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    # 정리 작업
    Write-Host "🔄 시스템을 종료합니다..." -ForegroundColor Yellow
    foreach ($job in $jobs) {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -ErrorAction SilentlyContinue
    }
    Write-Host "✅ 모든 서비스가 종료되었습니다." -ForegroundColor Green
} 