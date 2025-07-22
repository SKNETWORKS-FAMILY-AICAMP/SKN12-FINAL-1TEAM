from . import Base
from sqlalchemy import Column, Integer, String, Boolean

class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    is_active = Column(Boolean, default=True) 
