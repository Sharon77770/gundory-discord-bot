from datetime import date
from typing import Optional

import discord

from app.database.models import MilitaryEvent, MilitaryProfile
from app.services.event_service import type_label
from app.services.military_service import branch_label
from app.utils.dates import d_day, event_end

BRIAR = discord.Color.dark_red()


def error_embed(message: str) -> discord.Embed:
    return discord.Embed(title="❌ 처리할 수 없습니다", description=message, color=discord.Color.red())


def profile_embed(profile: MilitaryProfile, reference: date, next_leave: Optional[MilitaryEvent]) -> discord.Embed:
    elapsed = max(0, (reference - profile.enlistment_date).days)
    total = max(1, (profile.discharge_date - profile.enlistment_date).days)
    progress = max(0.0, min(100.0, elapsed / total * 100))
    filled = round(progress / 100 * 12)
    bar = "█" * filled + "░" * (12 - filled)
    embed = discord.Embed(title=f"🪖 {profile.display_name}의 군생활", color=BRIAR)
    embed.add_field(name="입대", value=profile.enlistment_date.strftime("%Y.%m.%d"), inline=True)
    embed.add_field(name="군종", value=branch_label(profile.service_branch), inline=True)
    embed.add_field(name="전역 예정", value=profile.discharge_date.strftime("%Y.%m.%d"), inline=True)
    embed.add_field(name="복무", value=d_day(profile.enlistment_date, reference), inline=True)
    embed.add_field(name="전역까지", value=d_day(profile.discharge_date, reference), inline=True)
    embed.add_field(name="복무율", value=f"{bar} {progress:.1f}%", inline=False)
    if next_leave:
        end = event_end(next_leave.start_date, next_leave.end_date)
        value = f"{next_leave.start_date:%Y.%m.%d} ~ {end:%Y.%m.%d}\n{d_day(next_leave.start_date, reference)} · {next_leave.title}"
    else:
        value = "등록된 다음 휴가가 없습니다."
    embed.add_field(name="다음 휴가", value=value, inline=False)
    return embed


def event_embed(event: MilitaryEvent, display_name: str, title: str = "일정 처리 완료") -> discord.Embed:
    end = event_end(event.start_date, event.end_date)
    date_text = event.start_date.strftime("%Y.%m.%d") if end == event.start_date else f"{event.start_date:%Y.%m.%d} ~ {end:%Y.%m.%d}"
    embed = discord.Embed(title=f"📅 {title}", color=BRIAR)
    embed.add_field(name="종류", value=type_label(event.event_type), inline=True)
    embed.add_field(name="제목", value=event.title, inline=True)
    embed.add_field(name="기간", value=date_text, inline=False)
    if event.memo:
        embed.add_field(name="메모", value=event.memo, inline=False)
    embed.set_footer(text=f"등록자: {display_name} · ID: {event.id}")
    return embed
