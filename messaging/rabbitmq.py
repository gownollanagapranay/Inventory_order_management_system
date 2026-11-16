import pika


RABBITMQ_HOST = "localhost"


def get_connection():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST
        )
    )

    return connection


def publish_message(
    queue_name: str,
    message: dict
):
    import json

    connection = get_connection()

    channel = connection.channel()

    channel.queue_declare(
        queue=queue_name,
        durable=True
    )

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    connection.close()