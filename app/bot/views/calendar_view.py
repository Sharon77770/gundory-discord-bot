import asyncio
from calendar import monthrange
from datetime import date
from typing import Callable, Optional

import discord

from app.database.database import session_scope
from app.database.models import MilitaryEvent, MilitaryProfile
from app.services.calendar_service import calendar_text, month_detail_lines
from app.utils.dates import month_bounds, month_shift, today


def build_calendar_embed(guild_id: int, year: int, month: int, display_name: Callable[[int], str]) -> discord.Embed:
    month_start, month_end = month_bounds(year, month)
    with session_scope() as session:
        events = list(session.query(MilitaryEvent).filter(MilitaryEvent.guild_id == guild_id).all())
        embed = discord.Embed(title=f"📆 Briar 공용 캘린더 · {year}년 {month}월", color=discord.Color.dark_red())
        embed.description = calendar_text(year, month, events)
        details = month_detail_lines(events, {event.discord_user_id: display_name(event.discord_user_id) for event in events}, month_start, month_end)
    if details:
        # Discord field values have a 1024-character limit.
        chunk = "\n\n".join(details)
        embed.add_field(name="이번 달 일정", value=chunk[:1024], inline=False)
        if len(chunk) > 1024:
            embed.add_field(name="일정 더보기", value="일정이 많아 일부만 표시했습니다. `/일정 목록`을 이용해주세요.", inline=False)
    else:
        embed.add_field(name="이번 달 일정", value="등록된 일정이 없습니다.", inline=False)
    embed.set_footer(text="날짜에 [ ]가 표시되면 일정이 있는 날입니다.")
    return embed


class CalendarView(discord.ui.View):
    def __init__(self, guild_id: int, year: int, month: int, display_name: Callable[[int], str]):
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.year = year
        self.month = month
        self.display_name = display_name
        self._lock = asyncio.Lock()

    async def _update(self, interaction: discord.Interaction, offset: int) -> None:
        async with self._lock:
            if offset == 0:
                current = today()
                self.year, self.month = current.year, current.month
            else:
                self.year, self.month = month_shift(self.year, self.month, offset)
            await interaction.response.edit_message(
                embed=build_calendar_embed(self.guild_id, self.year, self.month, self.display_name), view=self
            )

    @discord.ui.button(label="◀ 이전 달", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._update(interaction, -1)

    @discord.ui.button(label="● 이번 달", style=discord.ButtonStyle.primary)
    async def current(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._update(interaction, 0)

    @discord.ui.button(label="다음 달 ▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._update(interaction, 1)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
