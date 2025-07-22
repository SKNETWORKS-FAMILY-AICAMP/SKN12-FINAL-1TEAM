from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter()

@router.get("/download/{filename}")
async def download_file(filename: str):
    """파일 다운로드 엔드포인트"""
    try:
        # downloads 폴더에서 파일 찾기 (절대 경로 사용)
        current_dir = Path(__file__).parent.parent.parent.parent  # backend 디렉토리
        file_path = current_dir / "downloads" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        # 파일 응답 반환
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 오류: {str(e)}")

@router.get("/files")
async def list_download_files():
    """다운로드 가능한 파일 목록 조회"""
    try:
        # downloads 폴더에서 파일 찾기 (절대 경로 사용)
        current_dir = Path(__file__).parent.parent.parent.parent  # backend 디렉토리
        download_dir = current_dir / "downloads"
        if not download_dir.exists():
            return {"files": []}
        
        files = []
        for file_path in download_dir.glob("*.json"):
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "created": file_path.stat().st_ctime
            })
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 목록 조회 오류: {str(e)}") 