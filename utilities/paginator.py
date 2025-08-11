from __future__ import annotations

import contextlib
from datetime import timedelta
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord import Interaction

    from core.noelle import Noelle

    NoelleItx = Interaction[Noelle]


class Paginator(discord.ui.View):
    """A view for paginating multiple embeds."""

    original_itx: NoelleItx
    end_time: str

    def __init__(self, embeds: list[discord.Embed], author: discord.Member, timeout: int = 600) -> None:
        """Init paginator."""
        super().__init__(timeout=timeout)
        self.pages = embeds
        self.author = author
        self._curr_page = 0
        self.page_number.label = f"1/{len(self.pages)}"
        self._update_end_time()
        if len(self.pages) > 1:
            return
        for component in self.children:
            if isinstance(component, discord.ui.Button):
                component.disabled = True

    def _update_end_time(self) -> None:
        assert self.timeout
        time = discord.utils.format_dt(discord.utils.utcnow() + timedelta(seconds=self.timeout), "R")
        self.end_time = "This command will time out " + time

    async def start(self, itx: NoelleItx) -> None:
        """Start the pagination view."""
        await itx.edit_original_response(
            content=self.end_time,
            embed=self.pages[0],
            view=self,
        )
        self.original_itx = itx
        await self.wait()

    async def interaction_check(self, itx: NoelleItx) -> bool:
        """Check if the itx user is the original users who started the itx."""
        return itx.user == self.author

    async def on_timeout(self) -> None:
        """Stop view on timeout."""
        self.clear_items()
        with contextlib.suppress(discord.HTTPException):
            await self.original_itx.edit_original_response(
                content=None,
                embed=self.pages[self._curr_page],
                view=self,
            )

        return await super().on_timeout()

    async def change_page(self, itx: NoelleItx) -> None:
        """Change the current page in paginator."""
        self.page_number.label = f"{self._curr_page + 1}/{len(self.pages)}"
        await itx.response.edit_message(content=self.end_time, embed=self.pages[self._curr_page], view=self)

    @discord.ui.button(label="First", emoji="⏮", row=4)
    async def first(self, itx: NoelleItx, button: discord.ui.Button) -> None:
        """Button component to return to the first pagination page."""
        self._curr_page = 0
        return await self.change_page(itx)

    @discord.ui.button(label="Back", emoji="◀", row=4)
    async def back(self, itx: NoelleItx, button: discord.ui.Button) -> None:
        """Button component to go back to the last pagination page."""
        self._curr_page = (self._curr_page - 1) % len(self.pages)
        return await self.change_page(itx)

    @discord.ui.button(label="...", disabled=True, row=4)
    async def page_number(self, itx: NoelleItx, button: discord.ui.Button) -> None:
        """Button component to visualize the page number."""

    @discord.ui.button(label="Next", emoji="▶", row=4)
    async def next(self, itx: NoelleItx, button: discord.ui.Button) -> None:
        """Button component to go to the next pagination page."""
        self._curr_page = (self._curr_page + 1) % len(self.pages)
        return await self.change_page(itx)

    @discord.ui.button(label="Last", emoji="⏭", row=4)
    async def last(self, itx: NoelleItx, button: discord.ui.Button) -> None:
        """Button component to go to the last pagination page."""
        self._curr_page = len(self.pages) - 1
        return await self.change_page(itx)
