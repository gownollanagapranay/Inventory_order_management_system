from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models
from .routes import cart, orders, coupons

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Order Service",
    description="Cart and Order Management Microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(cart.router)

app.include_router(orders.router)

app.include_router(coupons.router)


@app.get("/")
def root():

    return {
        "message": "Order Service is running"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }