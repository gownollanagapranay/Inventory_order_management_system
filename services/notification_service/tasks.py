from .celery_app import celery_app


@celery_app.task
def send_order_notification(order_id, user_id, total_amount):

    print("\n ================================")
    print("CELERY BACKGROUND TASK")
    print("================================")

    print(f"Order ID: {order_id}")
    print(f"User ID: {user_id}")
    print(f"Order Amount: ₹{total_amount}")

    print("Order notification processed.")
    print("================================\n")

    return {
        "status": "success",
        "order_id": order_id
    }


@celery_app.task
def send_payment_notification(order_id, user_id, total_amount):

    print("\n================================")
    print("CELERY PAYMENT TASK")
    print("================================")

    print(f"Order ID: {order_id}")
    print(f"User ID: {user_id}")
    print(f"Amount Paid: ₹{total_amount}")

    print("Payment notification processed.")
    print("================================\n")

    return {
        "status": "success",
        "order_id": order_id
    }