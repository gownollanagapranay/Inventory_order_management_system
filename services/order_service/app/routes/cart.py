from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CartItem
from ..schemas import CartItemCreate, CartItemUpdate, CartItemResponse
from ..dependencies import get_current_user


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.get("/", response_model=list[CartItemResponse])
def get_cart(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()

    return cart_items



@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    cart_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    existing_item = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == cart_data.product_id
    ).first()

    if existing_item:

        existing_item.quantity += cart_data.quantity

        db.commit()
        db.refresh(existing_item)

        return existing_item

    cart_item = CartItem(
        user_id=user_id,
        product_id=cart_data.product_id,
        quantity=cart_data.quantity
    )

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return cart_item



@router.put("/{product_id}", response_model=CartItemResponse)
def update_cart_item(
    product_id: int,
    cart_data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    cart_item = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id
    ).first()

    if cart_item is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )

    cart_item.quantity = cart_data.quantity

    db.commit()
    db.refresh(cart_item)

    return cart_item



@router.delete("/{product_id}")
def remove_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    cart_item = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id
    ).first()

    if cart_item is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Product removed from cart"
    }