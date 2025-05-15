from typing import List, Any, TypedDict, Literal

import discord
import msgspec
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from rapidfuzz import process, fuzz, utils


class CharacterInfo(msgspec.Struct):
    character_name: str
    video_url: str
    guide_image_url: str
    character_icon_url: str
    element: Literal["pyro", "cryo", "hydro", "dendro", "anemo", "geo", "electro"]

    @property
    def element_color(self):
        return ELEMENTS[self.element]["color"]

    @property
    def element_icon(self):
        return ELEMENTS[self.element]["icon"]


class ElementData(TypedDict):
    color: str
    icon: str


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
        "icon": "https://cdn.discordapp.com/attachments/1372695311369109594/1372695727590998208/Fire.png",
    },
    "cryo": {
        "color": "#75a9d8",
        "icon": "https://cdn.discordapp.com/attachments/1372695311369109594/1372695669223063642/Ice.png",
    },
    "hydro": {
        "color": "#248fbd",
        "icon": "https://cdn.discordapp.com/attachments/1372695311369109594/1372695712827183134/Water.png",
    },
    "dendro": {
        "color": "#7553c3",
        "icon": "https://cdn.discordapp.com/attachments/1372695311369109594/1372695654127632394/Grass.png",
    },
    "anemo": {
        "color": "#289d93",
        "icon": "https://cdn.discordapp.com/attachments/1372695311369109594/1372695638948708462/Wind.png",
    },
    "geo": {
        "color": "#e5a659",
        "icon": "https://cdn.discordapp.com/attachments/1372695311369109594/1372695627124703263/Rock.png",
    },
    "electro": {
        "color": "7553c3",
        "icon": "https://cdn.discordapp.com/attachments/1372695311369109594/1372695683575975977/Elec.png",
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
                f"Character ({personagem}) not found.", ephemeral=True
            )
            return

        char = CHARACTER_INFO[personagem]

        embed = discord.Embed(
            description=f"[{personagem} Guide]({char.video_url})",
            color=discord.Color.from_str(char.element_color),
        )
        embed.set_author(name=char.character_name, icon_url=char.element_icon)
        embed.set_image(url=char.guide_image_url)
        embed.set_thumbnail(url=char.character_icon_url)
        embed.set_footer(
            text="Tudo é só sugestão — builde seu boneco com o que você tem e o que fizer sentido pro seu jogo",
            icon_url="https://cdn.discordapp.com/attachments/1372695311369109594/1372701860179476520/warning-genshin.png",
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PersonagemCog(bot))
