from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class TimestampMixin:
    """Mixin to add timestamp fields to models."""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """Base model class with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
