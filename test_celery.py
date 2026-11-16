from services.notification_service.tasks import send_order_notification

result = send_order_notification.delay(
    order_id=101,
    user_id=5,
    total_amount=900.0
)

print("Task sent successfully!")
print("Task ID:", result.id)