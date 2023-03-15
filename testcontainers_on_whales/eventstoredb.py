import requests
import urllib3
from eventstoredb import Client
from eventstoredb.options import ClientOptions

from testcontainers_on_whales import Container


class EventStoreDBContainer(Container):
    EVENTSTOREDB_HTTP_PORT = 2113
    EVENTSTOREDB_TCP_PORT = 1113

    def __init__(
        self,
        image: str = "docker.io/eventstore/eventstore:latest",
    ) -> None:
        super().__init__(
            image=image,
            env={
                "EVENTSTORE_CLUSTER_SIZE": "1",
                "EVENTSTORE_RUN_PROJECTIONS": "All",
                "EVENTSTORE_START_STANDARD_PROJECTIONS": "true",
                "EVENTSTORE_EXT_TCP_PORT": str(self.EVENTSTOREDB_TCP_PORT),
                "EVENTSTORE_HTTP_PORT": str(self.EVENTSTOREDB_HTTP_PORT),
                "EVENTSTORE_INSECURE": "true",
                "EVENTSTORE_ENABLE_EXTERNAL_TCP": "true",
                "EVENTSTORE_ENABLE_ATOM_PUB_OVER_HTTP": "true",
            },
        )

    def get_connection_url(self) -> str:
        ip = self.get_container_ip()
        port = self.get_container_port(self.EVENTSTOREDB_HTTP_PORT)
        return f"esdb://{ip}:{port}?tls=false"

    def get_client(self) -> Client:
        options = ClientOptions(
            host=self.get_container_ip(),
            port=self.get_container_port(self.EVENTSTOREDB_HTTP_PORT),
        )
        return Client(options)

    def readiness_probe(self) -> bool:
        ip = self.get_container_ip()
        port = self.get_container_port(self.EVENTSTOREDB_HTTP_PORT)
        url = f"http://{ip}:{port}/stats"
        try:
            r = requests.get(url)
            return r.status_code == 200
        except urllib3.exceptions.MaxRetryError:
            pass
        except requests.exceptions.ConnectionError:
            pass
        return False
