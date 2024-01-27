import pika  # type: ignore

from testcontainers_on_whales import Container


class RabbitmqContainer(Container):
    RABBITMQ_PORT = 5672

    def __init__(
        self,
        image: str = "docker.io/library/rabbitmq:alpine",
        username: str = "guest",
        password: str = "guest",  # noqa: S107
    ) -> None:
        self.username = username
        self.password = password
        super().__init__(
            image=image,
            env={
                "RABBITMQ_DEFAULT_USER": self.username,
                "RABBITMQ_DEFAULT_PASS": self.password,
            },
        )

    def get_connection_url(self) -> str:
        ip = self.get_container_ip()
        port = self.get_container_port(self.RABBITMQ_PORT)
        return f"amqp://{self.username}:{self.password}@{ip}:{port}"

    def readiness_probe(self) -> bool:
        try:
            parameters = pika.URLParameters(url=self.get_connection_url())
            connection = pika.BlockingConnection(parameters=parameters)
            connection.close()
        except pika.exceptions.AMQPConnectionError:
            pass
        except pika.exceptions.IncompatibleProtocolError:
            pass
        else:
            return True
        return False
