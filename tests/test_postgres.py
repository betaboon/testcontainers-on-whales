from sqlalchemy import Column, Integer, MetaData, Table, Text, insert, select

from testcontainers_on_whales.postgres import PostgresContainer


def test_postgres_container() -> None:
    with PostgresContainer() as container:
        container.wait_ready(timeout=120)
        engine = container.get_sqlalchemy_engine()

        metadata = MetaData()
        messages_table = Table(
            "messages",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("message", Text),
        )
        messages_table.create(bind=engine)

        with engine.connect() as connection:
            insert_message = insert(messages_table).values(message="Hello, Test!")
            connection.execute(insert_message)
            select_stmt = select(messages_table)
            message_row = connection.execute(select_stmt).fetchone()
            assert message_row is not None
            _, message = message_row
            assert message == "Hello, Test!"
