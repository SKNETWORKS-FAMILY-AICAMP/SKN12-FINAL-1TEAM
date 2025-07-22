from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base

Base = declarative_base()
metadata = MetaData()

# ?¤ì œ ?¬ìš© ??engine??import?´ì„œ autoload_with=engine?¼ë¡œ ?¬ìš©?´ì•¼ ??
# ?ˆì‹œ: from backend.app.database_api.db import engine
# ?„ë˜??êµ¬ì¡° ?ˆì‹œ

def get_customer_monthly_performance_mv_table(engine):
    return Table(
        "customer_monthly_performance_mv",
        metadata,
        Column("performance_id", Integer, primary_key=True),
        Column("customer_id", Integer),
        Column("year_month", String),
        Column("monthly_sales", Integer),
        Column("budget_used", Integer),
        Column("visit_count", Integer),
        autoload_with=engine
    )

# ?½ê¸° ?„ìš© ORM ë§¤í•‘ ?ˆì‹œ
# ?¤ì œ ?¬ìš© ???„ë˜ì²˜ëŸ¼ ?™ì ?¼ë¡œ __table__??? ë‹¹?´ì•¼ ??
#
# CustomerMonthlyPerformanceMV = type(
#     "CustomerMonthlyPerformanceMV",
#     (Base,),
#     {"__table__": get_customer_monthly_performance_mv_table(engine)}
# ) 
