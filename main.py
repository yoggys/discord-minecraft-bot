from asyncio import Future, ensure_future, get_event_loop, sleep
from logging import INFO, basicConfig, error
from typing import Any, Optional

from discord import (ApplicationContext, Bot, Intents, Permissions, User,
                     default_permissions, guild_only, option)
from tortoise import Tortoise, connections
from tortoise.queryset import Q

from utils.checks import check_admin, check_allowed
from utils.config import Config
from utils.controller import Controller
from utils.models import Connection

basicConfig(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

config = Config()

intents = Intents.default()
if config.expires:
    intents.members = True

client = Bot(intents=intents)
controller = Controller(client, config)

admin_group = client.create_group(
    "admin",
    "Admin commands for the Minecraft server.",
    default_member_permissions=Permissions(administrator=True),
    guild_only=True,
)


@client.slash_command(
    name="minecraft",
    description="Connect your Discord account to the Minecraft server.",
)
@option(
    name="username",
    description="Provide your Minecraft username.",
    max_length=16,
    type=str,
    required=False,
)
async def minecraft(ctx: ApplicationContext, username: Optional[str]) -> Any:
    if await check_allowed(ctx, config):
        return

    await ctx.defer(ephemeral=True)
    if username is None:
        return await controller.whitelist_remove(
            ctx, ctx.author, "Your Discord account connection has been removed."
        )
    await controller.whitelist_add(ctx, username)


@admin_group.command(name="check", description="Check the user data.")
@option(name="user", description="Provide Discord user.", type=User, required=False)
@option(
    name="username",
    description="Provide Minecraft username.",
    max_length=16,
    type=str,
    required=False,
)
async def check(
    ctx: ApplicationContext, user: Optional[User], username: Optional[str]
) -> Any:
    if await check_admin(ctx, user, username):
        return

    await ctx.defer(ephemeral=True)
    await controller.user_check(ctx, user or username)


@admin_group.command(name="ban", description="Ban user from the server.")
@option(name="user", description="Provide Discord user.", type=User, required=False)
@option(
    name="username",
    description="Provide Minecraft username.",
    max_length=16,
    type=str,
    required=False,
)
@option(
    name="reason",
    description="Reason for the ban.",
    max_length=64,
    type=str,
    required=False,
)
async def ban(
    ctx: ApplicationContext,
    user: Optional[User],
    username: Optional[str],
    reason: Optional[str],
) -> Any:
    if await check_admin(ctx, user, username):
        return

    await ctx.defer(ephemeral=True)
    await controller.user_ban(ctx, user or username, reason)


@admin_group.command(name="unban", description="Ban user from the server.")
@option(name="user", description="Provide Discord user.", type=User, required=False)
@option(
    name="username",
    description="Provide Minecraft username.",
    max_length=16,
    type=str,
    required=False,
)
async def unban(
    ctx: ApplicationContext,
    user: Optional[User],
    username: Optional[str],
) -> Any:
    if await check_admin(ctx, user, username):
        return

    await ctx.defer(ephemeral=True)
    await controller.user_unban(ctx, user or username)


@admin_group.command(name="remove", description="Remove user from the whitelist.")
@option(name="user", description="Provide Discord user.", type=User, required=False)
@option(
    name="username",
    description="Provide Minecraft username.",
    max_length=16,
    type=str,
    required=False,
)
@option(
    name="reason",
    description="Reason for the removal.",
    max_length=64,
    type=str,
    required=False,
)
@default_permissions(administrator=True)
@guild_only()
async def remove(
    ctx: ApplicationContext,
    user: Optional[User],
    username: Optional[str],
    reason: Optional[str],
) -> Any:
    if await check_admin(ctx, user, username):
        return

    await ctx.defer(ephemeral=True)
    await controller.whitelist_remove(ctx, user or username, reason)


@admin_group.command(
    name="restart", description="Restart connection to the Minecraft server."
)
async def restart(
    ctx: ApplicationContext,
) -> Any:
    await ctx.defer(ephemeral=True)
    await controller.connect()
    await ctx.respond("🔄 Connection restarted!")


if config.admin_commands:

    @client.slash_command(name="root", description="Execute any Minecraft command.")
    @option(
        name="command",
        description="Provide the command you want to execute.",
        max_length=256,
        type=str,
    )
    @default_permissions(administrator=True)
    @guild_only()
    async def root(ctx: ApplicationContext, command: str) -> Any:
        await ctx.defer(ephemeral=True)
        await controller.command(ctx, command)


expire_future: Optional[Future] = None
if config.expires and config.guild is not None:

    async def expire_check() -> None:
        while True:
            if guild := client.get_guild(config.guild):
                for connection in await Connection.filter(
                    ~Q(username=None) & Q(is_banned=False)
                ):
                    member = guild.get_member(connection.user_id)
                    if not member or (
                        config.allowed_roles
                        and not any(
                            [role.id in config.allowed_roles for role in member.roles]
                        )
                    ):
                        try:
                            await controller.whitelist_remove(
                                None,
                                connection.username,
                                "Membership has expired. Access has been revoked.",
                            )
                        except Exception as e:
                            error(f"Error in expire check: {e}")
            await sleep(config.check_interval)

    @client.listen("on_ready", once=True)
    async def on_ready() -> None:
        global expire_future
        expire_future = ensure_future(expire_check())


async def start() -> None:
    await Tortoise.init(db_url="sqlite://main.db", modules={"models": ["utils.models"]})
    await Tortoise.generate_schemas()
    await controller.connect()
    await client.start(config.bot_token)


loop = get_event_loop()
try:
    loop.run_until_complete(start())
except (KeyboardInterrupt, Exception) as e:
    if isinstance(e, Exception):
        error(f"Error in main loop: {e}")
    if expire_future:
        expire_future.cancel()
    if not client.is_closed():
        loop.run_until_complete(client.close())
    loop.run_until_complete(controller.close())
    loop.run_until_complete(connections.close_all())
finally:
    if not loop.is_closed():
        loop.close()
