from asyncio import (StreamReader, StreamWriter, TimeoutError, open_connection,
                     wait_for)
from enum import Enum
from ssl import CERT_NONE, create_default_context
from struct import pack, unpack
from typing import Optional


class RconError(Exception):
    pass


class TLSMode(Enum):
    DISABLED = 0
    ENABLED = 1
    INSECURE = 2


class RconPacketType(Enum):
    COMMAND = 2
    AUTH = 3


class Rcon:
    def __init__(
        self,
        host: str,
        password: str,
        port: int = 25575,
        tls_mode: TLSMode = TLSMode.DISABLED,
        timeout: int = 5,
    ):
        self.host: str = host
        self.password: str = password
        self.port: int = port
        self.tls_mode: TLSMode = tls_mode
        self.timeout: int = timeout
        self.reader: Optional[StreamReader] = None
        self.writer: Optional[StreamWriter] = None

    async def connect(self) -> None:
        if self.tls_mode != TLSMode.DISABLED:
            ctx = create_default_context()
            if self.tls_mode == TLSMode.INSECURE:
                ctx.check_hostname = False
                ctx.verify_mode = CERT_NONE
            self.reader, self.writer = await open_connection(
                self.host, self.port, ssl=ctx
            )
        else:
            self.reader, self.writer = await open_connection(self.host, self.port)
        await self._send(RconPacketType.AUTH, self.password)

    async def disconnect(self) -> None:
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.reader = None
            self.writer = None

    async def _read(self, length: int) -> bytes:
        try:
            return await wait_for(self.reader.readexactly(length), timeout=self.timeout)
        except TimeoutError:
            raise RconError("Connection timeout error")

    async def _send(self, packet_type: RconPacketType, data: str) -> str:
        if not self.writer:
            raise RconError("Not connected")

        payload = pack("<ii", 0, packet_type.value) + data.encode() + b"\x00\x00"
        self.writer.write(pack("<i", len(payload)) + payload)
        await self.writer.drain()

        response = ""
        while True:
            length = unpack("<i", await self._read(4))[0]
            payload = await self._read(length)
            packet_id, packet_type = unpack("<ii", payload[:8])
            response += payload[8:-2].decode()

            if packet_id == -1:
                raise RconError("Login failed")
            if self.reader.at_eof():
                return response

            try:
                next_data = await wait_for(self.reader.read(1), timeout=1)
                if not next_data:
                    return response
            except TimeoutError:
                return response

    async def command(self, command: str) -> str:
        return await self._send(RconPacketType.COMMAND, command)
