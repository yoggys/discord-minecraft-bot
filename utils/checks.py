from typing import Any, Optional

from discord import ApplicationContext, User

from utils.config import Config


async def check_allowed(ctx: ApplicationContext, config: Config) -> Any:
    if config.allowed_roles and not any(
        [role.id in config.allowed_roles for role in ctx.author.roles]
    ):
        return await ctx.respond(
            "❌ You're not allowed to use this command.", ephemeral=True
        )


async def check_admin(
    ctx: ApplicationContext, user: Optional[User], username: Optional[str]
) -> Any:
    if not user and not username:
        return await ctx.respond(
            "❌ You have to provide Discord user or Minecraft username.", ephemeral=True
        )
