from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Tuple

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from app.database.database import session_scope
from app.database.models import MilitaryEvent, MilitaryProfile
from app.services.event_service import type_label
from app.services.military_service import next_leave_for_user
from app.utils.dates import d_day, event_end, intervals_overlap, today
from app.utils.embeds import error_embed


def find_overlapping_leaves(events: List[MilitaryEvent]) -> List[Tuple[date, date, Set[int]]]:
    leaves = [(event.start_date, event_end(event.start_date, event.end_date), event.discord_user_id) for event in events if event.event_type == "LEAVE"]
    if len(leaves) < 2:
        return []
    boundaries = sorted({point for start, end, _user in leaves for point in (start, end + timedelta(days=1))})
    segments: List[Tuple[date, date, Set[int]]] = []
    for left, right_exclusive in zip(boundaries, boundaries[1:]):
        users = {user for start, end, user in leaves if start <= left <= end}
        if users and len(users) >= 2:
            segment = (left, right_exclusive - timedelta(days=1), users)
            if segments and segments[-1][1] + timedelta(days=1) == segment[0] and segments[-1][2] == users:
                segments[-1] = (segments[-1][0], segment[1], users)
            else:
                segments.append(segment)
    return segments


class SpecialCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="다음휴가", description="가장 가까운 휴가를 확인합니다.")
    @app_commands.describe(사용자="확인할 서버 구성원 (생략하면 본인)")
    async def next_leave(self, interaction: discord.Interaction, 사용자: Optional[discord.Member] = None):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        target = 사용자 or interaction.user
        with session_scope() as session:
            event = next_leave_for_user(session, interaction.guild.id, target.id, today())
        if not event:
            await interaction.response.send_message(embed=discord.Embed(title="🩸 다음 탈출", description=f"{target.display_name}님의 예정된 휴가가 없습니다.", color=discord.Color.dark_red()))
            return
        end = event_end(event.start_date, event.end_date)
        nights = (end - event.start_date).days
        embed = discord.Embed(title="🩸 다음 탈출", color=discord.Color.dark_red())
        embed.description = f"**{target.display_name}**\n{event.start_date:%Y.%m.%d} ~ {end:%Y.%m.%d}\n\n**{d_day(event.start_date, today())}**\n{nights}박 {nights + 1}일 · {event.title}"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="겹치는휴가", description="서버 구성원들의 겹치는 휴가를 찾습니다.")
    async def overlapping(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        with session_scope() as session:
            events = list(session.scalars(select(MilitaryEvent).where(MilitaryEvent.guild_id == interaction.guild.id, MilitaryEvent.event_type == "LEAVE")))
            profiles = {
                profile.discord_user_id: profile.display_name
                for profile in session.scalars(select(MilitaryProfile).where(MilitaryProfile.guild_id == interaction.guild.id))
            }
        segments = find_overlapping_leaves(events)
        if not segments:
            await interaction.response.send_message(embed=discord.Embed(title="🤝 같이 살아있는 날", description="겹치는 휴가가 없습니다.", color=discord.Color.dark_red()))
            return
        lines = []
        for start, end, users in segments:
            names = [
                interaction.guild.get_member(user_id).display_name
                if interaction.guild.get_member(user_id)
                else profiles.get(user_id, "알 수 없는 사용자")
                for user_id in sorted(users)
            ]
            lines.append(f"**{start:%m/%d} ~ {end:%m/%d}**\n" + "\n".join(names))
        await interaction.response.send_message(embed=discord.Embed(title="🤝 같이 살아있는 날", description="\n\n".join(lines)[:4096], color=discord.Color.dark_red()))

    @app_commands.command(name="전역랭킹", description="서버 구성원들의 전역 예정 순위를 봅니다.")
    async def ranking(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        with session_scope() as session:
            profiles = list(session.scalars(select(MilitaryProfile).where(MilitaryProfile.guild_id == interaction.guild.id).order_by(MilitaryProfile.discharge_date)))
        if not profiles:
            await interaction.response.send_message(embed=discord.Embed(title="🏃 탈출 순서", description="등록된 군생활 프로필이 없습니다.", color=discord.Color.dark_red()))
            return
        reference = today()
        active = [profile for profile in profiles if profile.discharge_date >= reference]
        completed = [profile for profile in profiles if profile.discharge_date < reference]
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for index, profile in enumerate(active):
            member = interaction.guild.get_member(profile.discord_user_id)
            name = member.display_name if member else profile.display_name
            lines.append(f"{medals[index] if index < 3 else f'{index + 1}.'} **{name}**\n{d_day(profile.discharge_date, reference)} · {profile.discharge_date:%Y.%m.%d}")
        if completed:
            lines.append("\n**완전 탈출**\n" + "\n".join(f"🎉 {profile.display_name} · {profile.discharge_date:%Y.%m.%d}" for profile in completed))
        await interaction.response.send_message(embed=discord.Embed(title="🏃 탈출 순서", description="\n\n".join(lines), color=discord.Color.dark_red()))
