import logging
from datetime import date
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.views.event_list_view import EventListView, render_event_page
from app.database.database import session_scope
from app.services.event_service import EVENT_TYPES, create_event, delete_event, get_owned_event, list_events, type_label, update_event
from app.utils.dates import event_end, parse_date, today
from app.utils.embeds import error_embed, event_embed

logger = logging.getLogger("briar.commands.events")
TYPE_CHOICES = [app_commands.Choice(name=name, value=value) for value, (name, _icon) in EVENT_TYPES.items()]


class EventsCog(commands.Cog):
    events = app_commands.Group(name="일정", description="군생활 일정 명령어")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @events.command(name="등록", description="군생활 일정을 등록합니다.")
    @app_commands.describe(종류="일정 종류", 제목="일정 제목", 시작일="YYYY-MM-DD", 종료일="생략하면 당일", 메모="선택 메모")
    @app_commands.choices(종류=TYPE_CHOICES)
    async def create(self, interaction: discord.Interaction, 종류: app_commands.Choice[str], 제목: str, 시작일: str,
                     종료일: Optional[str] = None, 메모: Optional[str] = None):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        try:
            start, end = parse_date(시작일), parse_date(종료일) if 종료일 else None
            with session_scope() as session:
                event = create_event(session, interaction.guild.id, interaction.user.id, 종류.value, 제목, start, end, 메모)
            await interaction.response.send_message(embed=event_embed(event, interaction.user.display_name, "일정 등록 완료"))
            logger.info("event created event_id=%s guild=%s user=%s", event.id, interaction.guild.id, interaction.user.id)
        except ValueError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @events.command(name="목록", description="내 일정을 페이지별로 확인합니다.")
    @app_commands.describe(과거포함="과거 일정을 포함할지 여부")
    async def list(self, interaction: discord.Interaction, 과거포함: bool = False):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        with session_scope() as session:
            events = list_events(session, interaction.guild.id, interaction.user.id, 과거포함, today())
        if not events:
            await interaction.response.send_message(embed=discord.Embed(title="📋 일정 목록", description="표시할 일정이 없습니다.", color=discord.Color.dark_red()))
            return
        view = EventListView(interaction.user.id, events, lambda page: render_event_page(events, page, interaction.user.display_name))
        await interaction.response.send_message(embed=render_event_page(events, 0, interaction.user.display_name), view=view)

    @events.command(name="삭제", description="내가 등록한 일정을 삭제합니다.")
    @app_commands.describe(일정번호="/일정 목록에 표시된 ID")
    async def delete(self, interaction: discord.Interaction, 일정번호: int):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        with session_scope() as session:
            event = get_owned_event(session, interaction.guild.id, interaction.user.id, 일정번호)
            if event:
                title = event.title
                delete_event(session, event)
            else:
                title = None
        if title is None:
            await interaction.response.send_message(embed=error_embed("존재하지 않거나 내가 등록한 일정이 아닙니다."), ephemeral=True)
            return
        await interaction.response.send_message(embed=discord.Embed(title="🗑️ 일정 삭제 완료", description=f"`{title}` 일정을 삭제했습니다.", color=discord.Color.dark_red()))

    @events.command(name="수정", description="내가 등록한 일정을 수정합니다.")
    @app_commands.describe(일정번호="수정할 일정 ID", 종류="일정 종류", 제목="일정 제목", 시작일="YYYY-MM-DD", 종료일="생략하면 당일", 메모="선택 메모")
    @app_commands.choices(종류=TYPE_CHOICES)
    async def update(self, interaction: discord.Interaction, 일정번호: int, 종류: app_commands.Choice[str], 제목: str,
                     시작일: str, 종료일: Optional[str] = None, 메모: Optional[str] = None):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        try:
            start, end = parse_date(시작일), parse_date(종료일) if 종료일 else None
            with session_scope() as session:
                event = get_owned_event(session, interaction.guild.id, interaction.user.id, 일정번호)
                if not event:
                    raise ValueError("존재하지 않거나 내가 등록한 일정이 아닙니다.")
                update_event(session, event, 종류.value, 제목, start, end, 메모)
            await interaction.response.send_message(embed=event_embed(event, interaction.user.display_name, "일정 수정 완료"))
        except ValueError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
