import requests

from testcontainers_on_whales import Container


class NginxContainer(Container):
    NGINX_PORT = 80

    def __init__(
        self,
        image: str = "docker.io/library/nginx:alpine",
    ) -> None:
        super().__init__(image=image)

    def get_connection_url(self) -> str:
        ip = self.get_host_ip()
        port = self.get_exposed_port(self.NGINX_PORT)
        return f"http://{ip}:{port}"

    def readiness_probe(self) -> bool:
        try:
            requests.get(self.get_connection_url())
            return True
        except requests.ConnectionError:
            pass
        return False
