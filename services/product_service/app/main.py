from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models
from .routes.products import router as product_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Product and Inventory Service",
    description="Product catalog and inventory management microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(product_router)


@app.get("/")
def root():
    return {
        "message": "Product and Inventory Service is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }