import sqlalchemy

from testcontainers_on_whales import Container


class PostgresContainer(Container):
    POSTGRES_PORT = 5432

    def __init__(
        self,
        image: str = "docker.io/library/postgres:alpine",
        username: str = "test",
        password: str = "test",  # noqa: S107
        database_name: str = "test",
    ) -> None:
        self.username = username
        self.password = password
        self.database_name = database_name
        super().__init__(
            image=image,
            env={
                "POSTGRES_USER": self.username,
                "POSTGRES_PASSWORD": self.password,
                "POSTGRES_DB": self.database_name,
            },
        )

    def get_connection_url(self, driver: str = "psycopg2") -> str:
        ip = self.get_container_ip()
        port = self.get_container_port(self.POSTGRES_PORT)
        auth = f"{self.username}:{self.password}"
        return f"postgresql+{driver}://{auth}@{ip}:{port}/{self.database_name}"

    def get_sqlalchemy_engine(self) -> sqlalchemy.engine.Engine:
        url = self.get_connection_url()
        return sqlalchemy.create_engine(url)

    def readiness_probe(self) -> bool:
        engine = self.get_sqlalchemy_engine()
        try:
            engine.connect()
        except sqlalchemy.exc.OperationalError:
            pass
        else:
            return True
        return False
