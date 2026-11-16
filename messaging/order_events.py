from .rabbitmq import publish_message


ORDER_CREATED_QUEUE = "order_created"


def publish_order_created(order):

    message = {
        "event": "order.created",
        "order_id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "payment_status": order.payment_status
    }

    publish_message(
        queue_name=ORDER_CREATED_QUEUE,
        message=message
    )

    print(
        f"Order created event published "
        f"for order {order.id}"
    )