# OpenSearchClient: 실전 서비스용 OpenSearch 연동 클래스
from opensearchpy import OpenSearch, exceptions, helpers
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker
import logging
import re
from typing import List, Dict, Any, Optional
from config import settings

class OpenSearchClient:
    def __init__(self):
        try:
            # 중앙화된 설정에서 OpenSearch 설정 가져오기
            opensearch_config = settings.get_opensearch_config()
            host = opensearch_config["host"]
            port = opensearch_config["port"]
            username = opensearch_config.get("username", "admin")
            password = opensearch_config["password"]
            
            # OpenSearch 클라이언트 초기화 (인증 포함)
            self.client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                http_auth=(username, password),
                timeout=30,
                verify_certs=False,  # 개발 환경에서는 SSL 검증 비활성화
                ssl_show_warn=False
            )
            
            if not self.client.ping():
                logging.warning("OpenSearch에 연결할 수 없습니다. 클라이언트는 None으로 설정됩니다.")
                self.client = None
            else:
                logging.info("OpenSearch에 성공적으로 연결되었습니다.")
        except Exception as e:
            logging.warning(f"OpenSearch 클라이언트 초기화 중 오류 발생: {e}")
            self.client = None
        self.model = self.embeddings_model()
        self.embedding_dim = len(self.model.encode("dummy_text"))
        self.reranker = self.rerank_model()

    def _check_client(self) -> bool:
        """클라이언트 초기화 상태를 확인합니다."""
        if not self.client:
            logging.error("OpenSearch 클라이언트가 초기화되지 않았습니다.")
            return False
        return True

    def _format_search_results(self, hits: List[Dict], source_type: str) -> List[Dict[str, Any]]:
        """
        검색 결과를 표준 형식으로 포맷팅합니다.
        
        Args:
            hits: OpenSearch 검색 결과 hits
            source_type: 검색 소스 타입 (예: "opensearch_vector_search")
            
        Returns:
            포맷팅된 검색 결과 리스트
        """
        results = []
        for hit in hits:
            source = hit["_source"]
            results.append({
                "content": source.get("content", ""),
                "metadata": {
                    "document_id": source.get("document_id"),
                    "chunk_index": source.get("chunk_index"),
                    "file_name": source.get("file_name"),
                    "title": source.get("title")
                },
                "score": hit["_score"],
                "rank": len(results) + 1,
                "source": source_type
            })
        return results

    def chunk_text_to_sentences(self, text: str, document_type: str = "report") -> List[Dict[str, Any]]:
        """
        문서 종류에 따라 텍스트를 지능적으로 분할합니다.
        
        Args:
            text: 분할할 텍스트
            document_type: 문서 종류 ("regulation" 또는 "report")
            
        Returns:
            청킹된 문서 리스트 (각 청크는 metadata 포함)
        """
        if document_type == "regulation":
            return self._chunk_regulation_document(text)
        else:
            return self._chunk_report_document(text)

    def _chunk_regulation_document(self, text: str) -> List[Dict[str, Any]]:
        """
        내부 규정 문서를 장/조 기준으로 분할합니다.
        
        Args:
            text: 내부 규정 문서 텍스트
            
        Returns:
            청킹된 규정 문서 리스트
        """
        chunks = []
        
        # 장(Chapter) 패턴 매칭
        chapter_pattern = r'제(\d+)장\s*([^\n]+)'
        article_pattern = r'제(\d+)조\s*\[([^\]]+)\]\s*([^\n]+)'
        
        lines = text.split('\n')
        current_chapter = None
        current_article = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 장(Chapter) 매칭
            chapter_match = re.match(chapter_pattern, line)
            if chapter_match:
                # 이전 청크 저장
                if current_content and current_chapter:
                    chunks.append({
                        "content": '\n'.join(current_content),
                        "chapter": current_chapter,
                        "article": current_article,
                        "metadata": {
                            "type": "regulation",
                            "chapter_num": current_chapter.get("number"),
                            "chapter_title": current_chapter.get("title"),
                            "article_num": current_article.get("number") if current_article else None,
                            "article_title": current_article.get("title") if current_article else None
                        }
                    })
                
                # 새 장 시작
                current_chapter = {
                    "number": chapter_match.group(1),
                    "title": chapter_match.group(2).strip()
                }
                current_article = None
                current_content = [line]
                continue
            
            # 조(Article) 매칭
            article_match = re.match(article_pattern, line)
            if article_match:
                # 이전 청크 저장
                if current_content and current_chapter:
                    chunks.append({
                        "content": '\n'.join(current_content),
                        "chapter": current_chapter,
                        "article": current_article,
                        "metadata": {
                            "type": "regulation",
                            "chapter_num": current_chapter.get("number"),
                            "chapter_title": current_chapter.get("title"),
                            "article_num": current_article.get("number") if current_article else None,
                            "article_title": current_article.get("title") if current_article else None
                        }
                    })
                
                # 새 조 시작
                current_article = {
                    "number": article_match.group(1),
                    "title": article_match.group(2).strip()
                }
                current_content = [line]
                continue
            
            # 일반 내용 추가
            current_content.append(line)
        
        # 마지막 청크 저장
        if current_content and current_chapter:
            chunks.append({
                "content": '\n'.join(current_content),
                "chapter": current_chapter,
                "article": current_article,
                "metadata": {
                    "type": "regulation",
                    "chapter_num": current_chapter.get("number"),
                    "chapter_title": current_chapter.get("title"),
                    "article_num": current_article.get("number") if current_article else None,
                    "article_title": current_article.get("title") if current_article else None
                }
            })
        
        # 빈 청크 제거 및 최소 길이 필터링
        filtered_chunks = []
        for chunk in chunks:
            content = chunk["content"].strip()
            if len(content) > 10:  # 최소 10자 이상
                filtered_chunks.append(chunk)
        
        logging.info(f"내부 규정 문서 청킹 완료: {len(filtered_chunks)}개 청크 생성")
        return filtered_chunks

    def _chunk_report_document(self, text: str) -> List[Dict[str, Any]]:
        """
        보고서 문서를 소제목 기준으로 분할합니다.
        
        Args:
            text: 보고서 문서 텍스트
            
        Returns:
            청킹된 보고서 문서 리스트
        """
        chunks = []
        
        # 소제목 패턴들 (다양한 형식 지원)
        subtitle_patterns = [
            r'^(\d+\.\s*[^\n]+)',  # 1. 제목
            r'^([A-Z]\.\s*[^\n]+)',  # A. 제목
            r'^([가-힣]+\.\s*[^\n]+)',  # 가. 제목
            r'^([^\n]+)\n[-=]{3,}',  # 제목\n--- 또는 ===
            r'^##\s*([^\n]+)',  # ## 제목
            r'^#\s*([^\n]+)',  # # 제목
        ]
        
        lines = text.split('\n')
        current_subtitle = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 소제목 매칭 확인
            subtitle_found = False
            for pattern in subtitle_patterns:
                match = re.match(pattern, line)
                if match:
                    # 이전 청크 저장
                    if current_content and current_subtitle:
                        chunks.append({
                            "content": '\n'.join(current_content),
                            "subtitle": current_subtitle,
                            "metadata": {
                                "type": "report",
                                "subtitle": current_subtitle,
                                "subtitle_level": self._get_subtitle_level(current_subtitle)
                            }
                        })
                    
                    # 새 소제목 시작
                    current_subtitle = match.group(1) if len(match.groups()) > 0 else line
                    current_content = [line]
                    subtitle_found = True
                    break
            
            if not subtitle_found:
                # 일반 내용 추가
                current_content.append(line)
        
        # 마지막 청크 저장
        if current_content and current_subtitle:
            chunks.append({
                "content": '\n'.join(current_content),
                "subtitle": current_subtitle,
                "metadata": {
                    "type": "report",
                    "subtitle": current_subtitle,
                    "subtitle_level": self._get_subtitle_level(current_subtitle)
                }
            })
        
        # 소제목이 없는 경우 문장 단위로 분할
        if not chunks:
            sentences = re.split(r'[.!?]+', text)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) > 20:  # 최소 20자 이상
                    chunks.append({
                        "content": sentence,
                        "subtitle": f"문장 {i+1}",
                        "metadata": {
                            "type": "report",
                            "subtitle": f"문장 {i+1}",
                            "subtitle_level": 0
                        }
                    })
        
        # 빈 청크 제거 및 최소 길이 필터링
        filtered_chunks = []
        for chunk in chunks:
            content = chunk["content"].strip()
            if len(content) > 20:  # 최소 20자 이상
                filtered_chunks.append(chunk)
        
        logging.info(f"보고서 문서 청킹 완료: {len(filtered_chunks)}개 청크 생성")
        return filtered_chunks

    def _get_subtitle_level(self, subtitle: str) -> int:
        """
        소제목의 레벨을 판단합니다.
        
        Args:
            subtitle: 소제목 텍스트
            
        Returns:
            소제목 레벨 (1, 2, 3, ...)
        """
        if re.match(r'^\d+\.', subtitle):
            return 1
        elif re.match(r'^[A-Z]\.', subtitle):
            return 2
        elif re.match(r'^[가-힣]\.', subtitle):
            return 3
        elif subtitle.startswith('##'):
            return 2
        elif subtitle.startswith('#'):
            return 1
        else:
            return 1

    def rerank_model(self):
        try:
            print("BGE Reranker 모델 로드 중...")
            reranker = FlagReranker('dragonkue/bge-reranker-v2-m3-ko', use_fp16=True, use_auth_token=None)
            print("BGE Reranker 모델 로드 완료")
            return reranker
        except Exception as e:
            logging.warning(f"Reranker 모델 로드 실패: {e}")
            return None

    def embeddings_model(self):
        try:
            model = SentenceTransformer("nlpai-lab/KURE-v1")
            vec_dim = len(model.encode("dummy_text"))
            logging.info(f"임베딩 차원: {vec_dim}")
            return model
        except Exception as e:
            logging.warning(f"임베딩 모델 로드 실패: {e}")
            return None

    @property
    def DOCUMENT_INDEX_MAPPING(self) -> Dict[str, Any]:
        return {
            "settings": {
                "index": {
                    "knn": True
                }
            },
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": self.embedding_dim,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "lucene"
                        }
                    },
                    "file_name": {"type": "keyword"},
                    "title": {"type": "text"},
                    "document_type": {"type": "keyword"},
                    # 내부 규정 관련 필드
                    "chapter_num": {"type": "keyword"},
                    "chapter_title": {"type": "text"},
                    "article_num": {"type": "keyword"},
                    "article_title": {"type": "text"},
                    # 보고서 관련 필드
                    "subtitle": {"type": "text"},
                    "subtitle_level": {"type": "integer"}
                }
            }
        }

    def create_index(self, index_name: str, mapping: Optional[Dict[str, Any]] = None) -> bool:
        """
        인덱스를 생성합니다.
        
        Args:
            index_name: 생성할 인덱스 이름
            mapping: 인덱스 매핑 (None이면 기본 매핑 사용)
            
        Returns:
            인덱스 생성 성공 여부
        """
        if not self._check_client():
            return False
        
        try:
            if not self.client.indices.exists(index=index_name):
                mapping_to_use = mapping or self.DOCUMENT_INDEX_MAPPING
                self.client.indices.create(index=index_name, body=mapping_to_use)
                logging.info(f"'{index_name}' 인덱스를 매핑과 함께 생성했습니다.")
                return True
            logging.info(f"'{index_name}' 인덱스가 이미 존재합니다.")
            return True
        except exceptions.OpenSearchException as e:
            logging.error(f"인덱스 생성 중 오류 발생: {e}")
            return False

    def create_index_with_mapping(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """사용자 정의 매핑으로 인덱스를 생성합니다."""
        return self.create_index(index_name, mapping)

    def create_index_if_not_exists(self, index_name: str) -> bool:
        """기본 매핑으로 인덱스를 생성합니다."""
        return self.create_index(index_name)

    def index_document(self, index_name: str, document: Dict[str, Any], refresh: bool = False) -> Optional[Dict[str, Any]]:
        if not self._check_client():
            return None
        try:
            params = {"refresh": "true" if refresh else "false"}
            response = self.client.index(index=index_name, body=document, params=params)
            logging.info(f"'{index_name}' 인덱스에 문서 ID '{response['_id']}'로 색인되었습니다.")
            return response
        except exceptions.RequestError as e:
            logging.error(f"문서 색인 중 오류 발생 (잘못된 요청): {e}")
        except exceptions.OpenSearchException as e:
            logging.error(f"문서 색인 중 예외적 오류 발생: {e}")
        return None

    def bulk_index_documents(self, index_name: str, documents: List[Dict[str, Any]], refresh: bool = False) -> bool:
        if not self._check_client():
            return False
        actions = [
            {"_index": index_name, "_source": doc}
            for doc in documents
        ]
        try:
            success, failed = helpers.bulk(self.client, actions, refresh=refresh)
            logging.info(f"Bulk 작업 완료: 성공 {success}건, 실패 {len(failed)}건")
            return not failed
        except exceptions.OpenSearchException as e:
            logging.error(f"Bulk 색인 중 예외적 오류 발생: {e}")
            return False

    def search_document(self, index_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self._check_client():
            return []
        try:
            response = self.client.search(index=index_name, body=query)
            hits = response["hits"]["hits"]
            logging.info(f"'{index_name}' 인덱스에서 {len(hits)}개의 문서를 찾았습니다.")
            return [{"score": hit["_score"], "source": hit["_source"]} for hit in hits]
        except exceptions.NotFoundError:
            logging.warning(f"검색 실패: '{index_name}' 인덱스가 존재하지 않습니다.")
        except exceptions.RequestError as e:
            logging.error(f"문서 검색 중 오류 발생 (잘못된 쿼리): {e}")
        except exceptions.OpenSearchException as e:
            logging.error(f"문서 검색 중 예외적 오류 발생: {e}")
        return []

    def vector_search(self, index_name: str, query_vector: List[float], top_k: int = 5, query_text: str = None) -> List[Dict[str, Any]]:
        """
        벡터 검색을 수행하고 reranker를 적용합니다.
        
        Args:
            index_name: 검색할 인덱스 이름
            query_vector: 쿼리 벡터
            top_k: 반환할 최대 문서 수
            query_text: reranker를 위한 쿼리 텍스트 (None이면 reranker 미적용)
            
        Returns:
            검색 결과 리스트
        """
        if not self._check_client():
            return []
        
        try:
            # 더 많은 후보를 검색 (reranker 적용을 위해)
            candidate_k = min(top_k * 3, 50)  # 최대 50개 후보 검색
            
            # KNN 검색 쿼리 구성
            query = {
                "size": candidate_k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": candidate_k
                        }
                    }
                },
                "_source": ["document_id", "chunk_index", "content", "file_name", "title"]
            }
            
            response = self.client.search(index=index_name, body=query)
            hits = response["hits"]["hits"]
            
            # 기본 검색 결과 포맷팅
            results = self._format_search_results(hits, "opensearch_vector_search")
            
            # Reranker 적용 (쿼리 텍스트가 제공된 경우)
            if query_text and self.reranker and len(results) > 0:
                try:
                    # Reranker를 위한 데이터 준비
                    pairs = [(query_text, result["content"]) for result in results]
                    
                    # Reranker 점수 계산
                    scores = self.reranker.compute_score(pairs)
                    
                    # 점수와 결과를 결합하여 재정렬
                    for i, (result, score) in enumerate(zip(results, scores)):
                        result["reranker_score"] = float(score)
                        result["final_score"] = (result["score"] + float(score)) / 2  # 벡터 점수와 reranker 점수 평균
                    
                    # 최종 점수로 재정렬
                    results.sort(key=lambda x: x["final_score"], reverse=True)
                    
                    # 상위 top_k개만 반환
                    results = results[:top_k]
                    
                    logging.info(f"Reranker 적용 완료: {len(results)}개 문서 재정렬됨")
                    
                except Exception as e:
                    logging.warning(f"Reranker 적용 중 오류 발생: {e}")
                    # Reranker 실패 시 원본 결과 반환 (상위 top_k개)
                    results = results[:top_k]
            else:
                # Reranker 미적용 시 상위 top_k개만 반환
                results = results[:top_k]
            
            logging.info(f"벡터 검색 완료: {len(results)}개 문서 찾음")
            return results
            
        except exceptions.OpenSearchException as e:
            logging.error(f"벡터 검색 중 오류 발생: {e}")
            return []

    def index_document_chunks(self, index_name: str, doc_id: int, doc_title: str, file_name: str, text: str, document_type: str = "report") -> bool:
        """
        문서를 청킹하여 OpenSearch에 인덱싱합니다.
        
        Args:
            index_name: 인덱스 이름
            doc_id: 문서 ID
            doc_title: 문서 제목
            file_name: 파일명
            text: 원본 텍스트
            document_type: 문서 종류 ("regulation" 또는 "report")
            
        Returns:
            인덱싱 성공 여부
        """
        if not self._check_client():
            return False
        
        try:
            # 인덱스가 없으면 생성
            self.create_index_if_not_exists(index_name)
            
            # 문서 청킹 수행
            chunks = self.chunk_text_to_sentences(text, document_type)
            
            if not chunks:
                logging.warning(f"문서 {doc_id}에서 청킹할 내용을 찾을 수 없습니다.")
                return False
            
            # 청킹된 문서를 벡터로 변환하여 인덱싱
            documents = []
            for i, chunk in enumerate(chunks):
                content = chunk["content"]
                if content.strip():  # 빈 내용 제외
                    # 내용을 벡터로 변환
                    embedding = self.model.encode(content)
                    
                    # 문서 정보 구성
                    document = {
                        "document_id": doc_id,
                        "chunk_index": i,
                        "content": content,
                        "embedding": embedding.tolist(),
                        "file_name": file_name,
                        "title": doc_title,
                        "document_type": document_type
                    }
                    
                    # 문서 종류별 메타데이터 추가
                    if document_type == "regulation":
                        metadata = chunk.get("metadata", {})
                        document.update({
                            "chapter_num": metadata.get("chapter_num"),
                            "chapter_title": metadata.get("chapter_title"),
                            "article_num": metadata.get("article_num"),
                            "article_title": metadata.get("article_title")
                        })
                    else:  # report
                        metadata = chunk.get("metadata", {})
                        document.update({
                            "subtitle": metadata.get("subtitle"),
                            "subtitle_level": metadata.get("subtitle_level", 1)
                        })
                    
                    documents.append(document)
            
            # Bulk 인덱싱 수행
            success = self.bulk_index_documents(index_name, documents, refresh=True)
            
            if success:
                logging.info(f"문서 {doc_id}의 {len(documents)}개 청킹을 OpenSearch에 저장했습니다. (문서 타입: {document_type})")
            else:
                logging.error(f"문서 {doc_id}의 청킹 인덱싱에 실패했습니다.")
            
            return success
            
        except Exception as e:
            logging.error(f"문서 청킹 인덱싱 실패: {e}")
            return False

    def delete_document_chunks(self, index_name: str, document_id: int) -> bool:
        """
        특정 문서의 모든 청킹을 삭제합니다.
        
        Args:
            index_name: 인덱스 이름
            document_id: 삭제할 문서 ID
            
        Returns:
            삭제 성공 여부
        """
        if not self._check_client():
            return False
        
        try:
            # 문서 ID로 모든 청킹 삭제
            query = {
                "query": {
                    "term": {
                        "document_id": document_id
                    }
                }
            }
            
            response = self.client.delete_by_query(index=index_name, body=query)
            deleted_count = response.get("deleted", 0)
            
            logging.info(f"문서 {document_id}의 {deleted_count}개 청킹을 OpenSearch에서 삭제했습니다.")
            return True
            
        except exceptions.OpenSearchException as e:
            logging.error(f"문서 청킹 삭제 실패: {e}")
            return False

    def hybrid_search(self, index_name: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (벡터 + 텍스트 검색)을 수행하고 reranker를 적용합니다.
        
        Args:
            index_name: 검색할 인덱스 이름
            query_text: 검색 쿼리 텍스트
            top_k: 반환할 최대 문서 수
            
        Returns:
            검색 결과 리스트
        """
        if not self._check_client():
            return []
        
        try:
            # 쿼리 텍스트를 벡터로 변환
            query_vector = self.model.encode(query_text).tolist()
            
            # 더 많은 후보를 검색 (reranker 적용을 위해)
            candidate_k = min(top_k * 3, 50)  # 최대 50개 후보 검색
            
            # 하이브리드 검색 쿼리 구성
            query = {
                "size": candidate_k,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_vector,
                                        "k": candidate_k
                                    }
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query_text,
                                    "fields": ["content", "title"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "_source": ["document_id", "chunk_index", "content", "file_name", "title"]
            }
            
            response = self.client.search(index=index_name, body=query)
            hits = response["hits"]["hits"]
            
            # 기본 검색 결과 포맷팅
            results = self._format_search_results(hits, "opensearch_hybrid_search")
            
            # Reranker 적용
            if self.reranker and len(results) > 0:
                try:
                    # Reranker를 위한 데이터 준비
                    pairs = [(query_text, result["content"]) for result in results]
                    
                    # Reranker 점수 계산
                    scores = self.reranker.compute_score(pairs)
                    
                    # 점수와 결과를 결합하여 재정렬
                    for i, (result, score) in enumerate(zip(results, scores)):
                        result["reranker_score"] = float(score)
                        result["final_score"] = (result["score"] + float(score)) / 2  # 벡터 점수와 reranker 점수 평균
                    
                    # 최종 점수로 재정렬
                    results.sort(key=lambda x: x["final_score"], reverse=True)
                    
                    # 상위 top_k개만 반환
                    results = results[:top_k]
                    
                    logging.info(f"하이브리드 검색 + Reranker 적용 완료: {len(results)}개 문서 재정렬됨")
                    
                except Exception as e:
                    logging.warning(f"Reranker 적용 중 오류 발생: {e}")
                    # Reranker 실패 시 원본 결과 반환 (상위 top_k개)
                    results = results[:top_k]
            else:
                # Reranker 미적용 시 상위 top_k개만 반환
                results = results[:top_k]
            
            logging.info(f"하이브리드 검색 완료: {len(results)}개 문서 찾음")
            return results
            
        except exceptions.OpenSearchException as e:
            logging.error(f"하이브리드 검색 중 오류 발생: {e}")
            return []

# 전역 OpenSearch 클라이언트 인스턴스 생성
opensearch_client = OpenSearchClient() 