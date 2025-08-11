"""Initial complete schema with all tables

Revision ID: initial_complete_schema
Revises: 
Create Date: 2025-01-10 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import VECTOR

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
    # 2. Base Tables (No Foreign Keys)
    # ========================================
    
    # employees 테이블 (계정 정보)
    op.create_table('employees',
        sa.Column('employee_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('employee_id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
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
        sa.Column('total_patients', sa.Integer(), nullable=True),
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
        sa.Column('doc_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=False),
        sa.Column('doc_title', sa.String(), nullable=False),
        sa.Column('doc_type', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=True),
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
    
    # ========================================
    # 3. Dependent Tables (With Foreign Keys)
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
        sa.Column('doc_id', sa.Integer(), nullable=False),
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
    
    # ========================================
    # 5. Materialized View for Employee Performance
    # ========================================
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
    
    # Create indexes for materialized view
    op.execute("CREATE UNIQUE INDEX idx_employee_performance_mv_unique ON employee_performance_mv (employee_id, year_month)")
    op.execute("CREATE INDEX idx_employee_performance_mv_employee ON employee_performance_mv (employee_id)")
    op.execute("CREATE INDEX idx_employee_performance_mv_month ON employee_performance_mv (year_month)")


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop materialized view first
    op.execute("DROP MATERIALIZED VIEW IF EXISTS employee_performance_mv")
    
    # Drop dependent tables first (reverse order)
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