from typing import Any

import boto3  # type: ignore
import requests
import urllib3
from botocore.client import Config  # type: ignore

from testcontainers_on_whales import Container


class MinioContainer(Container):
    MINIO_PORT = 9000
    MINIO_CONSOLE_PORT = 9001

    def __init__(
        self,
        image: str = "docker.io/minio/minio:latest",
        username: str = "minioadmin",
        password: str = "minioadmin",  # noqa: S107
    ):
        self.username = username
        self.__password = password
        super().__init__(
            image=image,
            command=[
                "server",
                "/data",
                "--console-address",
                f":{MinioContainer.MINIO_CONSOLE_PORT}",
            ],
            env={
                "MINIO_ROOT_USER": self.username,
                "MINIO_ROOT_PASSWORD": self.__password,
            },
        )

    def get_connection_url(self) -> str:
        ip = self.get_container_ip()
        port = self.get_container_port(self.MINIO_PORT)
        return f"http://{ip}:{port}"

    def get_boto_resource(self) -> Any:
        return boto3.resource(
            "s3",
            endpoint_url=self.get_connection_url(),
            aws_access_key_id=self.username,
            aws_secret_access_key=self.__password,
            config=Config(signature_version="s3v4"),
        )

    def get_bucket(self, name: str = "test") -> Any:
        """
        Get bucket by name. Create if it does not exist.
        :param name:
        :return:
        """
        s3 = self.get_boto_resource()
        bucket = s3.Bucket(name)
        if None is bucket.creation_date:
            bucket.create()
        return bucket

    def readiness_probe(self) -> bool:
        url = self.get_connection_url()
        try:
            r = requests.get(url, timeout=10)
        except urllib3.exceptions.MaxRetryError:
            pass
        except requests.exceptions.ConnectionError:
            pass
        else:
            return r.status_code == 403
        return False
