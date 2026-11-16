from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone

from .database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    image_url = Column(String(1000), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc))