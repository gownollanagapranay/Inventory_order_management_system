
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import stripe

from ..database import get_db
from ..models import CartItem, Order, OrderItem, Coupon, ReturnRequest
from ..schemas import (OrderResponse, PaymentResponse, CheckoutRequest, ReturnRequestCreate, 
                ReturnRequestResponse, OrderStatusUpdate,ReturnRequestReview)
from ..dependencies import get_current_user,get_admin_user
from ..product_client import get_product, decrease_product_stock
from ..payment_service import create_payment_intent

from ..messaging.rabbitmq import publish_order_created, publish_order_paid

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# -----------------------------------------
# validate coupon and calculate discount
# -----------------------------------------

def calculate_coupon_discount(
    db: Session,
    coupon_code: str,
    order_amount: float
):
    code = coupon_code.strip().upper()

    coupon = db.query(Coupon).filter(
        Coupon.code == code
    ).first()

    if coupon is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid coupon code"
        )

    if coupon.is_active != 1:
        raise HTTPException(
            status_code=400,
            detail="Coupon is inactive"
        )

    if coupon.expires_at is not None:
        expiry = coupon.expires_at

        if expiry.tzinfo is None:
            now = datetime.utcnow()
        else:
            now = datetime.now(expiry.tzinfo)

        if now > expiry:
            raise HTTPException(
                status_code=400,
                detail="Coupon has expired"
            )

    if (
        coupon.usage_limit is not None
        and coupon.used_count >= coupon.usage_limit
    ):
        raise HTTPException(
            status_code=400,
            detail="Coupon usage limit reached"
        )

    if order_amount < coupon.minimum_order_amount:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Minimum order amount is "
                f"{coupon.minimum_order_amount}"
            )
        )

    if coupon.discount_type == "percentage":
        discount = (
            order_amount * coupon.discount_value / 100
        )

    elif coupon.discount_type == "fixed":
        discount = coupon.discount_value

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid coupon configuration"
        )

    discount = min(discount, order_amount)
    discount = round(discount, 2)

    final_amount = round(order_amount - discount, 2)

    return coupon, discount, final_amount


# -----------------------------------------
# CHECKOUT
# -----------------------------------------

@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
def checkout(
    checkout_data: CheckoutRequest | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]

    cart_items = db.query(CartItem).filter(
        CartItem.user_id == user_id
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    order_items_data = []
    total_amount = 0.0

    # STEP 1: Validate products and calculate cart total

    for cart_item in cart_items:

        product = get_product(cart_item.product_id)

        available_stock = product["stock_quantity"]

        if available_stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock for "
                    f"product {cart_item.product_id}"
                )
            )

        unit_price = product["price"]

        subtotal = unit_price * cart_item.quantity

        total_amount += subtotal

        order_items_data.append({
            "product_id": cart_item.product_id,
            "quantity": cart_item.quantity,
            "unit_price": unit_price,
            "subtotal": subtotal
        })

    total_amount = round(total_amount, 2)

    # STEP 2: Validate optional coupon

    coupon_code = None
    discount_amount = 0.0
    final_amount = total_amount

    if checkout_data and checkout_data.coupon_code:

        coupon_code = checkout_data.coupon_code.strip().upper()

        coupon, discount_amount, final_amount = (
            calculate_coupon_discount(
                db=db,
                coupon_code=coupon_code,
                order_amount=total_amount
            )
        )

    # STEP 3: Reduce inventory after all validations

    for item_data in order_items_data:

        decrease_product_stock(
            product_id=item_data["product_id"],
            quantity=item_data["quantity"]
        )

    # STEP 4: Create order with discounted amount

    order = Order(
        user_id=user_id,
        total_amount=final_amount,
        coupon_code=coupon_code,
        discount_amount=discount_amount,
        status="pending_payment",
        payment_status="pending"
    )

    db.add(order)
    db.flush()

    response_items = []

    # STEP 5: Create order items

    for item_data in order_items_data:

        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"]
        )

        db.add(order_item)
        response_items.append(order_item)

    # STEP 6: Clear cart

    for cart_item in cart_items:
        db.delete(cart_item)

    db.commit()
    db.refresh(order)

    # Publish order.created event
    publish_order_created(order)

    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "coupon_code": order.coupon_code,
        "discount_amount": order.discount_amount,
        "status": order.status,
        "payment_status": order.payment_status,
        "items": response_items
    }


