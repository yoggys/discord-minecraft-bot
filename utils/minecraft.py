from typing import Any, Optional

from utils.config import Config
from utils.rcon import Rcon, TLSMode


class MinecraftController:
    def __init__(self, config: Config, tls_mode: TLSMode = TLSMode.DISABLED) -> None:
        self.config = config
        self.tls_mode = tls_mode

        self._server: Optional[Rcon] = None

    async def connect(self) -> None:
        if self._server:
            await self._server.disconnect()
        self._server = Rcon(
            self.config.host, self.config.password, self.config.port, self.tls_mode
        )
        await self._server.connect()

    async def close(self) -> None:
        if self._server:
            await self._server.disconnect()

    async def command(self, command: str) -> Any:
        return await self._server.command(command)

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
