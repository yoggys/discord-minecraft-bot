from os import getenv
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    def __init__(self) -> None:
        self.bot_token: str = getenv("BOT_TOKEN")
        if self.bot_token is None:
            raise ValueError("BOT_TOKEN environment variable not set")

        self.host: str = getenv("HOST")
        self.password: str = getenv("PASSWORD")

        if self.password is None or self.host is None:
            raise ValueError("HOST or PASSWORT environment variable not set")

        self.port: int = 25575
        if port := getenv("PORT"):
            if not port.isdigit():
                raise ValueError("Invalid PORT")
            self.port = int(port)

        self.admin_commands: bool = False
        if admin_commands := getenv("ADMIN_COMMANDS"):
            if admin_commands.lower() == "true":
                self.admin_commands = True

        self.expires: bool = False
        if expires := getenv("EXPIRES"):
            if expires.lower() == "true":
                self.expires = True

        self.check_interval: int = 60
        self.guild: Optional[int] = None

        if expires:
            if check_interval := getenv("CHECK_INTERVAL"):
                if not check_interval.isdigit():
                    raise ValueError("Invalid CHECK_INTERVAL")
                self.check_interval = int(check_interval)

            if guild := getenv("GUILD_ID"):
                if not guild.isdigit():
                    raise ValueError("Invalid check GUILD_ID")
                self.guild = int(guild)

            if self.guild is None:
                raise ValueError("GUILD_ID environment variable not set")

        self.allowed_roles: Optional[list[str]] = None
        if allowed_roles := getenv("ALLOWED_ROLES"):
            allowed_roles = allowed_roles.split(",")
            if len(allowed_roles) > 0:
                if not all([role.isdigit() for role in allowed_roles]):
                    raise ValueError("Invalid ALLOWED_ROLES")
                self.allowed_roles = list(map(lambda r: int(r.strip()), allowed_roles))

        self.logs_channel: Optional[int] = None
        if logs_channel := getenv("LOGS_CHANNEL"):
            if not logs_channel.isdigit():
                raise ValueError("Invalid check LOGS_CHANNEL")
            self.logs_channel = int(logs_channel)
