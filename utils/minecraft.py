from asyncio import CancelledError, Future, Queue, ensure_future, sleep
from logging import debug, error
from typing import Any, Optional

from utils.config import Config
from utils.rcon import Rcon, TLSMode


class MinecraftController:
    def __init__(self, config: Config, tls_mode: TLSMode = TLSMode.DISABLED) -> None:
        self.config = config
        self.tls_mode = tls_mode

        self._server: Optional[Rcon] = None
        self._future: Optional[Future] = None
        self._queue = Queue()

    async def connect(self) -> None:
        if self._server:
            await self._server.disconnect()
        self._server = Rcon(
            self.config.host, self.config.password, self.config.port, self.tls_mode
        )
        await self._server.connect()
        if self._future:
            self._future.cancel()
        self._future = ensure_future(self.start())

    async def start(self) -> None:
        while True:
            try:
                command = await self._queue.get()
                result = await self.execute(command)
                debug(f"MinecraftController nowait ({command}): {result}")
            except Exception as e:
                error(f"Error in command execution: {e}")
                await self.connect()
            finally:
                await sleep(0.05)

    async def close(self) -> None:
        await self._queue.join()
        if self._server:
            await self._server.disconnect()
        if self._future:
            self._future.cancel()
            try:
                await self._future
            except CancelledError:
                pass

    @property
    def is_closed(self) -> bool:
        return self._future.cancelled() if self._future else True

    async def execute(self, command: str) -> Any:
        return await self._server.command(command)

    async def command(self, command: str, wait: bool = False) -> Any:
        if wait:
            result = await self.execute(command)
            debug(f"MinecraftController wait ({command}): {result}")
            return result
        await self._queue.put(command)

    async def whitelist_add(self, username: str) -> None:
        await self.command(f"whitelist add {username}")

    async def whitelist_remove(
        self, username: str, reason: Optional[str] = None
    ) -> None:
        await self.command(f"whitelist remove {username}")
        await self.command(
            f"kick {username} {reason if reason else 'No reason provided.'}"
        )

    async def ban_add(self, username: str, reason: Optional[str] = None) -> None:
        await self.command(f"whitelist remove {username}")
        await self.command(
            f"ban {username} {reason if reason else 'No reason provided'}"
        )

    async def ban_remove(self, username: str) -> None:
        await self.command(f"pardon {username}")
