import time
from typing import Any

import pytest

from testcontainers_on_whales import Container


def test_container_is_running() -> None:
    container = Container(image="alpine", command=["watch", "uptime"])

    assert container.is_running is False

    with container:
        assert container.is_running is True

    assert container.is_running is False


def test_container_wait_exited() -> None:
    with Container(image="alpine", command=["sleep", "1"]) as container:
        assert container.is_running is True
        container.wait_exited()
        assert container.is_running is False


def test_container_wait_exited_timeout_raises() -> None:
    with Container(image="alpine", command=["sleep", "1"]) as container:
        assert container.is_running is True
        with pytest.raises(TimeoutError, match=r".*did not exit.*"):
            container.wait_exited(timeout=0.1, interval=0.1)


def test_container_wait_ready() -> None:
    class CustomContainer(Container):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self._readiness_probes = 0

        def readiness_probe(self) -> bool:
            self._readiness_probes += 1
            if self._readiness_probes == 2:
                return True
            time.sleep(0.1)
            return False

    with CustomContainer(image="alpine") as container:
        time_to_ready = container.wait_ready(timeout=10, interval=0.1)
        assert container.is_ready is True
        assert container._readiness_probes == 2
        assert round(time_to_ready, 1) == 0.2


def test_container_wait_ready_timeout_raises() -> None:
    class CustomContainer(Container):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self._readiness_probes = 0

        def readiness_probe(self) -> bool:
            self._readiness_probes += 1
            if self._readiness_probes == 5:
                return True
            time.sleep(0.1)
            return False

    with CustomContainer(image="alpine") as container:
        with pytest.raises(TimeoutError, match=r".*did not become ready.*"):
            container.wait_ready(timeout=0.1, interval=0.1)


def test_container_logs_while_running() -> None:
    with Container(image="hello-world") as container:
        assert "Hello from Docker!" in container.logs


def test_container_logs_after_exited() -> None:
    container = Container(image="hello-world")
    with container:
        pass
    assert "Hello from Docker!" in container.logs


def test_container_wait_logs_match() -> None:
    with Container(image="hello-world") as container:
        container.wait_logs_match("Hello from Docker!")


def test_container_wait_logs_match_timeout_raises() -> None:
    with Container(image="alpine", command=["sleep", "1"]) as container:
        with pytest.raises(TimeoutError, match=r".*did not emit matching logs.*"):
            container.wait_logs_match("Hello from Docker!", timeout=0.1, interval=0.1)
