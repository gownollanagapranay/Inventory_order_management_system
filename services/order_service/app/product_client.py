import httpx

from fastapi import HTTPException, status

from .settings import settings


def get_product(product_id: int):

    url = (
        f"{settings.PRODUCT_SERVICE_URL}"
        f"/products/{product_id}"
    )

    try:
        response = httpx.get(
            url,
            timeout=5.0
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product service is unavailable"
        )

    if response.status_code == 404:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve product information"
        )

    return response.json()


def decrease_product_stock(
    product_id: int,
    quantity: int
):

    url = (
        f"{settings.PRODUCT_SERVICE_URL}"
        f"/products/{product_id}/stock/decrease"
    )

    try:
        response = httpx.post(
            url,
            json={
                "quantity": quantity
            },
            timeout=5.0
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product service is unavailable"
        )

    if response.status_code == 404:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if response.status_code == 400:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock"
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to update product inventory"
        )

    return response.json()