from unittest.mock import patch
from types import SimpleNamespace


def test_order_service_root(order_client):

    response = order_client.get("/")

    assert response.status_code == 200
    

def test_get_empty_cart(order_client):

    response = order_client.get("/cart/")

    assert response.status_code == 200
    assert response.json() == []


def test_add_item_to_cart(order_client):

    response = order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == 101
    assert data["quantity"] == 2


def test_get_cart_items(order_client):

    # Add an item
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    # Retrieve cart
    response = order_client.get("/cart/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["product_id"] == 101
    assert data[0]["quantity"] == 2


def test_add_same_product_increases_quantity(order_client):

    # First addition
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    # Add the same product again
    response = order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 3
        }
    )

    assert response.status_code == 201

    data = response.json()

    # Quantity should become 2 + 3 = 5
    assert data["quantity"] == 5

    # Only one cart entry should exist
    cart_response = order_client.get("/cart/")

    assert len(cart_response.json()) == 1


def test_update_cart_item_quantity(order_client):

    # Add product
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    # Update quantity
    response = order_client.put(
        "/cart/101",
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == 101
    assert data["quantity"] == 5


def test_remove_cart_item(order_client):

    # Add product
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    # Remove product
    response = order_client.delete("/cart/101")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Product removed from cart"
    }

    # Verify cart is empty
    cart_response = order_client.get("/cart/")

    assert cart_response.json() == []


def test_update_nonexistent_cart_item(order_client):

    response = order_client.put(
        "/cart/999",
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Product not found in cart"


def test_remove_nonexistent_cart_item(order_client):

    response = order_client.delete("/cart/999")

    assert response.status_code == 404

    assert response.json()["detail"] == "Product not found in cart"





# -----------------------------------------
# CHECKOUT TESTS
# -----------------------------------------


def test_checkout_success(order_client):

    # Step 1: Add product to cart
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    # Step 2: Mock external service calls
    with patch(
        "services.order_service.app.routes.orders.get_product"
    ) as mock_get_product, patch(
        "services.order_service.app.routes.orders.decrease_product_stock"
    ) as mock_decrease_stock, patch(
        "services.order_service.app.routes.orders.publish_order_created"
    ) as mock_publish:

        mock_get_product.return_value = {
            "id": 101,
            "price": 500.0,
            "stock_quantity": 10
        }

        mock_decrease_stock.return_value = None
        mock_publish.return_value = None

        # Step 3: Checkout
        response = order_client.post(
            "/orders/checkout",
            json={}
        )

    # Step 4: Verify response
    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == 1
    assert data["total_amount"] == 1000.0
    assert data["status"] == "pending_payment"
    assert data["payment_status"] == "pending"

    assert len(data["items"]) == 1

    assert data["items"][0]["product_id"] == 101
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price"] == 500.0
    assert data["items"][0]["subtotal"] == 1000.0

    # Step 5: Verify external calls
    mock_get_product.assert_called_once_with(101)

    mock_decrease_stock.assert_called_once_with(
        product_id=101,
        quantity=2
    )

    mock_publish.assert_called_once()

    # Step 6: Verify cart is cleared
    cart_response = order_client.get("/cart/")

    assert cart_response.status_code == 200
    assert cart_response.json() == []



def test_checkout_empty_cart(order_client):

    # Checkout without adding any product
    response = order_client.post(
        "/orders/checkout",
        json={}
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Cart is empty"


def test_checkout_insufficient_stock(order_client):

    # Add product to cart
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 5
        }
    )

    with patch(
        "services.order_service.app.routes.orders.get_product"
    ) as mock_get_product, patch(
        "services.order_service.app.routes.orders.decrease_product_stock"
    ) as mock_decrease_stock, patch(
        "services.order_service.app.routes.orders.publish_order_created"
    ) as mock_publish:

        # Only 2 items available
        mock_get_product.return_value = {
            "id": 101,
            "price": 500.0,
            "stock_quantity": 2
        }

        response = order_client.post(
            "/orders/checkout",
            json={}
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Insufficient stock for product 101"
    )

    # Stock must not be reduced
    mock_decrease_stock.assert_not_called()

    # No order should be published
    mock_publish.assert_not_called()

    # Cart should remain unchanged
    cart_response = order_client.get("/cart/")

    assert len(cart_response.json()) == 1
    assert cart_response.json()[0]["quantity"] == 5