# -----------------------------------------
# CREATE STRIPE PAYMENT INTENT
# -----------------------------------------

@router.post(
    "/{order_id}/payment",
    response_model=PaymentResponse
)
def create_order_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.payment_status == "paid":
        raise HTTPException(
            status_code=400,
            detail="Order is already paid"
        )

    if order.status != "pending_payment":
        raise HTTPException(
            status_code=400,
            detail="Order is not available for payment"
        )

    payment_intent = create_payment_intent(
        amount=order.total_amount,
        order_id=order.id
    )

    order.stripe_payment_intent_id = payment_intent.id

    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "payment_intent_id": payment_intent.id,
        "client_secret": payment_intent.client_secret,
        "amount": order.total_amount,
        "currency": "inr"
    }


# -----------------------------------------
# VERIFY PAYMENT
# -----------------------------------------

@router.post("/{order_id}/verify-payment")
def verify_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]

    # STEP 1: Find order

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # STEP 2: Check PaymentIntent

    if not order.stripe_payment_intent_id:
        raise HTTPException(
            status_code=400,
            detail="Payment has not been initiated"
        )

    # STEP 3: Retrieve payment from Stripe

    try:
        payment_intent = stripe.PaymentIntent.retrieve(
            order.stripe_payment_intent_id
        )

    except stripe.StripeError:
        raise HTTPException(
            status_code=502,
            detail="Unable to verify payment with Stripe"
        )

    # STEP 4: Check payment status

    if payment_intent.status != "succeeded":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment is not successful. "
                f"Current status: {payment_intent.status}"
            )
        )

    # STEP 5: Verify amount and currency

    expected_amount = int(round(order.total_amount * 100))

    if (
        payment_intent.amount_received != expected_amount
        or payment_intent.currency.lower() != "inr"
    ):
        raise HTTPException(
            status_code=400,
            detail="Payment amount or currency does not match the order"
        )

    # STEP 6: Verify order metadata

    metadata = payment_intent.metadata or {}

    if str(metadata.order_id) != str(order.id):
        raise HTTPException(
            status_code=400,
            detail="Payment does not match this order"
        )

    # STEP 7: Update order and coupon usage only once

    if order.payment_status != "paid":

        order.payment_status = "paid"
        order.status = "confirmed"

        if order.coupon_code:

            coupon = db.query(Coupon).filter(
                Coupon.code == order.coupon_code
            ).first()

            if coupon is not None:
                coupon.used_count += 1

        db.commit()
        db.refresh(order)

        publish_order_paid(order)

    return {
        "message": "Payment verified successfully",
        "order_id": order.id,
        "payment_status": order.payment_status,
        "order_status": order.status,
        "coupon_code": order.coupon_code,
        "discount_amount": order.discount_amount,
        "amount": order.total_amount
    }


# -----------------------------------------
# VIEW MY ORDERS
# -----------------------------------------

@router.get("/")
def get_my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]

    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []

    for order in orders:

        items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()

        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "coupon_code": order.coupon_code,
            "discount_amount": order.discount_amount,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal
                }
                for item in items
            ]
        })

    return result



# Retun Request History
@router.get(
    "/return-requests",
    response_model=list[ReturnRequestResponse]
)
def get_my_return_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    requests = (
        db.query(ReturnRequest)
        .filter(
            ReturnRequest.user_id == current_user["user_id"]
        )
        .order_by(ReturnRequest.created_at.desc())
        .all()
    )

    return requests



