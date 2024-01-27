import pika  # type: ignore
import pytest

from testcontainers_on_whales.rabbitmq import RabbitmqContainer


def test_rabbitmq_container() -> None:
    with RabbitmqContainer() as container:
        container.wait_ready(timeout=120)

        url = container.get_connection_url()
        parameters = pika.URLParameters(url=url)
        connection = pika.BlockingConnection(parameters=parameters)
        channel = connection.channel()
        channel.queue_declare(queue="test")

        channel.basic_publish(exchange="", routing_key="test", body=b"Test message")
        _, _, body = channel.basic_get(queue="test")

        assert body == b"Test message"


def test_rabbitmq_container_custom_credentials() -> None:
    with RabbitmqContainer(username="custom", password="supersecure") as container:
        container.wait_ready(timeout=120)
        ip = container.get_container_ip()
        port = container.get_container_port(RabbitmqContainer.RABBITMQ_PORT)

        incorrect_url = f"amqp://guest:guest@{ip}:{port}"
        incorrect_parameters = pika.URLParameters(url=incorrect_url)

        with pytest.raises(pika.exceptions.ProbableAuthenticationError):
            pika.BlockingConnection(parameters=incorrect_parameters)

        correct_url = f"amqp://custom:supersecure@{ip}:{port}"
        correct_parameters = pika.URLParameters(url=correct_url)
        pika.BlockingConnection(parameters=correct_parameters)
