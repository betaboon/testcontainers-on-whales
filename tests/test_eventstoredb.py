from typing import Generator

import pytest
from eventstoredb.events import JsonEvent

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
    append_result = await client.append_to_stream(
        stream_name="test-stream",
        events=JsonEvent(type="test-event"),
    )
    assert append_result.success == True
