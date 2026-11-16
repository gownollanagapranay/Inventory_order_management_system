import pika
import json


RABBITMQ_HOST = "localhost"
QUEUE_NAME = "test_queue"


def send_message(message):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST
        )
    )

    channel = connection.channel()

    # Create the queue if it doesn't already exist
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    print("Message sent successfully:")
    print(message)

    connection.close()


if __name__ == "__main__":

    message = {
        "event": "test",
        "message": "Hello from Order Management System"
    }

    send_message(message)