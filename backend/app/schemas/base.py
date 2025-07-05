from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True
    )


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResponseSchema(BaseSchema):
    """Standard API response schema."""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None
    errors: Optional[list] = None
