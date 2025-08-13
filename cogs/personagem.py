from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

import discord
import msgspec
from discord import app_commands
from discord.ext import commands
from rapidfuzz import fuzz, process, utils

from utilities.paginator import Paginator

if TYPE_CHECKING:
    from discord import Interaction

    from core.noelle import Noelle

    NoelleItx = Interaction[Noelle]


class CharacterInfo(msgspec.Struct):
    character_name: str
    guide_video_url: str
    guide_image_url: str
    character_icon_url: str
    element: Literal["pyro", "cryo", "hydro", "dendro", "anemo", "geo", "electro"]

    @property
    def element_color(self) -> str:
        return ELEMENTS[self.element]["color"]

    @property
    def element_emoji(self) -> str:
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
        "color": "#ff935e",
        "emoji": "<:_:1372712159661916212>",
    },
    "cryo": {
        "color": "#abfafa",
        "emoji": "<:_:1372712163516354631>",
    },
    "hydro": {
        "color": "#52d2ff",
        "emoji": "<:_:1372712160869748758>",
    },
    "dendro": {
        "color": "#d0f281",
        "emoji": "<:_:1372712164439101450>",
    },
    "anemo": {
        "color": "#51ebba",
        "emoji": "<:_:1372712165408116828>",
    },
    "geo": {
        "color": "#e2c83c",
        "emoji": "<:geo:1372710383260930048>",
    },
    "electro": {
        "color": "#e1a5ff",
        "emoji": "<:_:1372712162471972984>",
    },
}


with open("/data/character_build_data.json", "r") as f:
    _list = msgspec.json.decode(f.read(), type=list[CharacterInfo])

CHARACTER_INFO: dict[str, CharacterInfo] = dict(
    sorted(
        ((_char.character_name, _char) for _char in _list),
        key=lambda item: item[0].lower(),
    )
)


class CharacterNameTransformer(app_commands.Transformer):
    async def autocomplete(self, itx: NoelleItx, value: str) -> list[app_commands.Choice[str]]:
        fuzzed = process.extract(  # type: ignore
            value,
            CHARACTER_INFO.keys(),
            scorer=fuzz.WRatio,
            limit=5,
            processor=utils.default_process,
        )
        return [app_commands.Choice(name=x[0], value=x[0]) for x in fuzzed]

    async def transform(self, itx: NoelleItx, value: str) -> str:
        fuzzed = process.extractOne(  # type: ignore
            value,
            CHARACTER_INFO.keys(),
            scorer=fuzz.WRatio,
            processor=utils.default_process,
        )
        return fuzzed[0]


class CharacterPaginator(Paginator):
    def __init__(self, embeds: list[discord.Embed], author: discord.Member, character_names: list[list[str]]) -> None:
        super().__init__(embeds, author)
        self.character_names_per_page = character_names
        self.character_select = CharacterSelect(character_names[0])
        self.add_item(self.character_select)

    async def change_page(self, itx: NoelleItx) -> None:
        self.character_select = CharacterSelect(self.character_names_per_page[self._curr_page])
        return await super().change_page(itx)


def _build_character_guide(personagem: str) -> discord.Embed:
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
        text=("Tudo é só recomendação — builde seu personagem com o que você tem e o que fizer sentido pro seu jogo!"),
        icon_url="https://cdn.discordapp.com/attachments/1372695311369109594/1372890662961152070/warning-genshin.png",
    )
    return embed


class CharacterSelect(discord.ui.Select):
    def __init__(self, character_names: list[str]) -> None:
        options = [discord.SelectOption(label=c, value=c) for c in character_names]
        super().__init__(placeholder="Ver personagem", options=options)

    async def callback(self, itx: NoelleItx) -> None:
        embed = _build_character_guide(self.values[0])
        await itx.response.send_message(embed=embed)


class CharacterCog(commands.Cog):
    def __init__(self, bot: Noelle) -> None:
        self.bot = bot

    @app_commands.command()
    async def build(
        self,
        itx: NoelleItx,
        personagem: app_commands.Transform[str, CharacterNameTransformer],
    ) -> None:
        """Encontre um guia de build para um personagem.

        Args:
            itx (Noelle): Interaction object
            personagem (str): Nome do personagem

        """
        if personagem not in CHARACTER_INFO:
            await itx.response.send_message(f"Personagem ({personagem}) não encontrado.", ephemeral=True)
            return
        embed = _build_character_guide(personagem)
        await itx.response.send_message(embed=embed)

    @app_commands.command(name="list")
    async def view_all_guides(self, itx: NoelleItx) -> None:
        """Veja a lista dos persoagens que já criamos guia."""
        char_chunks = list(discord.utils.as_chunks(CHARACTER_INFO, 10))
        embeds = [
            discord.Embed(
                title="Lista dos Nossos Guias!",
                description="\n".join(chunk),
            )
            for chunk in char_chunks
        ]
        for embed in embeds:
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1372695311369109594/1404896788451688539/Noelle_List.png"
            )

        assert isinstance(itx.user, discord.Member)
        paginator = CharacterPaginator(embeds, itx.user, char_chunks)
        await paginator.start(itx)


async def setup(bot: Noelle) -> None:
    """Load the CharacterCog cog."""
    await bot.add_cog(CharacterCog(bot))