# Admin Sales Summary Report Endpoint
@router.get("/admin/sales-summary")
def get_sales_summary(
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    total_orders = db.query(func.count(Order.id)).scalar() or 0

    paid_orders = db.query(Order).filter(
        Order.payment_status == "paid"
    )

    total_paid_orders = paid_orders.count()

    total_revenue = db.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.payment_status == "paid"
    ).scalar()

    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status == "pending_payment"
    ).scalar() or 0

    delivered_orders = db.query(func.count(Order.id)).filter(
        Order.status == "delivered"
    ).scalar() or 0

    cancelled_orders = db.query(func.count(Order.id)).filter(
        Order.status == "cancelled"
    ).scalar() or 0

    return {
        "total_orders": total_orders,
        "total_paid_orders": total_paid_orders,
        "total_revenue": round(float(total_revenue), 2),
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders
    }
    
    

# VIEW ORDER BY ID
@router.get("/{order_id}")
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == user_id
        )
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "coupon_code": order.coupon_code,
        "discount_amount": order.discount_amount,
        "status": order.status,
        "payment_status": order.payment_status,
        "created_at": order.created_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal
            }
            for item in items
        ]
    }



# -----------------------------------------
# ADMIN - VIEW ALL ORDERS
# -----------------------------------------

@router.get("/admin/all")
def get_all_orders(
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []

    for order in orders:

        items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()

        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "coupon_code": order.coupon_code,
            "discount_amount": order.discount_amount,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal
                }
                for item in items
            ]
        })

    return result


#Order status Updation Endpoint 
@router.patch("/admin/{order_id}/status")
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    allowed_transitions = {
        "confirmed": ["processing"],
        "processing": ["shipped"],
        "shipped": ["out_for_delivery"],
        "out_for_delivery": ["delivered"]
    }

    new_status = status_data.status.lower().strip()

    if new_status not in allowed_transitions.get(order.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change order status from {order.status} to {new_status}"
        )

    order.status = new_status

    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "status": order.status
    }
    
    

# Return Request Endpoint
@router.post(
    "/{order_id}/return-request",
    response_model=ReturnRequestResponse,
    status_code=status.HTTP_201_CREATED
)
def create_return_request(
    order_id: int,
    request_data: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Find the order belonging to the logged-in customer
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user["user_id"]
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Only delivered orders can be returned
    if order.status != "delivered":
        raise HTTPException(
            status_code=400,
            detail="Return request is allowed only for delivered orders"
        )

    # Prevent duplicate pending return requests
    existing_request = db.query(ReturnRequest).filter(
        ReturnRequest.order_id == order_id,
        ReturnRequest.user_id == current_user["user_id"],
        ReturnRequest.status == "pending"
    ).first()

    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="A pending return request already exists for this order"
        )

    return_request = ReturnRequest(
        order_id=order_id,
        user_id=current_user["user_id"],
        reason=request_data.reason,
        status="pending"
    )

    db.add(return_request)
    db.commit()
    db.refresh(return_request)

    return return_request



# Return Requests Approving by Admin endpoint
@router.patch(
    "/return-requests/admin/{request_id}",
    response_model=ReturnRequestResponse
)
def review_return_request(
    request_id: int,
    review_data: ReturnRequestReview,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    return_request = db.query(ReturnRequest).filter(
        ReturnRequest.id == request_id
    ).first()

    if not return_request:
        raise HTTPException(
            status_code=404,
            detail="Return request not found"
        )

    if return_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="This return request has already been reviewed"
        )

    new_status = review_data.status.lower().strip()

    if new_status not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be approved or rejected"
        )

    return_request.status = new_status

    db.commit()
    db.refresh(return_request)

    return return_request



# Admin can view all Return Requests
@router.get(
    "/return-requests/admin/all",
    response_model=list[ReturnRequestResponse]
)
def get_all_return_requests(
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    requests = (
        db.query(ReturnRequest)
        .order_by(ReturnRequest.created_at.desc())
        .all()
    )

    return requests

