
# =====================================================
#           PRODUCTS TESTS
# =====================================================


# TEST 1: ROOT ENDPOINT

def test_root(client):

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Product and Inventory Service is running"
    }


# TEST 2: HEALTH CHECK

def test_health_check(client):

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy"
    }


# TEST 3: GET ALL PRODUCTS

def test_get_products(client):

    response = client.get("/products/")

    assert response.status_code == 200

    assert response.json() == []


# TEST 4: CREATE PRODUCT

def test_create_product(client):

    product_data = {
        "name": "Test Laptop",
        "description": "Laptop created during testing",
        "category": "Electronics",
        "price": 50000,
        "stock_quantity": 10,
        "low_stock_threshold": 5
    }

    response = client.post(
        "/products/",
        json=product_data
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Laptop"
    assert data["category"] == "Electronics"
    assert data["price"] == 50000
    assert data["stock_quantity"] == 10

    assert "id" in data


# TEST 5: GET PRODUCT BY ID

def test_get_product_by_id(client):

    product_data = {
        "name": "Test Mobile",
        "description": "Test mobile phone",
        "category": "Electronics",
        "price": 20000,
        "stock_quantity": 15,
        "low_stock_threshold": 3
    }

    create_response = client.post(
        "/products/",
        json=product_data
    )

    product_id = create_response.json()["id"]

    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    assert response.json()["name"] == "Test Mobile"



# TEST 6: UPDATE PRODUCT


def test_update_product(client):

    product_data = {
        "name": "Old Laptop",
        "description": "Old description",
        "category": "Electronics",
        "price": 40000,
        "stock_quantity": 10,
        "low_stock_threshold": 5
    }

    create_response = client.post(
        "/products/",
        json=product_data
    )

    product_id = create_response.json()["id"]

    update_data = {
        "name": "Updated Laptop",
        "price": 55000
    }

    response = client.put(
        f"/products/{product_id}",
        json=update_data
    )

    assert response.status_code == 200

    assert response.json()["name"] == "Updated Laptop"
    assert response.json()["price"] == 55000



# TEST 7: DELETE PRODUCT


def test_delete_product(client):

    product_data = {
        "name": "Delete Laptop",
        "description": "Product to delete",
        "category": "Electronics",
        "price": 30000,
        "stock_quantity": 5,
        "low_stock_threshold": 2
    }

    create_response = client.post(
        "/products/",
        json=product_data
    )

    product_id = create_response.json()["id"]

    response = client.delete(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Product deleted successfully"
    }



# TEST 8: PRODUCT NOT FOUND


def test_product_not_found(client):

    response = client.get("/products/99999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Product not found"
    }


# TEST 9: INVALID PRODUCT DATA


def test_create_product_with_invalid_data(client):

    product_data = {
        "name": "A",
        "description": "Invalid product",
        "category": "Electronics",
        "price": -100,
        "stock_quantity": 10,
        "low_stock_threshold": 5
    }

    response = client.post(
        "/products/",
        json=product_data
    )

    assert response.status_code == 422
    
    

# =====================================================
#                  INVENTORY TESTS
# =====================================================


def create_test_product(client, stock=10, threshold=5):

    product_data = {
        "name": "Inventory Test Product",
        "description": "Product for inventory testing",
        "category": "Electronics",
        "price": 1000,
        "stock_quantity": stock,
        "low_stock_threshold": threshold
    }

    response = client.post(
        "/products/",
        json=product_data
    )

    assert response.status_code == 201

    return response.json()["id"]


# TEST 10: ADMIN UPDATES STOCK

def test_update_stock(client):

    product_id = create_test_product(client)

    response = client.patch(
        f"/products/{product_id}/stock",
        json={"quantity": 50}
    )

    assert response.status_code == 200
    assert response.json()["stock_quantity"] == 50


# TEST 11: GET LOW-STOCK PRODUCTS

def test_get_low_stock_products(client):

    create_test_product(
        client,
        stock=2,
        threshold=5
    )

    response = client.get(
        "/products/inventory/low-stock"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["stock_quantity"] == 2


# TEST 12: DECREASE STOCK SUCCESSFULLY

def test_decrease_stock(client):

    product_id = create_test_product(
        client,
        stock=10
    )

    response = client.post(
        f"/products/{product_id}/stock/decrease",
        json={"quantity": 3}
    )

    assert response.status_code == 200
    assert response.json()["stock_quantity"] == 7


# TEST 13: INSUFFICIENT STOCK

def test_decrease_insufficient_stock(client):

    product_id = create_test_product(
        client,
        stock=5
    )

    response = client.post(
        f"/products/{product_id}/stock/decrease",
        json={"quantity": 10}
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Insufficient stock"
    }


# TEST 14: DECREASE STOCK FOR NONEXISTENT PRODUCT

def test_decrease_stock_product_not_found(client):

    response = client.post(
        "/products/99999/stock/decrease",
        json={"quantity": 2}
    )

    assert response.status_code == 404


# TEST 15: CUSTOMER CANNOT UPDATE STOCK


def test_customer_cannot_update_stock(client):

    from services.product_service.app.dependencies import (
        get_current_user
    )

    # First create product while default user is admin
    product_id = create_test_product(client)

    # Now change the user to customer
    def override_customer():
        return {
            "user_id": 2,
            "role": "customer"
        }

    client.app.dependency_overrides[
        get_current_user
    ] = override_customer

    # Customer attempts to update stock
    response = client.patch(
        f"/products/{product_id}/stock",
        json={"quantity": 50}
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "You do not have permission to perform this action"
    }



# TEST 16: CUSTOMER CANNOT VIEW LOW-STOCK INVENTORY

def test_customer_cannot_view_low_stock(client):

    from services.product_service.app.dependencies import (
        get_current_user
    )

    def override_customer():
        return {
            "user_id": 2,
            "role": "customer"
        }

    client.app.dependency_overrides[
        get_current_user
    ] = override_customer

    response = client.get(
        "/products/inventory/low-stock"
    )

    assert response.status_code == 403



# =====================================================
#           PRODUCTS TESTS
# =====================================================


def test_product_list_is_cached(client):
    # Create a product
    product_id = create_test_product(client)

    # Make first request
    response = client.get("/products/")

    assert response.status_code == 200

    # Redis should now contain the product list
    from services.product_service.app.redis_client import redis_client

    cached_data = redis_client.get("products:all")

    assert cached_data is not None

    # Make sure cached data is valid JSON
    import json

    cached_products = json.loads(cached_data)

    assert isinstance(cached_products, list)

    # Make sure our product exists in the cached data
    assert any(
        product["id"] == product_id
        for product in cached_products
    )


def test_individual_product_is_cached(client):
    # Create a product
    product_id = create_test_product(client)

    # First request
    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    from services.product_service.app.redis_client import redis_client

    cache_key = f"product:{product_id}"

    cached_data = redis_client.get(cache_key)

    assert cached_data is not None

    import json

    cached_product = json.loads(cached_data)

    assert cached_product["id"] == product_id


def test_update_product_clears_individual_cache(client):
    # Create product
    product_id = create_test_product(client)

    # Populate individual cache
    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    from services.product_service.app.redis_client import redis_client

    cache_key = f"product:{product_id}"

    # Confirm cache exists
    assert redis_client.get(cache_key) is not None

    # Update product
    response = client.put(
        f"/products/{product_id}",
        json={
            "name": "Updated Product",
            "price": 150.0
        }
    )

    assert response.status_code == 200

    # Cache should be removed
    assert redis_client.get(cache_key) is None


def test_update_stock_clears_individual_cache(client):
    # Create product
    product_id = create_test_product(client)

    # Populate cache
    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    from services.product_service.app.redis_client import redis_client

    cache_key = f"product:{product_id}"

    assert redis_client.get(cache_key) is not None

    # Update stock
    response = client.patch(
        f"/products/{product_id}/stock",
        json={
            "quantity": 50
        }
    )

    assert response.status_code == 200

    # Cache should be cleared
    assert redis_client.get(cache_key) is None


def test_delete_product_clears_individual_cache(client):
    # Create product
    product_id = create_test_product(client)

    # Populate cache
    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    from services.product_service.app.redis_client import redis_client

    cache_key = f"product:{product_id}"

    assert redis_client.get(cache_key) is not None

    # Delete product
    response = client.delete(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    # Cache should be removed
    assert redis_client.get(cache_key) is None


def test_decrease_stock_clears_individual_cache(client):
    # Create product with stock 10
    product_id = create_test_product(
        client,
        stock=10
    )

    # Populate cache
    response = client.get(
        f"/products/{product_id}"
    )

    assert response.status_code == 200

    from services.product_service.app.redis_client import redis_client

    cache_key = f"product:{product_id}"

    assert redis_client.get(cache_key) is not None

    # Decrease stock
    response = client.post(
        f"/products/{product_id}/stock/decrease",
        json={
            "quantity": 2
        }
    )

    assert response.status_code == 200

    # Cache should be cleared
    assert redis_client.get(cache_key) is None
    
    

