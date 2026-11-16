# Inventory and Order Management System

A microservices-based Inventory and Order Management System built using **React, FastAPI, SQLite, Redis, RabbitMQ, Celery, Stripe, and Docker**.

## 1. Technologies Used

- **Frontend:** React.js, Vite
- **Backend:** Python, FastAPI
- **Database:** SQLite, SQLAlchemy
- **Authentication:** JWT
- **Payment:** Stripe Test Mode
- **Caching:** Redis
- **Message Broker:** RabbitMQ
- **Background Tasks:** Celery
- **Containerization:** Docker and Docker Compose
- **API Testing:** Postman

## 2. Project Features

### Customer
- Register and login.
- Browse products.
- Add, update, and remove cart items.
- Apply discount coupons.
- Place orders.
- Make payments using Stripe Test Mode.
- View order history and track orders.
- Request product returns.

### Admin
- Manage products.
- Manage inventory and stock.
- View and manage customer orders.
- Update order status.
- Approve or reject return requests.
- View sales summary.

## 3. Project Structure

```text
Inventory_Order_Management_System/
│
├── services/
│   ├── auth_service/
│   ├── product_service/
│   ├── order_service/
│   └── notification_service/
│
├── frontend/
│
├── postman_collection.json
├── requirements.txt
├── docker-compose.yml
├── .dockerignore
├── .env
└── README.md
```

Each backend service has its own database:

- `auth.db`
- `product.db`
- `order.db`

## 4. Prerequisites

Install the following:

1. Python 3.12+
2. Node.js and npm
3. Docker Desktop
4. Postman

**Note:** Docker Desktop must be running before starting the project.

## 5. Environment Setup

Create a `.env` file in the project root (same location as `docker-compose.yml`).

Add the following:

```env
JWT_SECRET_KEY=your_long_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

RABBITMQ_PASSWORD=your_strong_password

STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
```

Replace the Stripe placeholders with your Stripe Test Mode API keys.

## 6. How to Run the Project

### Step 1: Open the project

Open PowerShell and navigate to the project directory:

```powershell
cd D:\Inventory_Order_Management_System
```

### Step 2: Start Docker Desktop

Make sure Docker Desktop is running.

### Step 3: Build and start all services

Run:

```powershell
docker compose up --build -d
```

This command builds the images and starts all application services.

### Step 4: Check running containers

```powershell
docker compose ps
```

Make sure all services are running.

### Step 5: Open the application

**Frontend:**

http://localhost:5173

**Backend Swagger Documentation:**

| Service | URL |
|---|---|
| Authentication | http://localhost:8001/docs |
| Product | http://localhost:8002/docs |
| Order | http://localhost:8003/docs |

**RabbitMQ Management:**

http://localhost:15672

Username: `app_user`

Password: The value configured in `.env`.

## 7. Docker Commands

**Start the project:**

```powershell
docker compose up -d
```

**Stop the project:**

```powershell
docker compose down
```

**View all containers:**

```powershell
docker compose ps
```

**View logs:**

```powershell
docker compose logs -f
```

**View a particular service's logs:**

```powershell
docker compose logs -f auth_service
```

Replace `auth_service` with `product_service`, `order_service`, or `notification_service` as needed.

**Rebuild after dependency or Dockerfile changes:**

```powershell
docker compose up --build -d
```

Note: Avoid `docker compose down -v` if you want to preserve RabbitMQ and Redis volume data.

## 8. API Testing Using Postman

The project includes a Postman collection:

```text
postman_collection.json
```

### Import Instructions

1. Open Postman.
2. Click **Import**.
3. Select `postman_collection.json`.
4. Import the collection.
5. Start testing the APIs.

The collection includes tests for:

- User registration and login.
- JWT authentication.
- Product management.
- Inventory management.
- Cart operations.
- Coupon validation.
- Checkout and order management.
- Stripe payment.
- Return requests.
- Admin operations.
- Positive and negative API test cases.

Some requests require an admin token or data created by earlier requests. Follow the collection's testing sequence.

## 9. Important Notes

- Each microservice manages its own SQLite database.
- JWT is used to authenticate protected API requests.
- Redis is used for product caching and Celery task processing.
- RabbitMQ handles order and payment events.
- Celery executes notification tasks asynchronously.
- Stripe is configured for Test Mode only.
- Notifications are currently demonstrated through background task processing; external email/SMS delivery is not configured.
- Automatic Stripe refunds and stock restoration after return approval are not implemented.

## 10. Project Summary

This project demonstrates microservices architecture, REST API development, database management, authentication, inventory management, payment integration, event-driven communication, caching, background task processing, API testing, and Docker containerization.

**Project:** Inventory and Order Management System  
**Backend:** FastAPI  
**Frontend:** React  
**Database:** SQLite  
**Architecture:** Microservices  
**Execution:** Docker Compose