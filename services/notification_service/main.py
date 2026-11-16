
import json
import os
import pika

from services.notification_service.tasks import (
    send_order_notification,
    send_payment_notification
)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

EXCHANGE_NAME = "order_events"

QUEUE_NAME = "notification_queue"
ROUTING_KEY = "order.created"

PAYMENT_QUEUE = "payment_notification_queue"
PAYMENT_ROUTING_KEY = "order.paid"


def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        event_type = message["event"]

        print(f"Received event: {event_type}")

        if event_type == "order.created":
            result = send_order_notification.delay(
                order_id=message["order_id"],
                user_id=message["user_id"],
                total_amount=message["total_amount"]
            )

            print("Order notification task submitted to Celery.")
            print("Celery Task ID:", result.id)

        elif event_type == "order.paid":
            result = send_payment_notification.delay(
                order_id=message["order_id"],
                user_id=message["user_id"],
                total_amount=message["total_amount"]
            )

            print("Payment notification task submitted to Celery.")
            print("Celery Task ID:", result.id)

        else:
            print(f"Unknown event: {event_type}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error processing message: {e}")

        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )


def start_consumer():
    print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}...")

    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=5672,
            credentials=credentials,
            connection_attempts=10,
            retry_delay=5,
            heartbeat=600
        )
    )

    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="direct",
        durable=True
    )

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY
    )

    channel.queue_declare(
        queue=PAYMENT_QUEUE,
        durable=True
    )

    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=PAYMENT_QUEUE,
        routing_key=PAYMENT_ROUTING_KEY
    )

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    channel.basic_consume(
        queue=PAYMENT_QUEUE,
        on_message_callback=callback
    )

    print("Notification Service started...")
    print("Listening for order.created and order.paid events...")
    print("Celery will process notifications in the background.")

    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
