from sqlalchemy import Column, Integer, MetaData, Table, Text, select

from testcontainers_on_whales.postgres import PostgresContainer


def test_postgres_container():
    with PostgresContainer() as container:
        container.wait_ready(timeout=120)
        engine = container.get_sqlalchemy_engine()

        metadata = MetaData()
        messages = Table(
            "messages",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("message", Text),
        )
        messages.create(bind=engine)

        insert_message = messages.insert().values(message="Hello, Test!")
        engine.execute(insert_message)
        stmt = select([messages.c.message])
        (message,) = engine.execute(stmt).fetchone()

        assert message == "Hello, Test!"
