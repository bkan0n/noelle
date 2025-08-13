from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from core.noelle import Noelle

    NoelleCtx = commands.Context[Noelle]


def youngnebula_or_sumpin_check(ctx: commands.Context) -> bool:
    """Check if author is youngnebula or sumpin."""
    return ctx.message.author.id in (141372217677053952, 243088306764513280)


class HousekeepingCog(commands.Cog):
    def __init__(self, bot: Noelle) -> None:
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.check(youngnebula_or_sumpin_check)
    async def sync(
        self,
        ctx: NoelleCtx,
        guilds: commands.Greedy[discord.Object],
        spec: Literal["~", "*", "^", "$"] | None = None,
    ) -> None:
        """Sync commands to Discord.

        ?sync -> global sync
        ?sync ~ -> sync current guild
        ?sync * -> copies all global app commands to current guild and syncs
        ?sync ^ -> clears all commands from the current
                        guild target and syncs (removes guild commands)
        ?sync id_1 id_2 -> syncs guilds with id 1 and 2
        >sync $ -> Clears global commands
        """
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                assert ctx.guild
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            elif spec == "$":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync()
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot: Noelle) -> None:
    """Load the HousekeepingCog cog."""
    await bot.add_cog(HousekeepingCog(bot))