def test_checkout_with_coupon_discount(order_client):

    # Add product to cart
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    with patch(
        "services.order_service.app.routes.orders.get_product"
    ) as mock_get_product, patch(
        "services.order_service.app.routes.orders.decrease_product_stock"
    ) as mock_decrease_stock, patch(
        "services.order_service.app.routes.orders.publish_order_created"
    ) as mock_publish, patch(
        "services.order_service.app.routes.orders.calculate_coupon_discount"
    ) as mock_coupon:

        mock_get_product.return_value = {
            "id": 101,
            "price": 500.0,
            "stock_quantity": 10
        }

        mock_decrease_stock.return_value = None
        mock_publish.return_value = None

        # Simulate a coupon giving Rs. 200 discount
        mock_coupon.return_value = (
            None,
            200.0,
            800.0
        )

        response = order_client.post(
            "/orders/checkout",
            json={
                "coupon_code": "save20"
            }
        )

    assert response.status_code == 201

    data = response.json()

    assert data["total_amount"] == 800.0
    assert data["coupon_code"] == "SAVE20"
    assert data["discount_amount"] == 200.0

    # Verify coupon calculation was requested
    mock_coupon.assert_called_once()

    # Verify inventory reduction
    mock_decrease_stock.assert_called_once()

    # Verify event publishing
    mock_publish.assert_called_once()


def test_checkout_invalid_coupon(order_client):

    # Add product to cart
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    with patch(
        "services.order_service.app.routes.orders.get_product"
    ) as mock_get_product, patch(
        "services.order_service.app.routes.orders.decrease_product_stock"
    ) as mock_decrease_stock, patch(
        "services.order_service.app.routes.orders.publish_order_created"
    ) as mock_publish, patch(
        "services.order_service.app.routes.orders.calculate_coupon_discount"
    ) as mock_coupon:

        mock_get_product.return_value = {
            "id": 101,
            "price": 500.0,
            "stock_quantity": 10
        }

        from fastapi import HTTPException

        mock_coupon.side_effect = HTTPException(
            status_code=400,
            detail="Invalid coupon code"
        )

        response = order_client.post(
            "/orders/checkout",
            json={
                "coupon_code": "INVALID"
            }
        )

    assert response.status_code == 400

    assert response.json()["detail"] == "Invalid coupon code"

    # Coupon validation happens before stock reduction
    mock_decrease_stock.assert_not_called()

    mock_publish.assert_not_called()

    # Cart should remain unchanged
    cart_response = order_client.get("/cart/")

    assert len(cart_response.json()) == 1




def create_pending_test_order(order_client):

    # Add a product to the cart
    order_client.post(
        "/cart/",
        json={
            "product_id": 101,
            "quantity": 2
        }
    )

    # Mock Product Service and RabbitMQ
    with patch(
        "services.order_service.app.routes.orders.get_product"
    ) as mock_get_product, patch(
        "services.order_service.app.routes.orders.decrease_product_stock"
    ), patch(
        "services.order_service.app.routes.orders.publish_order_created"
    ):

        mock_get_product.return_value = {
            "id": 101,
            "price": 500.0,
            "stock_quantity": 10
        }

        response = order_client.post(
            "/orders/checkout",
            json={}
        )

    assert response.status_code == 201

    return response.json()["id"]


def initiate_test_payment(order_client, order_id):

    with patch(
        "services.order_service.app.routes.orders.create_payment_intent"
    ) as mock_create_payment:

        mock_create_payment.return_value = SimpleNamespace(
            id="pi_test_123",
            client_secret="test_client_secret"
        )

        response = order_client.post(
            f"/orders/{order_id}/payment"
        )

    return response



# -----------------------------------------
# PAYMENT CREATION TESTS
# -----------------------------------------

