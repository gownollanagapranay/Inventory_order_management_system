from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models import Coupon
from ..schemas import CouponCreate, CouponResponse, CouponValidate
from ..dependencies import get_current_user


router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"]
)


# Creating Coupons
@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Only admins can create coupons
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Clean the coupon code
    code = coupon_data.code.strip().upper()

    # Check whether coupon already exists
    existing_coupon = (db.query(Coupon).filter(Coupon.code == code).first())

    if existing_coupon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon code already exists"
        )

    # Validate discount type
    if coupon_data.discount_type not in ["percentage", "fixed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="discount_type must be 'percentage' or 'fixed'"
        )

    # Validate discount value
    if coupon_data.discount_value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="discount_value must be greater than 0"
        )

    # Percentage cannot be greater than 100
    if (
        coupon_data.discount_type == "percentage"
        and coupon_data.discount_value > 100
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Percentage discount cannot exceed 100"
        )

    # Validate minimum order amount
    if coupon_data.minimum_order_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="minimum_order_amount cannot be negative"
        )

    # Validate usage limit
    if (
        coupon_data.usage_limit is not None
        and coupon_data.usage_limit <= 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="usage_limit must be greater than 0"
        )

    coupon = Coupon(
        code=code,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        minimum_order_amount=coupon_data.minimum_order_amount,
        usage_limit=coupon_data.usage_limit,
        expires_at=coupon_data.expires_at
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return coupon



# Validating Coupons
@router.post("/validate")
def validate_coupon(
    coupon_data: CouponValidate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    code = coupon_data.code.strip().upper()
    order_amount = coupon_data.order_amount

    # Validate order amount
    if order_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Order amount must be greater than zero"
        )

    # Find coupon
    coupon = (
        db.query(Coupon)
        .filter(Coupon.code == code)
        .first()
    )

    if coupon is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid coupon code"
        )

    # Check active status
    if not coupon.is_active:
        raise HTTPException(
            status_code=400,
            detail="Coupon is inactive"
        )

    # Check expiry
    if coupon.expires_at is not None:
        expiry = coupon.expires_at

        # SQLite may return a naive datetime.
        # Compare consistently using UTC.
        if expiry.tzinfo is None:
            now = datetime.utcnow()
        else:
            now = datetime.now(expiry.tzinfo)

        if now > expiry:
            raise HTTPException(
                status_code=400,
                detail="Coupon has expired"
            )

    # Check usage limit
    if (
        coupon.usage_limit is not None
        and coupon.used_count >= coupon.usage_limit
    ):
        raise HTTPException(
            status_code=400,
            detail="Coupon usage limit reached"
        )

    # Check minimum order amount
    if order_amount < coupon.minimum_order_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order amount is {coupon.minimum_order_amount}"
        )

    # Calculate discount
    if coupon.discount_type == "percentage":
        discount = order_amount * coupon.discount_value / 100

    elif coupon.discount_type == "fixed":
        discount = coupon.discount_value

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid coupon discount type"
        )

    # Discount cannot exceed order amount
    discount = min(discount, order_amount)

    # Round to two decimal places
    discount = round(discount, 2)
    final_amount = round(order_amount - discount, 2)

    return {
        "message": "Coupon applied successfully",
        "coupon_code": coupon.code,
        "original_amount": order_amount,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount,
        "final_amount": final_amount
    }



# GET ALL ACTIVE COUPONS
@router.get("/")
def get_coupons(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    coupons = db.query(Coupon).filter(
        Coupon.is_active == 1
    ).all()

    return [
        {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "minimum_order_amount": coupon.minimum_order_amount,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
            "expires_at": coupon.expires_at
        }
        for coupon in coupons
    ]
