import requests

from testcontainers_on_whales import Container


class NginxContainer(Container):
    NGINX_PORT = 8080

    def __init__(
        self,
        image: str = "docker.io/nginxinc/nginx-unprivileged:alpine",
    ) -> None:
        super().__init__(image=image)

    def get_connection_url(self) -> str:
        ip = self.get_container_ip()
        port = self.get_container_port(self.NGINX_PORT)
        return f"http://{ip}:{port}"

    def readiness_probe(self) -> bool:
        try:
            requests.get(self.get_connection_url(), timeout=10)
        except requests.ConnectionError:
            pass
        else:
            return True
        return False