def test_create_payment_success(order_client):

    order_id = create_pending_test_order(order_client)

    with patch(
        "services.order_service.app.routes.orders.create_payment_intent"
    ) as mock_create_payment:

        mock_create_payment.return_value = SimpleNamespace(
            id="pi_test_123",
            client_secret="test_client_secret"
        )

        response = order_client.post(
            f"/orders/{order_id}/payment"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["order_id"] == order_id
    assert data["payment_intent_id"] == "pi_test_123"
    assert data["client_secret"] == "test_client_secret"
    assert data["amount"] == 1000.0
    assert data["currency"] == "inr"

    mock_create_payment.assert_called_once_with(
        amount=1000.0,
        order_id=order_id
    )


def test_create_payment_order_not_found(order_client):

    response = order_client.post(
        "/orders/999/payment"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_create_payment_already_paid(order_client):

    order_id = create_pending_test_order(order_client)

    # Initiate payment
    initiate_test_payment(order_client, order_id)

    # Mock successful Stripe verification
    with patch(
        "services.order_service.app.routes.orders.stripe.PaymentIntent.retrieve"
    ) as mock_retrieve, patch(
        "services.order_service.app.routes.orders.publish_order_paid"
    ):

        mock_retrieve.return_value = SimpleNamespace(
            status="succeeded",
            amount_received=100000,
            currency="inr",
            metadata=SimpleNamespace(
                order_id=str(order_id)
            )
        )

        verify_response = order_client.post(
            f"/orders/{order_id}/verify-payment"
        )

    assert verify_response.status_code == 200

    # Try creating another payment for the paid order
    response = order_client.post(
        f"/orders/{order_id}/payment"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Order is already paid"
    
    

# -----------------------------------------
# PAYMENT VERIFICATION TESTS
# -----------------------------------------


def test_verify_payment_success(order_client):

    order_id = create_pending_test_order(order_client)

    initiate_test_payment(order_client, order_id)

    with patch(
        "services.order_service.app.routes.orders.stripe.PaymentIntent.retrieve"
    ) as mock_retrieve, patch(
        "services.order_service.app.routes.orders.publish_order_paid"
    ) as mock_publish:

        mock_retrieve.return_value = SimpleNamespace(
            status="succeeded",
            amount_received=100000,
            currency="inr",
            metadata=SimpleNamespace(
                order_id=str(order_id)
            )
        )

        response = order_client.post(
            f"/orders/{order_id}/verify-payment"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Payment verified successfully"
    assert data["order_id"] == order_id
    assert data["payment_status"] == "paid"
    assert data["order_status"] == "confirmed"
    assert data["amount"] == 1000.0

    mock_retrieve.assert_called_once_with("pi_test_123")
    mock_publish.assert_called_once()


def test_verify_payment_not_initiated(order_client):

    order_id = create_pending_test_order(order_client)

    response = order_client.post(
        f"/orders/{order_id}/verify-payment"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment has not been initiated"
    )


def test_verify_payment_not_successful(order_client):

    order_id = create_pending_test_order(order_client)

    initiate_test_payment(order_client, order_id)

    with patch(
        "services.order_service.app.routes.orders.stripe.PaymentIntent.retrieve"
    ) as mock_retrieve:

        mock_retrieve.return_value = SimpleNamespace(
            status="requires_payment_method",
            amount_received=0,
            currency="inr",
            metadata=SimpleNamespace(
                order_id=str(order_id)
            )
        )

        response = order_client.post(
            f"/orders/{order_id}/verify-payment"
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment is not successful. Current status: "
        "requires_payment_method"
    )


def test_verify_payment_amount_mismatch(order_client):

    order_id = create_pending_test_order(order_client)

    initiate_test_payment(order_client, order_id)

    with patch(
        "services.order_service.app.routes.orders.stripe.PaymentIntent.retrieve"
    ) as mock_retrieve:

        mock_retrieve.return_value = SimpleNamespace(
            status="succeeded",
            amount_received=50000,
            currency="inr",
            metadata=SimpleNamespace(
                order_id=str(order_id)
            )
        )

        response = order_client.post(
            f"/orders/{order_id}/verify-payment"
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment amount or currency does not match the order"
    )


def test_verify_payment_wrong_currency(order_client):

    order_id = create_pending_test_order(order_client)

    initiate_test_payment(order_client, order_id)

    with patch(
        "services.order_service.app.routes.orders.stripe.PaymentIntent.retrieve"
    ) as mock_retrieve:

        mock_retrieve.return_value = SimpleNamespace(
            status="succeeded",
            amount_received=100000,
            currency="usd",
            metadata=SimpleNamespace(
                order_id=str(order_id)
            )
        )

        response = order_client.post(
            f"/orders/{order_id}/verify-payment"
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment amount or currency does not match the order"
    )


def test_verify_payment_wrong_order_metadata(order_client):

    order_id = create_pending_test_order(order_client)

    initiate_test_payment(order_client, order_id)

    with patch(
        "services.order_service.app.routes.orders.stripe.PaymentIntent.retrieve"
    ) as mock_retrieve:

        mock_retrieve.return_value = SimpleNamespace(
            status="succeeded",
            amount_received=100000,
            currency="inr",
            metadata=SimpleNamespace(
                order_id="999"
            )
        )

        response = order_client.post(
            f"/orders/{order_id}/verify-payment"
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment does not match this order"
    )
    
