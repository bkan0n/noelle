import logging

import discord
from discord.ext import commands
from discord.ext.commands import Context, errors

import cogs

intents = discord.Intents.all()

log = logging.getLogger(__name__)


class Noelle(commands.Bot):
    def __init__(self) -> None:
        super().__init__("!", intents=intents)

    async def setup_hook(self) -> None:
        """Execute code during setup.

        The setup_hook function is called when the bot is starting up.
        It's responsible for loading all the cogs that are in
        the initial_extensions list. This function is also used
        to start a connection with the database,
        and register any tasks that need to be run on a loop.

        Args:
            self: bot instance

        Returns:
            None

        """
        for ext in [*cogs.EXTENSIONS, "jishaku"]:
            log.info(f"Loading {ext}...")
            await self.load_extension(ext)
        log.info("Setup complete.")

    async def on_command_error(self, context: Context, exception: errors.CommandError) -> None:
        if isinstance(exception, errors.CommandNotFound):
            return
