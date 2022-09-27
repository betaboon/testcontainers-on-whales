import threading
import time

import pika as pika

from testcontainers_on_whales.minio import MinioContainer
from testcontainers_on_whales.rabbitmq import RabbitmqContainer


def thread_func(channel, exchange_name, message):
    # channel = connection.channel()
    channel.exchange_declare(exchange_name, exchange_type='fanout', durable=True)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    message = "nix"

    def callback(ch, method, properties, body):
        print(" [x] Channel  %r" % ch)
        print(" [x] Method   %r" % method)
        print(" [x] Proper   %r" % properties)
        print(" [x] Received %r" % body)
        message = body
        ch.stop_consuming()

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


def test_minio_with_rabbitmq():
    print("blabla----------------------")
    with RabbitmqContainer() as amqp:
        time.sleep(3)
        amqp.wait_ready(20)
        amqp_url = amqp.get_connection_url()
        exchange_name = "exchange"
        extra_env = MinioContainer.get_amqp_extra_env(amqp_url, exchange_name)
        with MinioContainer(extra_env=extra_env) as minio:
            minio.wait_ready(20)
            bucket_name = 'test'
            bucket = minio.get_bucket(bucket_name)
            minio.configure_notifications(bucket_name, event_list=["s3:ObjectCreated:*"])

            parameters = pika.URLParameters(url=amqp.get_connection_url())
            connection = pika.BlockingConnection(parameters=parameters)

            channel = connection.channel()
            message = "empty"
            consumer = threading.Thread(target=thread_func, args=(channel, exchange_name, message))
            consumer.start()

            print("started")
            time.sleep(5)
            print("sleep end")
            consumer.join(60)
            channel.stop_consuming()
            print("stop consume")
            print("JOIN ENDED")
