import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.product_service.app.main import app
from services.product_service.app.database import Base, get_db
from services.product_service.app.dependencies import get_current_user
from services.product_service.app.redis_client import redis_client

from services.order_service.app.database import Base as OrderBase, get_db as get_order_db
from services.order_service.app.main import app as order_app
from services.order_service.app.dependencies import get_current_user as get_order_current_user


@pytest.fixture
def client(tmp_path):

    # Create a separate temporary SQLite database
    test_database = tmp_path / "test_product.db"

    test_database_url = f"sqlite:///{test_database.as_posix()}"

    test_engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    # Create tables in the test database
    Base.metadata.create_all(bind=test_engine)

    # Override the application's database dependency
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    # Simulate an authenticated admin user
    def override_get_current_user():
        return {
            "user_id": 1,
            "role": "admin"
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Clear product cache before each test
    clear_test_cache()

    with TestClient(app) as test_client:
        yield test_client

    # Clean up after the test
    app.dependency_overrides.clear()

    clear_test_cache()

    test_engine.dispose()


def clear_test_cache():

    redis_client.delete("products:all")

    cached_keys = list(
        redis_client.scan_iter(match="product:*")
    )

    if cached_keys:
        redis_client.delete(*cached_keys)
        
        


@pytest.fixture
def order_client(tmp_path):

    # Create a separate temporary Order database
    test_database = tmp_path / "test_order.db"

    test_database_url = f"sqlite:///{test_database.as_posix()}"

    test_engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    # Create Order Service tables
    OrderBase.metadata.create_all(bind=test_engine)

    # Override database dependency
    def override_order_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    # Simulate authenticated customer
    def override_order_current_user():
        return {
            "user_id": 1,
            "role": "customer"
        }

    order_app.dependency_overrides[get_order_db] = override_order_db

    order_app.dependency_overrides[
        get_order_current_user
    ] = override_order_current_user

    with TestClient(order_app) as test_client:
        yield test_client

    # Remove dependency overrides
    order_app.dependency_overrides.clear()

    test_engine.dispose()


