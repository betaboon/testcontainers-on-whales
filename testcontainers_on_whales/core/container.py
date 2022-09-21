from __future__ import annotations

import logging
import re
import shutil
import time
from contextlib import AbstractContextManager

import python_on_whales

from testcontainers_on_whales.core.exceptions import (
    ContainerRuntimeNotFoundError,
    NetworkModeUnknownError,
    PortBindingNotFoundError,
)

logger = logging.getLogger(__name__)


class Container(AbstractContextManager):
    def __init__(
        self,
        image: str,
        command: list[str] = [],
        env: dict[str, str] = {},
        client_call: list[str] | None = None,
    ) -> None:
        self._image = image
        self._command = command
        self._env = env
        self._client_call = client_call

        self._client = None
        self._container = None
        self._is_ready = False

    @property
    def client_call(self) -> list[str]:
        if self._client_call is None:
            if shutil.which("podman"):
                logger.debug("detected container-runtime: podman")
                self._client_call = ["podman"]
            elif shutil.which("docker"):
                logger.debug("detected container-runtime: docker")
                self._client_call = ["docker"]
            else:
                logger.error("failed to detect container-runtime")
                raise ContainerRuntimeNotFoundError()
        return self._client_call

    @property
    def client(self) -> python_on_whales.DockerClient:
        if self._client is None:
            self._client = python_on_whales.DockerClient(client_call=self.client_call)
        return self._client

    @property
    def container(self) -> python_on_whales.Container:
        if self._container is None:
            self._container = self.client.create(
                image=self._image,
                command=self._command,
                envs=self._env,
                publish_all=True,
            )
        return self._container

    def __enter__(self) -> Container:
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self.stop()

    def __del__(self) -> None:
        if self._container:
            self._container.remove()

    def start(self) -> None:
        if self.is_running:
            return
        self.container.start()

    def stop(self) -> None:
        if not self.is_running:
            return
        self.container.stop()

    @property
    def is_running(self) -> bool:
        return self.container.state.running

    def readiness_probe(self) -> bool:
        return True

    @property
    def is_ready(self) -> bool:
        if not self._is_ready:
            self._is_ready = self.readiness_probe()
        return self._is_ready

    def get_container_ip(self) -> str:
        network_mode = self.container.host_config.network_mode
        network_settings = self.container.network_settings

        if network_mode == "host":
            return "localhost"

        if network_mode in ("bridge", "default", "slirp4netns"):
            return network_settings.gateway or "localhost"

        raise NetworkModeUnknownError(network_mode=network_mode)

    def get_container_port(self, port: int | str) -> int:
        protocol = "tcp"

        if isinstance(port, str) and "/" in port:
            port, protocol = port.split("/")
        if isinstance(port, str):
            port = int(port)

        port_name = f"{port}/{protocol}"
        network_mode = self.container.host_config.network_mode
        network_settings = self.container.network_settings

        if network_mode == "host":
            return port

        if network_mode in ("bridge", "default", "slirp4netns"):
            if port_name not in network_settings.ports:
                raise PortBindingNotFoundError(port_name)

            exposed_port = network_settings.ports[port_name]
            host_port = exposed_port[0]["HostPort"]
            return int(host_port)

        raise NetworkModeUnknownError(network_mode=network_mode)

    @property
    def logs(self) -> str:
        return self.container.logs()

    def wait_exited(
        self,
        timeout: float | None = None,
        interval: float = 1,
    ) -> float:
        start = time.time()
        while True:
            duration = time.time() - start
            if not self.is_running:
                return duration
            if timeout and duration > timeout:
                raise TimeoutError(f"container did not exit within {timeout:.2f}")
            time.sleep(interval)

    def wait_ready(
        self,
        timeout: float | None = None,
        interval: float = 1,
    ) -> float:
        start = time.time()
        while True:
            duration = time.time() - start
            if self.is_ready:
                return duration
            if timeout and duration > timeout:
                raise TimeoutError(
                    f"container did not become ready within {timeout:.2f}"
                )
            time.sleep(interval)

    def wait_logs_match(
        self,
        pattern: str,
        timeout: float | None = None,
        interval: float = 1,
    ) -> float:
        prog = re.compile(pattern)
        start = time.time()
        while True:
            duration = time.time() - start
            if prog.search(self.logs):
                return duration
            if not self.is_running:
                return duration
            if timeout and duration > timeout:
                raise TimeoutError(
                    f"container did not emit matching logs within {timeout:.2f}"
                )
            time.sleep(interval)
