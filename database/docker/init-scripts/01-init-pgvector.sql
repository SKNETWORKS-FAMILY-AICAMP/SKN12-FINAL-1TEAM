-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 확장이 제대로 설치되었는지 확인
SELECT * FROM pg_extension WHERE extname = 'vector'; 