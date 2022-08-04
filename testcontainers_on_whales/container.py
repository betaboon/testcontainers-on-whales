from __future__ import annotations

import logging
import re
import shutil
import time
from contextlib import AbstractContextManager
from typing import List, Optional

import python_on_whales

logger = logging.getLogger(__name__)


class ContainerRuntimeException(Exception):
    pass


class ContainerRuntimeNotFoundException(ContainerRuntimeException):
    pass


class Container(AbstractContextManager):
    def __init__(
        self,
        image: str,
        command: List[str] = [],
        client_call: Optional[List[str]] = None,
    ) -> None:
        self._image = image
        self._command = command
        self._client_call = client_call

        self._client = None
        self._container = None

    @property
    def client_call(self) -> List[str]:
        if self._client_call is None:
            if shutil.which("podman"):
                logger.debug("detected container-runtime: podman")
                self._client_call = ["podman"]
            elif shutil.which("docker"):
                logger.debug("detected container-runtime: docker")
                self._client_call = ["docker"]
            else:
                logger.error("failed to detect container-runtime")
                raise ContainerRuntimeNotFoundException()
        return self._client_call

    @property
    def client(self) -> python_on_whales.DockerClient:
        if self._client is None:
            self._client = python_on_whales.DockerClient(client_call=self.client_call)
        return self._client

    @property
    def container(self) -> python_on_whales.Container:
        if not self._container:
            self._container = self.client.create(
                image=self._image,
                command=self._command,
            )
        return self._container

    def __enter__(self) -> Container:
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self.stop()

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

    @property
    def is_ready(self) -> bool:
        return True

    @property
    def logs(self) -> str:
        return self.container.logs()

    def wait_exited(
        self,
        timeout: Optional[float] = None,
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
        timeout: Optional[float] = None,
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
        timeout: Optional[float] = None,
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
