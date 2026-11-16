from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ProductCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )
    
    image_url: Optional[str] = Field(
    default=None,
    max_length=1000
    )

    category: str = Field(
        min_length=2,
        max_length=100
    )

    price: float = Field(
        gt=0
    )

    stock_quantity: int = Field(
        ge=0
    )

    low_stock_threshold: int = Field(
        ge=0
    )


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )
    
    image_url: Optional[str] = Field(
    default=None,
    max_length=1000
    )

    category: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    price: Optional[float] = Field(
        default=None,
        gt=0
    )

    stock_quantity: Optional[int] = Field(
        default=None,
        ge=0
    )

    low_stock_threshold: Optional[int] = Field(
        default=None,
        ge=0
    )


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    image_url: Optional[str]
    category: str
    price: float
    stock_quantity: int
    low_stock_threshold: int
    

class StockUpdate(BaseModel):
    quantity: int = Field(ge=0)
    

class StockDecrease(BaseModel):
    quantity: int = Field(gt=0)