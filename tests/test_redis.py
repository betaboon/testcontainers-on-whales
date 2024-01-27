from typing import cast

import pytest
import redis

from testcontainers_on_whales.redis import RedisContainer


def test_redis_container() -> None:
    with RedisContainer() as container:
        container.wait_ready(timeout=120)
        client = container.get_client()

        client.set(name="test-name", value="test-value")
        value = client.get(name="test-name")

        assert value == b"test-value"


def test_redis_container_with_credentials() -> None:
    with RedisContainer(password="supersecure") as container:
        container.wait_ready(timeout=120)
        ip = container.get_container_ip()
        port = container.get_container_port(RedisContainer.REDIS_PORT)

        incorrect_url = f"redis://{ip}:{port}"
        incorrect_client = redis.Redis.from_url(url=incorrect_url)
        # TODO remove cast when PR has hit py-redis release: https://github.com/redis/redis-py/pull/2963
        incorrect_client = cast(redis.Redis, incorrect_client)
        with pytest.raises(redis.AuthenticationError):
            incorrect_client.ping()

        correct_url = f"redis://:supersecure@{ip}:{port}"
        correct_client = redis.Redis.from_url(url=correct_url)
        # TODO remove cast when PR has hit py-redis release: https://github.com/redis/redis-py/pull/2963
        correct_client = cast(redis.Redis, correct_client)
        correct_client.ping()
