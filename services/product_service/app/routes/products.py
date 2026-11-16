from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json

from ..database import get_db
from ..models import Product
from ..schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    StockUpdate,
    StockDecrease
)
from ..dependencies import get_current_user, require_role
from ..redis_client import redis_client


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# =========================================================
# REDIS CACHE KEYS
# =========================================================

PRODUCT_LIST_CACHE_KEY = "products:all"


def product_cache_key(product_id: int):
    return f"product:{product_id}"


def clear_product_cache(product_id: int | None = None):
    """
    Remove product cache after product data changes.
    """

    # Clear all-products cache
    redis_client.delete(PRODUCT_LIST_CACHE_KEY)

    # Clear individual product cache if product_id is provided
    if product_id is not None:
        redis_client.delete(product_cache_key(product_id))


# =========================================================
# GET ALL PRODUCTS
# =========================================================

@router.get("/", response_model=list[ProductResponse])
def get_products(
    db: Session = Depends(get_db)
):
    # -----------------------------------------
    # 1. Check Redis cache
    # -----------------------------------------

    cached_products = redis_client.get(PRODUCT_LIST_CACHE_KEY)

    if cached_products:
        print("Redis CACHE HIT - Returning products from Redis")

        return json.loads(cached_products)

    # -----------------------------------------
    # 2. Cache MISS -> Get data from database
    # -----------------------------------------

    print("Redis CACHE MISS - Fetching products from database")

    products = db.query(Product).all()

    # -----------------------------------------
    # 3. Convert SQLAlchemy objects to dictionaries
    # -----------------------------------------

    products_data = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "image_url": product.image_url,
            "category": product.category,
            "price": product.price,
            "stock_quantity": product.stock_quantity,
            "low_stock_threshold": product.low_stock_threshold
        }
        for product in products
    ]

    # -----------------------------------------
    # 4. Store result in Redis
    # -----------------------------------------

    redis_client.set(
    PRODUCT_LIST_CACHE_KEY,
    json.dumps(products_data),
    ex=60
    )

    print("Products stored in Redis cache")

    return products


# =========================================================
# LOW STOCK PRODUCTS
# =========================================================

@router.get(
    "/inventory/low-stock",
    response_model=list[ProductResponse]
)
def get_low_stock_products(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    products = db.query(Product).filter(
        Product.stock_quantity <= Product.low_stock_threshold
    ).all()

    return products


# =========================================================
# GET SINGLE PRODUCT
# =========================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    # -----------------------------------------
    # 1. Check Redis
    # -----------------------------------------

    cache_key = product_cache_key(product_id)

    cached_product = redis_client.get(cache_key)

    if cached_product:
        print(
            f"Redis CACHE HIT - Product {product_id}"
        )

        return json.loads(cached_product)

    # -----------------------------------------
    # 2. Cache MISS -> Database
    # -----------------------------------------

    print(
        f"Redis CACHE MISS - Product {product_id}"
    )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # -----------------------------------------
    # 3. Convert to dictionary
    # -----------------------------------------

    product_data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_url": product.image_url,
        "category": product.category,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "low_stock_threshold": product.low_stock_threshold
    }

    # -----------------------------------------
    # 4. Store in Redis
    # -----------------------------------------

    redis_client.set(
    cache_key,
    json.dumps(product_data),
    ex=60
    )

    print(
        f"Product {product_id} stored in Redis cache"
    )

    return product


# =========================================================
# CREATE PRODUCT
# =========================================================

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    product = Product(
        name=product_data.name.strip(),
        description=product_data.description,
        image_url=product_data.image_url,
        category=product_data.category.strip(),
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
        low_stock_threshold=product_data.low_stock_threshold
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    # Product list changed
    clear_product_cache()

    return product


# =========================================================
# UPDATE PRODUCT
# =========================================================

@router.put(
    "/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    update_data = product_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():

        if isinstance(value, str):
            value = value.strip()

        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    # Product changed
    clear_product_cache(product_id)

    return product


# =========================================================
# DELETE PRODUCT
# =========================================================

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    # Product removed
    clear_product_cache(product_id)

    return {
        "message": "Product deleted successfully"
    }


# =========================================================
# UPDATE STOCK
# =========================================================

@router.patch(
    "/{product_id}/stock",
    response_model=ProductResponse
)
def update_stock(
    product_id: int,
    stock_data: StockUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.stock_quantity = stock_data.quantity

    db.commit()
    db.refresh(product)

    # Stock changed
    clear_product_cache(product_id)

    return product


# =========================================================
# DECREASE STOCK
# =========================================================

@router.post(
    "/{product_id}/stock/decrease",
    response_model=ProductResponse
)
def decrease_stock(
    product_id: int,
    stock_data: StockDecrease,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if product.stock_quantity < stock_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock"
        )

    product.stock_quantity -= stock_data.quantity

    db.commit()
    db.refresh(product)

    # Stock changed
    clear_product_cache(product_id)

    return product
