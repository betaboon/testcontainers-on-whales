import boto3 as boto3
import requests as requests
import urllib3 as urllib3
from botocore.client import Config
from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig

from testcontainers_on_whales import Container


class MinioContainer(Container):
    MINIO_PORT = 9000
    MINIO_CONSOLE_PORT = 9001
    AMQP_IDENTIFIER = "TEST"

    def __init__(
            self,
            image: str = "docker.io/minio/minio:latest",
            username: str = "minioadmin",
            password: str = "minioadmin",
            extra_env: dict = None,
    ):
        self.username = username
        self.__password = password
        if not extra_env:
            extra_env = dict()
        super().__init__(
            image=image,
            command=[
                "server",
                "/tmp/storage",
                "--console-address",
                f":{MinioContainer.MINIO_CONSOLE_PORT}",
            ],
            env={
                    "MINIO_ROOT_USER": self.username,
                    "MINIO_ROOT_PASSWORD": self.__password,
                } | extra_env,
        )

    @staticmethod
    def get_amqp_extra_env(amqp_url: str, exchange: str):
        # "TEST" is the AMQP endpoint identifier
        identifier = ""
        if MinioContainer.AMQP_IDENTIFIER:
            identifier = f"_{MinioContainer.AMQP_IDENTIFIER}"
        return {
            f"MINIO_NOTIFY_AMQP_ENABLE{identifier}": "on",
            f"MINIO_NOTIFY_AMQP_URL{identifier}": amqp_url,  # amqp://guest:guest@rabbitmq:5672
            f"MINIO_NOTIFY_AMQP_EXCHANGE{identifier}": exchange,
            f"MINIO_NOTIFY_AMQP_EXCHANGE_TYPE{identifier}": "fanout",
            f"MINIO_NOTIFY_AMQP_DURABLE{identifier}": "on",
            f"MINIO_SKIP_CLIENT": "yes",  # bitnami minio client broke some setups in the past
        }

    def get_connection_url(self) -> str:
        ip = self.get_container_ip()
        port = self.get_container_port(self.MINIO_PORT)
        return f"http://{ip}:{port}"

    def get_boto_resource(self):
        s3 = boto3.resource(
            "s3",
            endpoint_url=self.get_connection_url(),
            aws_access_key_id=self.username,
            aws_secret_access_key=self.__password,
            config=Config(signature_version="s3v4"),
        )
        return s3

    def get_bucket(self, name: str = "test"):
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
            r = requests.get(url)
            return r.status_code == 403
        except urllib3.exceptions.MaxRetryError:
            pass
        except requests.exceptions.ConnectionError:
            pass
        return False

    def _get_arn(self):
        idf = "_"
        if self.AMQP_IDENTIFIER:
            idf = self.AMQP_IDENTIFIER

        return f"arn:minio:sqs::{idf}:amqp"

    def get_minio_client(self):
        ip = self.get_container_ip()
        port = self.get_container_port(self.MINIO_PORT)
        minio_endpoint = f"{ip}:{port}"
        client = Minio(
            minio_endpoint,
            secure=False,
            access_key=self.username,
            secret_key=self.__password
        )
        return client

    def configure_notifications(self, bucket_name: str, event_list: list[str]):
        """
        Configure this minio server to release events via amqp for specific S3 events
        :param bucket_name:
        :param event_list: e.g. ["s3:ObjectCreated:*"]
        :return:
        """
        arn = self._get_arn()
        client = self.get_minio_client()

        notification_config = NotificationConfig(
            queue_config_list=[
                QueueConfig(
                    arn,
                    event_list,
                    config_id="1",
                    # prefix_filter_rule=PrefixFilterRule("abc"),
                    # suffix_filter_rule=SuffixFilterRule(".pdf"),
                ),
            ],
        )
        client.set_bucket_notification(bucket_name, notification_config)
