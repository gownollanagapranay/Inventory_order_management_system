
FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /app/data

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/order_service/ /app/services/order_service/

EXPOSE 8003

CMD ["uvicorn", "services.order_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
