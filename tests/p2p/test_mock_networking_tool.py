import asyncio
import pytest

from p2p.tools.local_network import Address


@pytest.mark.asyncio
async def test_router_connected_readers(router):
    address = Address('tcp', '192.168.1.1', 1234)
    reader, writer = router.get_connected_readers(address)

    writer.write(b'test-data')

    data = await reader.read(9)

    assert data == b'test-data'


@pytest.mark.asyncio
async def test_server_connection_callback(router):
    n1 = router.get_network('192.168.1.1')
    n2 = router.get_network('192.168.1.2')

    was_run = asyncio.Event()

    async def cb(reader, writer):
        nonlocal was_run
        was_run.set()

    await asyncio.wait_for(n2.start_server(cb, n2.host, 1234), timeout=0.01)

    await asyncio.wait_for(n1.open_connection(n2.host, 1234), timeout=0.01)

    await asyncio.wait_for(was_run.wait(), timeout=0.1)

    assert was_run.is_set()


@pytest.mark.asyncio
async def test_arst_server_client_communication(router):
    n1 = router.get_network('192.168.1.1')
    n2 = router.get_network('192.168.1.2')

    was_run = asyncio.Event()

    server_reader, server_writer = None, None

    async def cb(reader, writer):
        nonlocal was_run
        nonlocal server_reader
        nonlocal server_writer
        server_reader = reader
        server_writer = writer
        await asyncio.sleep(0)
        was_run.set()

    await n2.start_server(cb, n2.host, 1234)

    client_reader, client_writer = await n1.open_connection(n2.host, 1234)

    await asyncio.wait_for(was_run.wait(), timeout=0.1)

    assert server_reader is not None
    assert server_writer is not None

    client_writer.write(b'arst')
    server_data = await asyncio.wait_for(server_reader.read(4), timeout=0.01)

    assert server_data == b'arst'

    server_writer.write(b'tsra')
    client_data = await asyncio.wait_for(client_reader.read(4), timeout=0.01)

    assert client_data == b'tsra'
