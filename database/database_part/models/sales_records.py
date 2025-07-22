from . import Base
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric

class SalesRecord(Base):
    __tablename__ = "sales_records"
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    sale_amount = Column(Numeric(15, 2), nullable=False)
    sale_date = Column(Date, nullable=False) 
