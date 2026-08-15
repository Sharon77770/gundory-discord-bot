from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from sqlalchemy import select

from app.bot.views.calendar_view import CalendarView, build_calendar_embed
from app.database.database import session_scope
from app.database.models import MilitaryEvent, MilitaryProfile
from app.services.event_service import overlaps_month, type_icon, type_label
from app.utils.dates import event_end, month_bounds, today
from app.utils.embeds import error_embed


def member_name(guild: discord.Guild, user_id: int) -> str:
    member = guild.get_member(user_id)
    if member:
        return member.display_name
    with session_scope() as session:
        profile = session.scalar(select(MilitaryProfile).where(
            MilitaryProfile.guild_id == guild.id,
            MilitaryProfile.discord_user_id == user_id,
        ))
    return profile.display_name if profile else "알 수 없는 사용자"


class CalendarCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="캘린더", description="서버 전체 군생활 일정을 월간 캘린더로 봅니다.")
    async def calendar(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        current = today()
        name = lambda user_id: member_name(interaction.guild, user_id)
        view = CalendarView(interaction.guild.id, current.year, current.month, name)
        await interaction.response.send_message(embed=build_calendar_embed(interaction.guild.id, current.year, current.month, name), view=view)

    @app_commands.command(name="이번주", description="이번 주 서버 전체 주요 일정을 봅니다.")
    async def this_week(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        start = today() - timedelta(days=today().weekday())
        end = start + timedelta(days=6)
        with session_scope() as session:
            events = list(session.scalars(select(MilitaryEvent).where(MilitaryEvent.guild_id == interaction.guild.id)))
        lines = []
        for offset in range(7):
            current = start + timedelta(days=offset)
            active = [event for event in events if event.start_date <= current <= event_end(event.start_date, event.end_date)]
            if active:
                lines.append(f"**{current:%m/%d (%a)}**")
                for event in sorted(active, key=lambda item: item.start_date):
                    lines.append(f"{type_icon(event.event_type)} {member_name(interaction.guild, event.discord_user_id)} · {type_label(event.event_type)} {event.title}")
        embed = discord.Embed(title="📆 이번 주 브라이어 일정", description="\n".join(lines) if lines else "이번 주 일정이 없습니다.", color=discord.Color.dark_red())
        await interaction.response.send_message(embed=embed)
