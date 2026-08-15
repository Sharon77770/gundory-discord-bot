from typing import Callable, List

import discord

from app.database.models import MilitaryEvent
from app.utils.dates import event_end
from app.services.event_service import type_label


class EventListView(discord.ui.View):
    def __init__(self, owner_id: int, events: List[MilitaryEvent], render: Callable[[int], discord.Embed]):
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.events = events
        self.render = render
        self.page = 0
        self.page_size = 5
        self._sync_buttons()

    def _sync_buttons(self):
        self.previous.disabled = self.page <= 0
        self.next.disabled = (self.page + 1) * self.page_size >= len(self.events)

    @property
    def pages(self) -> int:
        return max(1, (len(self.events) + self.page_size - 1) // self.page_size)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("이 일정 목록은 명령을 실행한 사람만 넘길 수 있습니다.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, _button: discord.ui.Button):
        self.page -= 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.render(self.page), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, _button: discord.ui.Button):
        self.page += 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.render(self.page), view=self)


def render_event_page(events: List[MilitaryEvent], page: int, display_name: str) -> discord.Embed:
    view_events = events[page * 5:(page + 1) * 5]
    embed = discord.Embed(title=f"📋 {display_name}의 일정", color=discord.Color.dark_red())
    for event in view_events:
        end = event_end(event.start_date, event.end_date)
        period = event.start_date.strftime("%Y.%m.%d") if end == event.start_date else f"{event.start_date:%Y.%m.%d} ~ {end:%Y.%m.%d}"
        value = f"{period} · {type_label(event.event_type)}\nID: {event.id}"
        if event.memo:
            value += f"\n{event.memo}"
        embed.add_field(name=event.title, value=value, inline=False)
    embed.set_footer(text=f"페이지 {page + 1}/{max(1, (len(events) + 4) // 5)}")
    return embed

