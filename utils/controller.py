from logging import error
from typing import Any, Optional, Union

from discord import ApplicationContext, Bot, Color, Embed, HTTPException, User
from tortoise.queryset import Q

from utils.config import Config
from utils.minecraft import MinecraftController
from utils.models import Connection
from utils.rcon import TLSMode
from utils.views import ConfirmView


class Controller:
    def __init__(
        self, client: Bot, config: Config, tls_mode: TLSMode = TLSMode.DISABLED
    ) -> None:
        self.client = client
        self.config = config
        self._mc_controller = MinecraftController(config, tls_mode)

    async def connect(self) -> None:
        await self._mc_controller.connect()

    async def close(self) -> None:
        if not self._mc_controller.is_closed:
            await self._mc_controller.close()

    def get_avatar(self, username: str) -> str:
        return f"https://mineskin.eu/armor/body/{username}/100.png"

    async def log_action(self, ctx: Optional[ApplicationContext], embed: Embed) -> None:
        if logs_channel := self.config.logs_channel:
            if logs_channel := self.client.get_channel(logs_channel):
                try:
                    await logs_channel.send(
                        content=f"## Executed by {ctx.author.mention if ctx else '` System `'}",
                        embed=embed,
                    )
                except HTTPException:
                    error(f"Failed to send log message to {logs_channel}.")

    async def command(self, ctx: ApplicationContext, command: str) -> Any:
        result = await self._mc_controller.command(command, True)
        embed = Embed(title="Command executed")
        embed.add_field(name="Input", value=f"``` {command} ```")
        embed.add_field(name="Output", value=f"``` {result[:1016]} ```")
        if len(result) > 1016:
            embed.set_footer(text="The result is too long to display in full.")
        await self.log_action(ctx, embed)
        await ctx.respond(embed=embed)

    async def whitelist_add(self, ctx: ApplicationContext, username: str) -> Any:
        if await Connection.exists(~Q(user_id=ctx.author.id) & Q(username=username)):
            return await ctx.respond(
                "❌ Your username is already taken, please contact admin."
            )

        if connection := await Connection.get_or_none(user_id=ctx.author.id):
            if connection.is_banned:
                return await ctx.respond("❌ You're banned from the server.")
            if connection.username == username:
                await self._mc_controller.whitelist_add(username)
                return await ctx.respond(
                    "❌ Your username is already whitelisted - re-added connection."
                )

            await self._mc_controller.whitelist_remove(
                connection.username, "Changed username"
            )
            await self._mc_controller.whitelist_add(username)

            embed = Embed(title="Whitelist user updated", color=Color.gold())
            embed.add_field(name="Discord", value=ctx.author.mention)
            embed.add_field(
                name="Minecraft", value=f"` {connection.username} ` ➜ ` {username} `"
            )
            embed.set_thumbnail(url=self.get_avatar(username))

            connection.username = username
            await connection.save()

            await self.log_action(ctx, embed)
            return await ctx.respond(embed=embed)

        await self._mc_controller.whitelist_add(username)
        await Connection.create(user_id=ctx.author.id, username=username)

        embed = Embed(title="Whitelist user added", color=Color.brand_green())
        embed.add_field(name="Discord", value=ctx.author.mention)
        embed.add_field(name="Minecraft", value=username)
        embed.set_thumbnail(url=self.get_avatar(username))
        await self.log_action(ctx, embed)
        await ctx.respond(embed=embed)

    async def whitelist_remove(
        self,
        ctx: Optional[ApplicationContext],
        user: Union[User, str],
        reason: Optional[str] = None,
    ) -> Any:
        filters = {"username": user} if isinstance(user, str) else {"user_id": user.id}
        connection = await Connection.get_or_none(**filters)

        if not isinstance(user, str) and (not connection or not connection.username):
            if ctx:
                await ctx.respond("❌ User not found!")
            return

        username = user if isinstance(user, str) else connection.username
        await self._mc_controller.whitelist_remove(username, reason)

        embed = Embed(title="Whitelist user removed", color=Color.brand_red())
        if connection:
            embed.add_field(name="Discord", value=f"<@{connection.user_id}>")
            if not connection.is_banned:
                await connection.delete()

        embed.add_field(name="Minecraft", value=username)
        embed.add_field(
            name="Reason", value=reason or "No reason provided.", inline=False
        )
        await self.log_action(ctx, embed)
        if ctx:
            await ctx.respond(embed=embed)

    async def user_check(self, ctx: ApplicationContext, user: Union[User, str]) -> Any:
        filters = {"username": user} if isinstance(user, str) else {"user_id": user.id}
        connection = await Connection.get_or_none(**filters)

        if not connection:
            return await ctx.respond("❌ User not found!")

        user_id = connection.user_id
        username = connection.username
        ban_reason = connection.ban_reason

        embed = Embed(title="User check", color=Color.blurple())
        embed.add_field(name="Discord", value=f"<@{user_id}>")
        embed.add_field(name="Minecraft", value=f"{username or 'Not set'}")
        if connection.is_banned:
            embed.add_field(
                name="Ban reason",
                value=ban_reason or "No reason provided.",
                inline=False,
            )
        await ctx.respond(embed=embed)

    async def user_ban(
        self,
        ctx: ApplicationContext,
        user: Union[User, str],
        reason: Optional[str] = None,
    ) -> Any:
        filters = {"username": user} if isinstance(user, str) else {"user_id": user.id}
        connection = await Connection.get_or_none(**filters)

        if not connection:
            if isinstance(user, str):
                view = ConfirmView(ctx.author)
                await ctx.respond(
                    "Connected user not found, continue with only Minecraft ban?",
                    view=view,
                )
                if not await view.wait():
                    await self._mc_controller.ban_add(user, reason)
                    embed = Embed(title="User ban", color=Color.brand_red())
                    embed.add_field(name="Minecraft", value=user)
                    await self.log_action(ctx, embed)
                    await ctx.followup.send(embed=embed, ephemeral=True)
                return

            connection = await Connection.create(
                user_id=user.id, is_banned=True, ban_reason=reason
            )
            embed = Embed(title="User ban", color=Color.brand_red())
            embed.add_field(name="Discord", value=f"<@{user.id}>")
            embed.add_field(
                name="Reason", value=reason or "No reason provided.", inline=False
            )
            await self.log_action(ctx, embed)
            await ctx.respond(embed=embed)

        connection.is_banned = True
        connection.ban_reason = reason
        await connection.save()

        user_id = connection.user_id
        username = connection.username

        await self._mc_controller.ban_add(connection.username, reason)

        embed = Embed(title="User ban", color=Color.brand_red())
        embed.add_field(name="Discord", value=f"<@{user_id}>")
        embed.add_field(name="Minecraft", value=f"{username or 'Not set'}")
        await self.log_action(ctx, embed)
        await ctx.respond(embed=embed)

    async def user_unban(
        self,
        ctx: ApplicationContext,
        user: Union[User, str],
    ) -> Any:
        filters = {"username": user} if isinstance(user, str) else {"user_id": user.id}
        connection = await Connection.get_or_none(**filters)

        if not connection:
            if isinstance(user, str):
                view = ConfirmView(ctx.author)
                await ctx.respond(
                    "Connected user not found, continue with only Minecraft unban?",
                    view=view,
                )
                if not await view.wait():
                    await self._mc_controller.ban_remove(user)
                    await self._mc_controller.whitelist_add(user)
                    embed = Embed(title="User unban", color=Color.brand_green())
                    embed.add_field(name="Minecraft", value=user)
                    await self.log_action(ctx, embed)
                    await ctx.followup.send(embed=embed, ephemeral=True)
                return
            return await ctx.respond("❌ User not found!")

        user_id = connection.user_id
        username = connection.username

        if username:
            await self._mc_controller.ban_remove(username)
            await self._mc_controller.whitelist_add(username)

        embed = Embed(title="User unban", color=Color.brand_green())
        embed.add_field(name="Discord", value=f"<@{user_id}>")
        embed.add_field(name="Minecraft", value=f"{username or 'Not set'}")

        if connection.username:
            connection.is_banned = False
            connection.ban_reason = None
            await connection.save()
        else:
            await connection.delete()

        await self.log_action(ctx, embed)
        await ctx.respond(embed=embed)
