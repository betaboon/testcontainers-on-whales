import pytest
from eventstoredb.events import JsonEvent

from testcontainers_on_whales.eventstoredb import EventStoreDBContainer


@pytest.mark.asyncio
async def test_eventstoredb_container():
    with EventStoreDBContainer() as container:
        container.wait_ready(timeout=120)
        client = container.get_client()
        stream_name = "example-stream"
        event = JsonEvent(type="ExampleEvent")
        result = await client.append_to_stream(
            stream_name=stream_name,
            events=event,
        )

        assert result.success is True
