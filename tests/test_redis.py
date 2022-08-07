import pytest
import redis

from testcontainers_on_whales.redis import RedisContainer


def test_redis_container():
    with RedisContainer() as container:
        container.wait_ready()
        client = container.get_client()

        client.set(name="test-name", value="test-value")
        value = client.get(name="test-name")

        assert value == b"test-value"


def test_redis_container_with_credentials():
    with RedisContainer(password="supersecure") as container:
        container.wait_ready()
        ip = container.get_container_ip()
        port = container.get_container_port(RedisContainer.REDIS_PORT)

        incorrect_url = f"redis://{ip}:{port}"
        incorrect_client = redis.Redis.from_url(url=incorrect_url)
        with pytest.raises(redis.AuthenticationError):
            incorrect_client.ping()

        correct_url = f"redis://:supersecure@{ip}:{port}"
        correct_client = redis.Redis.from_url(url=correct_url)
        correct_client.ping()
