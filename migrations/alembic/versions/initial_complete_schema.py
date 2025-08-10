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
        sa.Column('password', sa.String(length=100), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('employee_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_employees_employee_id'), 'employees', ['employee_id'], unique=False)
    
    # branches 테이블 (지점 정보)
    op.create_table('branches',
        sa.Column('branch_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('branch_name', sa.String(length=100), nullable=False),
        sa.Column('headquarters', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('contact_number', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('branch_id'),
        sa.UniqueConstraint('branch_name')
    )
    op.create_index(op.f('ix_branches_branch_id'), 'branches', ['branch_id'], unique=False)
    
    # customers 테이블 (고객 정보)
    op.create_table('customers',
        sa.Column('customer_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('doctor_name', sa.String(), nullable=True),
        sa.Column('total_patients', sa.Integer(), nullable=True),
        sa.Column('customer_grade', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('is_auto_created', sa.Boolean(), nullable=True),
        sa.Column('approval_status', sa.String(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['employees.employee_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('customer_id')
    )
    op.create_index(op.f('ix_customers_customer_id'), 'customers', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customers_customer_name'), 'customers', ['customer_name'], unique=False)
    
    # products 테이블 (제품 정보)
    op.create_table('products',
        sa.Column('product_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_auto_created', sa.Boolean(), nullable=True),
        sa.Column('approval_status', sa.String(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['employees.employee_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('product_id')
    )
    op.create_index(op.f('ix_products_product_id'), 'products', ['product_id'], unique=False)
    op.create_index(op.f('ix_products_product_name'), 'products', ['product_name'], unique=False)
    
    # documents 테이블 (문서 메타데이터)
    op.create_table('documents',
        sa.Column('document_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('table_type', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('columns_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('upload_status', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('created_records', sa.Integer(), nullable=True),
        sa.Column('updated_records', sa.Integer(), nullable=True),
        sa.Column('skipped_records', sa.Integer(), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['uploaded_by'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('document_id')
    )
    op.create_index(op.f('ix_documents_document_id'), 'documents', ['document_id'], unique=False)
    
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
    
    # employee_info 테이블 (인사 정보)
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
        sa.Column('is_auto_created', sa.Boolean(), nullable=True),
        sa.Column('approval_status', sa.String(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['employees.employee_id'], ),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.branch_id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('employee_info_id'),
        sa.UniqueConstraint('employee_number')
    )
    
    # branch_targets 테이블 (지점별 목표)
    op.create_table('branch_targets',
        sa.Column('target_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('employee_info_id', sa.Integer(), nullable=False),
        sa.Column('target_year', sa.Integer(), nullable=False),
        sa.Column('target_month', sa.Integer(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('target_amount', sa.Float(), nullable=True),
        sa.Column('actual_amount', sa.Float(), nullable=True),
        sa.Column('achievement_rate', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.branch_id'], ),
        sa.ForeignKeyConstraint(['employee_info_id'], ['employee_info.employee_info_id'], ),
        sa.PrimaryKeyConstraint('target_id'),
        sa.UniqueConstraint('branch_id', 'employee_info_id', 'target_year', 'target_month', name='uq_branch_employee_yearmonth')
    )
    op.create_index(op.f('ix_branch_targets_target_id'), 'branch_targets', ['target_id'], unique=False)
    
    # sales_records 테이블 (매출 기록)
    op.create_table('sales_records',
        sa.Column('sale_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sale_amount', sa.Float(), nullable=False),
        sa.Column('sale_date', sa.Date(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_info.employee_info_id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['employees.employee_id'], ),
        sa.PrimaryKeyConstraint('sale_id')
    )
    op.create_index(op.f('ix_sales_records_customer_id'), 'sales_records', ['customer_id'], unique=False)
    op.create_index(op.f('ix_sales_records_employee_id'), 'sales_records', ['employee_id'], unique=False)
    op.create_index(op.f('ix_sales_records_product_id'), 'sales_records', ['product_id'], unique=False)
    op.create_index(op.f('ix_sales_records_sale_date'), 'sales_records', ['sale_date'], unique=False)
    op.create_index(op.f('ix_sales_records_sale_id'), 'sales_records', ['sale_id'], unique=False)
    
    # interaction_logs 테이블 (상호작용 기록)
    op.create_table('interaction_logs',
        sa.Column('log_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('interaction_type', sa.String(), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('sentiment', sa.String(), nullable=True),
        sa.Column('compliance_risk', sa.String(), nullable=True),
        sa.Column('interacted_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_info.employee_info_id'], ),
        sa.PrimaryKeyConstraint('log_id')
    )
    op.create_index(op.f('ix_interaction_logs_customer_id'), 'interaction_logs', ['customer_id'], unique=False)
    op.create_index(op.f('ix_interaction_logs_employee_id'), 'interaction_logs', ['employee_id'], unique=False)
    op.create_index(op.f('ix_interaction_logs_interacted_at'), 'interaction_logs', ['interacted_at'], unique=False)
    op.create_index(op.f('ix_interaction_logs_log_id'), 'interaction_logs', ['log_id'], unique=False)
    
    # assignment_map 테이블 (담당자 배정)
    op.create_table('assignment_map',
        sa.Column('assignment_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_info.employee_info_id'], ),
        sa.PrimaryKeyConstraint('assignment_id'),
        sa.UniqueConstraint('employee_id', 'customer_id')
    )
    op.create_index(op.f('ix_assignment_map_assignment_id'), 'assignment_map', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_assignment_map_customer_id'), 'assignment_map', ['customer_id'], unique=False)
    op.create_index(op.f('ix_assignment_map_employee_id'), 'assignment_map', ['employee_id'], unique=False)
    
    # document_relations 테이블 (문서 관계)
    op.create_table('document_relations',
        sa.Column('relation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('related_table', sa.String(), nullable=False),
        sa.Column('related_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ),
        sa.PrimaryKeyConstraint('relation_id')
    )
    op.create_index(op.f('ix_document_relations_document_id'), 'document_relations', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_relations_related_id'), 'document_relations', ['related_id'], unique=False)
    op.create_index(op.f('ix_document_relations_related_table'), 'document_relations', ['related_table'], unique=False)
    op.create_index(op.f('ix_document_relations_relation_id'), 'document_relations', ['relation_id'], unique=False)


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop dependent tables first (reverse order)
    op.drop_index(op.f('ix_document_relations_relation_id'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_related_table'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_related_id'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_document_id'), table_name='document_relations')
    op.drop_table('document_relations')
    
    op.drop_index(op.f('ix_assignment_map_employee_id'), table_name='assignment_map')
    op.drop_index(op.f('ix_assignment_map_customer_id'), table_name='assignment_map')
    op.drop_index(op.f('ix_assignment_map_assignment_id'), table_name='assignment_map')
    op.drop_table('assignment_map')
    
    op.drop_index(op.f('ix_interaction_logs_log_id'), table_name='interaction_logs')
    op.drop_index(op.f('ix_interaction_logs_interacted_at'), table_name='interaction_logs')
    op.drop_index(op.f('ix_interaction_logs_employee_id'), table_name='interaction_logs')
    op.drop_index(op.f('ix_interaction_logs_customer_id'), table_name='interaction_logs')
    op.drop_table('interaction_logs')
    
    op.drop_index(op.f('ix_sales_records_sale_id'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_sale_date'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_product_id'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_employee_id'), table_name='sales_records')
    op.drop_index(op.f('ix_sales_records_customer_id'), table_name='sales_records')
    op.drop_table('sales_records')
    
    op.drop_index(op.f('ix_branch_targets_target_id'), table_name='branch_targets')
    op.drop_table('branch_targets')
    
    op.drop_table('employee_info')
    
    # Drop base tables
    op.drop_table('table_descriptions')
    
    op.drop_index(op.f('ix_documents_document_id'), table_name='documents')
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