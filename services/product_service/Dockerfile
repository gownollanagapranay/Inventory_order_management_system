
FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /app/data

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/product_service/ /app/services/product_service/

EXPOSE 8002

CMD ["uvicorn", "services.product_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
