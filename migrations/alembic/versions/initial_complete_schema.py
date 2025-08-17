"""Initial complete schema with all tables

Revision ID: initial_complete_schema
Revises: 
Create Date: 2025-01-10 08:00:00.000000

"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ENUM
from pgvector.sqlalchemy import VECTOR

logger = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision: str = 'initial_complete_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with complete schema"""
    
    # ========================================
    # 1. Extensions
    # ========================================
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # ========================================
    # 2. Enum Types
    # ========================================
    
    # NewsType enum for news table - 존재 확인 후 생성
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'newstype')")
    ).scalar()
    
    if not result:
        try:
            op.execute("CREATE TYPE newstype AS ENUM ('general', 'pharmaceutical')")
            logger.info("NewsType enum created successfully")
        except Exception as e:
            logger.warning(f"Failed to create NewsType enum: {e}")
    else:
        logger.info("NewsType enum already exists, skipping creation")
    
    # ========================================
    # 3. Base Tables (No Foreign Keys)
    # ========================================
    
    # employees 테이블 (계정 정보)
    op.create_table('employees',
        sa.Column('employee_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('employee_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_employees_employee_id'), 'employees', ['employee_id'], unique=False)
    
    # branches 테이블 (지점 정보) - 모델과 일치
    op.create_table('branches',
        sa.Column('branch_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('headquarters', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('branch_name', sa.String(length=100), nullable=False),
        sa.Column('contact_number', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'active'"), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('branch_id'),
        sa.UniqueConstraint('branch_name')
    )
    op.create_index(op.f('ix_branches_branch_id'), 'branches', ['branch_id'], unique=False)
    
    # customers 테이블 (고객 정보) - 모델과 일치
    op.create_table('customers',
        sa.Column('customer_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('doctor_name', sa.String(), nullable=True),
        sa.Column('contact_number', sa.String(), nullable=True),
        sa.Column('customer_grade', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('is_auto_created', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('approval_status', sa.String(), server_default=sa.text("'pending'"), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_notes', sa.String(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('customer_id'),
        sa.UniqueConstraint('customer_name', 'address', name='uq_customer_name_address')
    )
    op.create_index(op.f('ix_customers_customer_id'), 'customers', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customers_customer_name'), 'customers', ['customer_name'], unique=False)
    
    # products 테이블 (제품 정보) - 모델과 일치
    op.create_table('products',
        sa.Column('product_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('is_auto_created', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('approval_status', sa.String(), server_default=sa.text("'pending'"), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('product_id')
    )
    op.create_index(op.f('ix_products_product_id'), 'products', ['product_id'], unique=False)
    op.create_index(op.f('ix_products_product_name'), 'products', ['product_name'], unique=False)
    
    # documents 테이블 (문서 메타데이터) - 모델과 일치
    op.create_table('documents',
        sa.Column('doc_id', sa.String(36), nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=False),
        sa.Column('doc_title', sa.String(), nullable=False),
        sa.Column('doc_type', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('processing_status', sa.String(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['uploader_id'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('doc_id')
    )
    op.create_index(op.f('ix_documents_doc_id'), 'documents', ['doc_id'], unique=False)
    
    # table_descriptions 테이블 (벡터 검색용)
    op.create_table('table_descriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('columns', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding', VECTOR(1536), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('table_name', name='uq_table_descriptions_table_name')
    )
    
    # 벡터 인덱스 생성
    op.execute('CREATE INDEX idx_table_descriptions_embedding ON table_descriptions USING ivfflat (embedding vector_cosine_ops)')
    
    # news 테이블 (뉴스 정보) - 테이블 존재 여부 체크
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    if 'news' not in existing_tables:
        try:
            op.create_table('news',
                sa.Column('news_id', sa.Integer(), autoincrement=True, nullable=False),
                sa.Column('title', sa.String(length=1000), nullable=False),
                sa.Column('content', sa.Text(), nullable=True),
                sa.Column('news_type', ENUM('general', 'pharmaceutical', name='newstype', create_type=False), nullable=False),
                sa.Column('source', sa.String(length=200), nullable=True),
                sa.Column('author', sa.String(length=100), nullable=True),
                sa.Column('published_date', sa.Date(), nullable=True),
                sa.Column('url', sa.String(length=1500), nullable=True),
                sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
                sa.PrimaryKeyConstraint('news_id'),
                sa.UniqueConstraint('url')
            )
            op.create_index(op.f('ix_news_news_id'), 'news', ['news_id'], unique=False)
            op.create_index(op.f('ix_news_news_type'), 'news', ['news_type'], unique=False)
            op.create_index(op.f('ix_news_published_date'), 'news', ['published_date'], unique=False)
            logger.info("News table created successfully")
        except Exception as e:
            logger.warning(f"Failed to create news table: {e}")
    
    # laws 테이블 (법령 정보)
    if 'laws' not in existing_tables:
        try:
            op.create_table('laws',
                sa.Column('law_id', sa.Integer(), autoincrement=True, nullable=False),
                sa.Column('title', sa.String(length=1000), nullable=False),
                sa.Column('law_number', sa.String(length=100), nullable=True),
                sa.Column('content', sa.Text(), nullable=True),
                sa.Column('article', sa.String(length=100), nullable=True),
                sa.Column('url', sa.String(length=1000), nullable=True),
                sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
                sa.PrimaryKeyConstraint('law_id'),
                sa.UniqueConstraint('law_number', 'article', name='uq_law_number_article')
            )
            op.create_index(op.f('ix_laws_law_id'), 'laws', ['law_id'], unique=False)
            op.create_index(op.f('ix_laws_article'), 'laws', ['article'], unique=False)
            logger.info("Laws table created successfully")
        except Exception as e:
            logger.warning(f"Failed to create laws table: {e}")
    
    # ========================================
    # 4. Dependent Tables (With Foreign Keys)
    # ========================================
    
    # employee_info 테이블 (인사 정보) - 모델과 일치
    op.create_table('employee_info',
        sa.Column('employee_info_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('employee_number', sa.String(), nullable=True),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('contact_number', sa.String(), nullable=True),
        sa.Column('base_salary', sa.Integer(), nullable=True),
        sa.Column('incentive_pay', sa.Integer(), nullable=True),
        sa.Column('avg_monthly_budget', sa.Integer(), nullable=True),
        sa.Column('latest_evaluation', sa.String(), nullable=True),
        sa.Column('responsibilities', sa.String(), nullable=True),
        sa.Column('is_auto_created', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('approval_status', sa.String(), server_default=sa.text("'pending'"), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['employees.employee_id'], ),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.branch_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('employee_info_id'),
        sa.UniqueConstraint('employee_number')
    )
    
    # employee_performance 테이블 (직원 실적 목표)
    op.create_table('employee_performance',
        sa.Column('performance_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('year_month', sa.Date(), nullable=False),
        sa.Column('target_amount', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_info.employee_info_id'], ),
        sa.PrimaryKeyConstraint('performance_id'),
        sa.UniqueConstraint('employee_id', 'year_month', name='uq_employee_yearmonth')
    )
    op.create_index(op.f('ix_employee_performance_performance_id'), 'employee_performance', ['performance_id'], unique=False)
    
    # sales_records 테이블 (매출 기록) - 모델과 일치
    op.create_table('sales_records',
        sa.Column('record_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sale_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('sale_date', sa.Date(), nullable=False),
        # used_budget 컬럼 제거 - customer_monthly_status로 이동
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_info.employee_info_id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ),
        sa.PrimaryKeyConstraint('record_id')
    )
    op.create_index(op.f('ix_sales_records_customer_id'), 'sales_records', ['customer_id'], unique=False)
    op.create_index(op.f('ix_sales_records_employee_id'), 'sales_records', ['employee_id'], unique=False)
    op.create_index(op.f('ix_sales_records_product_id'), 'sales_records', ['product_id'], unique=False)
    op.create_index(op.f('ix_sales_records_sale_date'), 'sales_records', ['sale_date'], unique=False)
    op.create_index(op.f('ix_sales_records_record_id'), 'sales_records', ['record_id'], unique=False)
    
    # customer_monthly_status 테이블 (거래처별 월간 상태 - 환자수, 사용예산 등)
    op.create_table('customer_monthly_status',
        sa.Column('status_record_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('year_month', sa.String(), nullable=False),
        sa.Column('patient_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('used_budget', sa.Numeric(15, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('status_record_id'),
        sa.UniqueConstraint('customer_id', 'year_month', name='uq_customer_month')
    )
    op.create_index(op.f('ix_customer_monthly_status_customer_id'), 'customer_monthly_status', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_monthly_status_year_month'), 'customer_monthly_status', ['year_month'], unique=False)
    
    # interaction_logs 테이블 (상호작용 기록) - 모델과 일치
    op.create_table('interaction_logs',
        sa.Column('log_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('interaction_type', sa.String(), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('sentiment', sa.String(), nullable=True),
        sa.Column('compliance_risk', sa.String(), nullable=True),
        sa.Column('interacted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_info.employee_info_id'], ),
        sa.PrimaryKeyConstraint('log_id')
    )
    op.create_index(op.f('ix_interaction_logs_customer_id'), 'interaction_logs', ['customer_id'], unique=False)
    op.create_index(op.f('ix_interaction_logs_employee_id'), 'interaction_logs', ['employee_id'], unique=False)
    op.create_index(op.f('ix_interaction_logs_interacted_at'), 'interaction_logs', ['interacted_at'], unique=False)
    op.create_index(op.f('ix_interaction_logs_log_id'), 'interaction_logs', ['log_id'], unique=False)
    
    # assignment_map 테이블 (담당자 배정) - 모델과 일치
    op.create_table('assignment_map',
        sa.Column('assignment_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_info.employee_info_id'], ),
        sa.PrimaryKeyConstraint('assignment_id'),
        sa.UniqueConstraint('employee_id', 'customer_id', name='uq_assignment_employee_customer')
    )
    op.create_index(op.f('ix_assignment_map_assignment_id'), 'assignment_map', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_assignment_map_customer_id'), 'assignment_map', ['customer_id'], unique=False)
    op.create_index(op.f('ix_assignment_map_employee_id'), 'assignment_map', ['employee_id'], unique=False)
    
    # document_relations 테이블 (문서 관계) - 모델과 일치
    op.create_table('document_relations',
        sa.Column('relation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('doc_id', sa.String(36), nullable=False),
        sa.Column('related_entity_type', sa.String(), nullable=False),
        sa.Column('related_entity_id', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.doc_id'], ),
        sa.PrimaryKeyConstraint('relation_id'),
        sa.UniqueConstraint('doc_id', 'related_entity_type', 'related_entity_id', name='uq_doc_relation_unique')
    )
    op.create_index(op.f('ix_document_relations_doc_id'), 'document_relations', ['doc_id'], unique=False)
    op.create_index(op.f('ix_document_relations_related_entity_id'), 'document_relations', ['related_entity_id'], unique=False)
    op.create_index(op.f('ix_document_relations_related_entity_type'), 'document_relations', ['related_entity_type'], unique=False)
    op.create_index(op.f('ix_document_relations_relation_id'), 'document_relations', ['relation_id'], unique=False)
    
    # chat_sessions 테이블 (채팅 세션)
    op.create_table('chat_sessions',
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('session_title', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('session_id')
    )
    
    # chat_history 테이블 (채팅 대화 기록)
    op.create_table('chat_history',
        sa.Column('message_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ),
        sa.PrimaryKeyConstraint('message_id')
    )
    
    # system_trace_logs 테이블 (시스템 추적 로그)
    op.create_table('system_trace_logs',
        sa.Column('trace_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=True),
        sa.Column('log_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('trace_id')
    )
    
    # insurance_recognition_criteria 테이블 (보험 인정기준)
    if 'insurance_recognition_criteria' not in existing_tables:
        try:
            op.create_table('insurance_recognition_criteria',
                sa.Column('criteria_id', sa.Integer(), autoincrement=True, nullable=False),
                sa.Column('product_id', sa.Integer(), nullable=True),
                sa.Column('criteria_code', sa.String(length=50), nullable=True),
                sa.Column('criteria_name', sa.String(length=200), nullable=False),
                sa.Column('description', sa.Text(), nullable=True),
                sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                sa.Column('coverage_amount', sa.Numeric(15, 2), nullable=True),
                sa.Column('effective_from', sa.Date(), nullable=True),
                sa.Column('effective_to', sa.Date(), nullable=True),
                sa.Column('status', sa.String(length=50), server_default=sa.text("'active'"), nullable=True),
                sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
                sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ),
                sa.PrimaryKeyConstraint('criteria_id'),
                sa.UniqueConstraint('criteria_code', 'criteria_name', name='uq_criteria_code_name')
            )
            op.create_index(op.f('ix_insurance_recognition_criteria_criteria_id'), 'insurance_recognition_criteria', ['criteria_id'], unique=False)
            op.create_index(op.f('ix_insurance_recognition_criteria_product_id'), 'insurance_recognition_criteria', ['product_id'], unique=False)
            op.create_index(op.f('ix_insurance_recognition_criteria_status'), 'insurance_recognition_criteria', ['status'], unique=False)
            logger.info("Insurance recognition criteria table created successfully")
        except Exception as e:
            logger.warning(f"Failed to create insurance_recognition_criteria table: {e}")
    
    # news_strategy_reports 테이블 (뉴스 전략 보고서)
    if 'news_strategy_reports' not in existing_tables:
        try:
            op.create_table('news_strategy_reports',
                sa.Column('report_id', sa.Integer(), autoincrement=True, nullable=False),
                sa.Column('title', sa.String(length=500), nullable=False),
                sa.Column('content', sa.Text(), nullable=True),
                sa.Column('created_by', sa.Integer(), nullable=True),
                sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                sa.ForeignKeyConstraint(['created_by'], ['employees.employee_id'], ),
                sa.PrimaryKeyConstraint('report_id')
            )
            op.create_index(op.f('ix_news_strategy_reports_report_id'), 'news_strategy_reports', ['report_id'], unique=False)
            op.create_index(op.f('ix_news_strategy_reports_created_by'), 'news_strategy_reports', ['created_by'], unique=False)
            logger.info("News strategy reports table created successfully")
        except Exception as e:
            logger.warning(f"Failed to create news_strategy_reports table: {e}")
    
    # news_strategy_report_references 테이블 (뉴스-전략보고서 연결 테이블)
    if 'news_strategy_report_references' not in existing_tables:
        try:
            op.create_table('news_strategy_report_references',
                sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                sa.Column('report_id', sa.Integer(), nullable=False),
                sa.Column('news_id', sa.Integer(), nullable=False),
                sa.Column('reference_type', sa.String(length=50), nullable=True),
                sa.Column('notes', sa.Text(), nullable=True),
                sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                sa.ForeignKeyConstraint(['report_id'], ['news_strategy_reports.report_id'], ondelete='CASCADE'),
                sa.ForeignKeyConstraint(['news_id'], ['news.news_id'], ondelete='CASCADE'),
                sa.PrimaryKeyConstraint('id'),
                sa.UniqueConstraint('report_id', 'news_id', name='uq_report_news')
            )
            op.create_index(op.f('ix_news_strategy_report_references_report_id'), 'news_strategy_report_references', ['report_id'], unique=False)
            op.create_index(op.f('ix_news_strategy_report_references_news_id'), 'news_strategy_report_references', ['news_id'], unique=False)
            logger.info("News strategy report references table created successfully")
        except Exception as e:
            logger.warning(f"Failed to create news_strategy_report_references table: {e}")
    
    # ========================================
    # 5. Materialized Views
    # ========================================
    
    # Employee Performance Materialized View
    op.execute("""
        CREATE MATERIALIZED VIEW employee_performance_mv AS
        WITH sales_summary AS (
            SELECT 
                sr.employee_id,
                DATE_TRUNC('month', sr.sale_date)::DATE as year_month,
                SUM(sr.sale_amount) as actual_sales,
                COUNT(DISTINCT sr.record_id) as sales_count,
                COUNT(DISTINCT sr.customer_id) as customer_count
            FROM sales_records sr
            GROUP BY sr.employee_id, DATE_TRUNC('month', sr.sale_date)
        )
        SELECT 
            COALESCE(ep.employee_id, ss.employee_id) as employee_id,
            COALESCE(ep.year_month, ss.year_month) as year_month,
            ei.name as employee_name,
            ei.employee_number,
            COALESCE(ep.target_amount, 0) as target_amount,
            COALESCE(ss.actual_sales, 0) as actual_sales,
            CASE 
                WHEN ep.target_amount > 0 THEN 
                    ROUND(CAST((COALESCE(ss.actual_sales, 0) / ep.target_amount) * 100 AS NUMERIC), 2)
                ELSE 0 
            END as achievement_rate,
            COALESCE(ss.sales_count, 0) as sales_count,
            COALESCE(ss.customer_count, 0) as customer_count
        FROM employee_performance ep
        FULL OUTER JOIN sales_summary ss 
            ON ep.employee_id = ss.employee_id 
            AND ep.year_month = ss.year_month
        LEFT JOIN employee_info ei 
            ON COALESCE(ep.employee_id, ss.employee_id) = ei.employee_info_id
    """)
    
    # Create indexes for employee performance materialized view
    op.execute("CREATE UNIQUE INDEX idx_employee_performance_mv_unique ON employee_performance_mv (employee_id, year_month)")
    op.execute("CREATE INDEX idx_employee_performance_mv_employee ON employee_performance_mv (employee_id)")
    op.execute("CREATE INDEX idx_employee_performance_mv_month ON employee_performance_mv (year_month)")
    
    # Customer Monthly Performance Materialized View
    op.execute("""
        CREATE MATERIALIZED VIEW customer_monthly_performance_mv AS
        WITH sales_summary AS (
            SELECT 
                sr.customer_id,
                TO_CHAR(sr.sale_date, 'YYYY-MM') as year_month,
                SUM(sr.sale_amount) as monthly_sales,
                COUNT(DISTINCT sr.sale_date) as visit_count,
                COUNT(DISTINCT sr.record_id) as transaction_count
            FROM sales_records sr
            WHERE sr.sale_date IS NOT NULL
            GROUP BY sr.customer_id, TO_CHAR(sr.sale_date, 'YYYY-MM')
        ),
        status_summary AS (
            SELECT 
                customer_id,
                year_month,
                patient_count,
                used_budget as budget_used
            FROM customer_monthly_status
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY c.customer_id, COALESCE(ss.year_month, st.year_month)) as performance_id,
            c.customer_id,
            c.customer_name,
            c.customer_grade,
            COALESCE(ss.year_month, st.year_month) as year_month,
            COALESCE(ss.monthly_sales, 0) as monthly_sales,
            COALESCE(st.budget_used, 0) as budget_used,
            COALESCE(ss.visit_count, 0) as visit_count,
            COALESCE(ss.transaction_count, 0) as transaction_count,
            COALESCE(st.patient_count, 0) as patient_count,
            NOW() as created_at
        FROM customers c
        LEFT JOIN sales_summary ss ON c.customer_id = ss.customer_id
        FULL OUTER JOIN status_summary st 
            ON c.customer_id = st.customer_id 
            AND ss.year_month = st.year_month
        WHERE c.is_deleted = false
            AND (ss.year_month IS NOT NULL OR st.year_month IS NOT NULL)
    """)
    
    # Create indexes for customer performance materialized view
    op.execute("CREATE UNIQUE INDEX idx_customer_performance_mv_pk ON customer_monthly_performance_mv (performance_id)")
    op.execute("CREATE INDEX idx_customer_performance_mv_customer ON customer_monthly_performance_mv (customer_id)")
    op.execute("CREATE INDEX idx_customer_performance_mv_yearmonth ON customer_monthly_performance_mv (year_month)")
    op.execute("CREATE INDEX idx_customer_performance_mv_customer_yearmonth ON customer_monthly_performance_mv (customer_id, year_month)")


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop materialized views first
    op.execute("DROP MATERIALIZED VIEW IF EXISTS customer_monthly_performance_mv")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS employee_performance_mv")
    
    # Drop dependent tables first (reverse order)
    # Drop news strategy report references first (depends on both news and reports)
    op.drop_index(op.f('ix_news_strategy_report_references_news_id'), table_name='news_strategy_report_references')
    op.drop_index(op.f('ix_news_strategy_report_references_report_id'), table_name='news_strategy_report_references')
    op.drop_table('news_strategy_report_references')
    
    # Drop news strategy reports
    op.drop_index(op.f('ix_news_strategy_reports_created_by'), table_name='news_strategy_reports')
    op.drop_index(op.f('ix_news_strategy_reports_report_id'), table_name='news_strategy_reports')
    op.drop_table('news_strategy_reports')
    
    # Drop insurance recognition criteria
    op.drop_index(op.f('ix_insurance_recognition_criteria_status'), table_name='insurance_recognition_criteria')
    op.drop_index(op.f('ix_insurance_recognition_criteria_product_id'), table_name='insurance_recognition_criteria')
    op.drop_index(op.f('ix_insurance_recognition_criteria_criteria_id'), table_name='insurance_recognition_criteria')
    op.drop_table('insurance_recognition_criteria')
    
    # Continue with existing dependent tables
    op.drop_index(op.f('ix_document_relations_relation_id'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_related_entity_type'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_related_entity_id'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_doc_id'), table_name='document_relations')
    op.drop_table('document_relations')
    
    op.drop_table('system_trace_logs')
    op.drop_table('chat_history')
    op.drop_table('chat_sessions')
    
    op.drop_index(op.f('ix_assignment_map_employee_id'), table_name='assignment_map')
    op.drop_index(op.f('ix_assignment_map_customer_id'), table_name='assignment_map')
    op.drop_index(op.f('ix_assignment_map_assignment_id'), table_name='assignment_map')
    op.drop_table('assignment_map')
    
    op.drop_index(op.f('ix_interaction_logs_log_id'), table_name='interaction_logs')
    op.drop_index(op.f('ix_interaction_logs_interacted_at'), table_name='interaction_logs')
    op.drop_index(op.f('ix_interaction_logs_employee_id'), table_name='interaction_logs')
    op.drop_index(op.f('ix_interaction_logs_customer_id'), table_name='interaction_logs')
    op.drop_table('interaction_logs')
    
    op.drop_index(op.f('ix_customer_monthly_status_year_month'), table_name='customer_monthly_status')
    op.drop_index(op.f('ix_customer_monthly_status_customer_id'), table_name='customer_monthly_status')
    op.drop_table('customer_monthly_status')
    
    op.drop_index(op.f('ix_sales_records_record_id'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_sale_date'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_product_id'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_employee_id'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_customer_id'), table_name='sales_records')
    op.drop_table('sales_records')
    
    op.drop_index(op.f('ix_employee_performance_performance_id'), table_name='employee_performance')
    op.drop_table('employee_performance')
    
    op.drop_table('employee_info')
    
    # Drop base tables
    op.drop_table('table_descriptions')
    
    op.drop_index(op.f('ix_documents_doc_id'), table_name='documents')
    op.drop_table('documents')
    
    op.drop_index(op.f('ix_products_product_name'), table_name='products')
    op.drop_index(op.f('ix_products_product_id'), table_name='products')
    op.drop_table('products')
    
    op.drop_index(op.f('ix_customers_customer_name'), table_name='customers')
    op.drop_index(op.f('ix_customers_customer_id'), table_name='customers')
    op.drop_table('customers')
    
    op.drop_index(op.f('ix_branches_branch_id'), table_name='branches')
    op.drop_table('branches')
    
    op.drop_index(op.f('ix_employees_employee_id'), table_name='employees')
    op.drop_table('employees')
    
    # Drop new base tables
    op.drop_index(op.f('ix_laws_article'), table_name='laws')
    op.drop_index(op.f('ix_laws_law_id'), table_name='laws')
    op.drop_table('laws')
    
    op.drop_index(op.f('ix_news_published_date'), table_name='news')
    op.drop_index(op.f('ix_news_news_type'), table_name='news')
    op.drop_index(op.f('ix_news_news_id'), table_name='news')
    op.drop_table('news')
    
    # Drop enum types - 존재하는 경우에만 삭제
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'newstype')")
    ).scalar()
    
    if result:
        connection.execute(sa.text("DROP TYPE IF EXISTS newstype CASCADE"))