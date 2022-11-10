from typing import Generator

import pytest

from testcontainers_on_whales.eventstoredb import EventStoreDBContainer


@pytest.fixture
def eventstoredb_container() -> Generator[EventStoreDBContainer, None, None]:
    with EventStoreDBContainer() as container:
        container.wait_ready(timeout=120)
        yield container


@pytest.mark.asyncio
async def test_eventstoredb_container(
    eventstoredb_container: EventStoreDBContainer,
) -> None:
    client = eventstoredb_container.get_client()
    async with client.connect() as conn:
        for i in range(10):
            append_result = await conn.streams.append(
                stream="test-stream",
                event_type="example-event",
                data={"test": i},
            )
    assert append_result.current_revision == 9
