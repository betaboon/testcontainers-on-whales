from __future__ import annotations

import redis

from testcontainers_on_whales import Container


class RedisContainer(Container):
    REDIS_PORT = 6379

    def __init__(
        self,
        image: str = "redis:alpine",
        password: str | None = None,
    ) -> None:
        self.password = password
        command = []
        if self.password:
            command = ["--requirepass", self.password]
        super().__init__(image=image, command=command)

    def get_connection_url(self) -> str:
        ip = self.get_host_ip()
        port = self.get_exposed_port(self.REDIS_PORT)
        auth = ""
        if self.password:
            auth = f":{self.password}@"
        return f"redis://{auth}{ip}:{port}"

    def get_client(self) -> redis.Redis:
        url = self.get_connection_url()
        client = redis.Redis.from_url(url)
        return client

    def readiness_probe(self) -> bool:
        client = self.get_client()
        return client.ping()
