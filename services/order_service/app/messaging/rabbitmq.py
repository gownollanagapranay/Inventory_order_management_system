
import json
import os
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

EXCHANGE_NAME = "order_events"
ROUTING_KEY = "order.created"


def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD
    )

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials,
        connection_attempts=10,
        retry_delay=5,
        heartbeat=600
    )

    return pika.BlockingConnection(parameters)


def publish_order_created(order):
    connection = get_rabbitmq_connection()
    try:
        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="direct",
            durable=True
        )

        message = {
            "event": "order.created",
            "order_id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_status": order.payment_status
        }

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        print(
            f"Order created event published: "
            f"order_id={order.id}"
        )
    finally:
        connection.close()


def publish_order_paid(order):
    connection = get_rabbitmq_connection()
    try:
        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="direct",
            durable=True
        )

        message = {
            "event": "order.paid",
            "order_id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "payment_status": order.payment_status
        }

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key="order.paid",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        print(
            f"Order paid event published: order_id={order.id}"
        )
    finally:
        connection.close()
