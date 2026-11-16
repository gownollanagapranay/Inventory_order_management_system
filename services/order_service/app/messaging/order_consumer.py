import json
import pika

RABBITMQ_HOST = "localhost"

EXCHANGE_NAME = "order_events"
QUEUE_NAME = "order_queue"
ROUTING_KEY = "order.created"


def callback(ch, method, properties, body):

    try:
        message = json.loads(body)

        print("\n================================")
        print("ORDER CREATED EVENT RECEIVED")
        print("================================")

        print(f"Event: {message['event']}")
        print(f"Order ID: {message['order_id']}")
        print(f"User ID: {message['user_id']}")
        print(f"Total Amount: {message['total_amount']}")
        print(f"Order Status: {message['status']}")
        print(f"Payment Status: {message['payment_status']}")

        print("================================\n")

        ch.basic_ack(
            delivery_tag=method.delivery_tag
        )

    except Exception as e:

        print(f"Error processing message: {e}")

        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )


def start_consumer():

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST
        )
    )

    channel = connection.channel()

    # Create exchange
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="direct",
        durable=True
    )

    # Create this consumer's own queue
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    # Connect queue to exchange
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY
    )

    channel.basic_qos(
        prefetch_count=1
    )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    print("Order Consumer started...")
    print("Waiting for order.created events...")

    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()