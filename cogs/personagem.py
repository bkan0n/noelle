from typing import List, Any

import discord
import msgspec
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from rapidfuzz import process, fuzz, utils


class CharacterInfo(msgspec.Struct):
    name: str
    url: str
    image: str


with open("/data/character_build_data.json", "r") as f:
    _list = msgspec.json.decode(f.read(), type=list[CharacterInfo])
CHARACTER_INFO: dict[str, CharacterInfo] = {}
for _char in _list:
    CHARACTER_INFO[_char.name] = _char


class CharacterNameTransformer(discord.app_commands.Transformer):
    async def autocomplete(
        self, interaction: Interaction, value: str
    ) -> List[Choice[str]]:
        fuzzed = process.extract(  # type: ignore
            value,
            CHARACTER_INFO.keys(),
            scorer=fuzz.WRatio,
            limit=5,
            processor=utils.default_process,
        )
        return [discord.app_commands.Choice(name=x[0], value=x[0]) for x in fuzzed]

    async def transform(self, interaction: Interaction, value: Any, /) -> Any:
        fuzzed = process.extractOne(  # type: ignore
            value,
            CHARACTER_INFO.keys(),
            scorer=fuzz.WRatio,
            processor=utils.default_process,
        )
        return fuzzed[0]


class PersonagemCog(commands.Cog):
    character_info: dict[str, CharacterInfo]

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command()
    async def build(
        self,
        interaction: discord.Interaction,
        personagem: app_commands.Transform[str, CharacterNameTransformer],
    ) -> None:
        """Encontre um guia de personagem

        Args:
            personagem (str): Nome do personagem
        """
        if personagem not in CHARACTER_INFO:
            await interaction.response.send_message(
                f"Character ({personagem}) not found.", ephemeral=True
            )
            return

        resolved_character = CHARACTER_INFO[personagem]

        embed = discord.Embed(
            title=personagem,
            description=f"[{personagem} Guide]({resolved_character.url})",
        )
        embed.set_image(
            url=resolved_character.image,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PersonagemCog(bot))
