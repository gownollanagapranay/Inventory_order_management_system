import pika
import json


RABBITMQ_HOST = "localhost"
QUEUE_NAME = "test_queue"


def callback(ch, method, properties, body):

    message = json.loads(body)

    print("\nMessage received:")
    print(message)

    # Tell RabbitMQ that the message was successfully processed
    ch.basic_ack(
        delivery_tag=method.delivery_tag
    )


connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST
    )
)

channel = connection.channel()

channel.queue_declare(
    queue=QUEUE_NAME,
    durable=True
)

channel.basic_qos(
    prefetch_count=1
)

channel.basic_consume(
    queue=QUEUE_NAME,
    on_message_callback=callback
)

print("Consumer started...")
print("Waiting for messages...")

channel.start_consuming()