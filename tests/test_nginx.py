import requests

from testcontainers_on_whales.nginx import NginxContainer


def test_nginx_container():
    with NginxContainer() as container:
        container.wait_ready(timeout=120)
        url = container.get_connection_url()
        response = requests.get(url)
        assert response.status_code == 200
        assert "Welcome to nginx!" in response.text
