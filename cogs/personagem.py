from typing import List, Any, TypedDict, Literal

import discord
import msgspec
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from rapidfuzz import process, fuzz, utils


class CharacterInfo(msgspec.Struct):
    character_name: str
    guide_video_url: str
    guide_image_url: str
    character_icon_url: str
    element: Literal["pyro", "cryo", "hydro", "dendro", "anemo", "geo", "electro"]

    @property
    def element_color(self):
        return ELEMENTS[self.element]["color"]

    @property
    def element_emoji(self):
        return ELEMENTS[self.element]["emoji"]


class ElementData(TypedDict):
    color: str
    emoji: str


class Elements(TypedDict):
    pyro: ElementData
    cryo: ElementData
    hydro: ElementData
    dendro: ElementData
    anemo: ElementData
    geo: ElementData
    electro: ElementData


ELEMENTS: Elements = {
    "pyro": {
        "color": "#b7242a",
        "emoji": "<:_:1372712159661916212>",
    },
    "cryo": {
        "color": "#75a9d8",
        "emoji": "<:_:1372712163516354631>",
    },
    "hydro": {
        "color": "#248fbd",
        "emoji": "<:_:1372712160869748758>",
    },
    "dendro": {
        "color": "#7553c3",
        "emoji": "<:_:1372712164439101450>",
    },
    "anemo": {
        "color": "#289d93",
        "emoji": "<:_:1372712165408116828>",
    },
    "geo": {
        "color": "#e5a659",
        "emoji": "<:geo:1372710383260930048>",
    },
    "electro": {
        "color": "7553c3",
        "emoji": "<:_:1372712162471972984>",
    },
}


with open("/data/character_build_data.json", "r") as f:
    _list = msgspec.json.decode(f.read(), type=list[CharacterInfo])

CHARACTER_INFO: dict[str, CharacterInfo] = {}
for _char in _list:
    CHARACTER_INFO[_char.character_name] = _char


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
        """Encontre um guia de build para um personagem

        Args:
            personagem (str): Nome do personagem
        """
        if personagem not in CHARACTER_INFO:
            await interaction.response.send_message(
                f"Personagem ({personagem}) não encontrado.", ephemeral=True
            )
            return

        char = CHARACTER_INFO[personagem]

        embed = discord.Embed(
            description=(
                f"## {char.element_emoji} {char.character_name}\n\n"
                "> ### Guia Detalhado no YouTube:\n"
                f"> ## [Link do Vídeo!]({char.guide_video_url})"
            ),
            color=discord.Color.from_str(char.element_color),
        )
        embed.set_image(url=char.guide_image_url)
        embed.set_thumbnail(url=char.character_icon_url)
        embed.set_footer(
            text="Tudo é só recomendação — builde seu personagem com o que você tem e o que fizer sentido pro seu jogo!",
            icon_url="https://cdn.discordapp.com/attachments/1372695311369109594/1372703311513522176/warning-genshin.png",
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PersonagemCog(bot))
