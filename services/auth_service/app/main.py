
from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routes.auth import router as auth_router


# Create database tables for imported SQLAlchemy models.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Authentication Service",
    description="Authentication and authorization microservice"
)


# Register authentication endpoints.
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "Authentication Service is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
