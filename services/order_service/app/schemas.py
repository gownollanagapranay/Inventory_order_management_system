
from pydantic import BaseModel, Field
from datetime import datetime


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float


# Optional coupon code during checkout
class CheckoutRequest(BaseModel):
    coupon_code: str | None = None


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    payment_status: str
    coupon_code: str | None = None
    discount_amount: float = 0
    items: list[OrderItemResponse]

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    order_id: int
    payment_intent_id: str
    client_secret: str
    amount: float
    currency: str


class CouponCreate(BaseModel):
    code: str
    discount_type: str
    discount_value: float
    minimum_order_amount: float = 0
    usage_limit: int | None = None
    expires_at: datetime | None = None


class CouponResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: float
    minimum_order_amount: float
    usage_limit: int | None
    used_count: int
    is_active: int
    expires_at: datetime | None
    created_at: datetime


class CouponValidate(BaseModel):
    code: str
    order_amount: float

    
    
class ReturnRequestCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class ReturnRequestResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        
    
class OrderStatusUpdate(BaseModel):
    status: str
    
    
class ReturnRequestReview(BaseModel):
    status: str