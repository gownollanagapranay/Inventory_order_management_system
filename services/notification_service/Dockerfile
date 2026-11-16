
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/notification_service/ /app/services/notification_service/

CMD ["python", "-m", "services.notification_service.main"]
