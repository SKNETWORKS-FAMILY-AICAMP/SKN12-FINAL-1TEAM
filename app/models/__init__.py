from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .employees import Employee
from .employee_info import EmployeeInfo
from .customers import Customer
from .products import Product
from .interaction_logs import InteractionLog
from .sales_records import SalesRecord
from .customer_monthly_performance_mv import get_customer_monthly_performance_mv_table
from .documents import Document
from .chat_history import ChatHistory
from .chat_sessions import ChatSession
from .system_trace_logs import SystemTraceLog
from .assignment_map import AssignmentMap
from .document_relations import DocumentRelation
from .branches import Branch
from .employee_performance import EmployeePerformance
from .employee_performance_mv import EmployeePerformanceMV
from .news import News, NewsType
from .laws import Law
from .insurance_recognition_criteria import InsuranceRecognitionCriteria
from .news_strategy_reports import NewsStrategyReport
from .news_strategy_report_references import NewsStrategyReportReference
from .schedules import Schedule, ScheduleType, ScheduleStatus
