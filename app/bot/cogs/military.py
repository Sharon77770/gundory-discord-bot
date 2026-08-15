import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from app.database.database import session_scope
from app.services.military_service import SERVICE_BRANCHES, estimated_discharge_date, get_profile, next_leave_for_user, upsert_profile
from app.utils.dates import parse_date, today, validate_range
from app.utils.embeds import error_embed, profile_embed

logger = logging.getLogger("briar.commands.military")
BRANCH_CHOICES = [
    app_commands.Choice(name=f"{label} ({months}개월)" if months else label, value=code)
    for code, (label, months) in SERVICE_BRANCHES.items()
]


class MilitaryCog(commands.Cog):
    military = app_commands.Group(name="군생활", description="군생활 프로필 명령어")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @military.command(name="등록", description="군종을 선택하고 군생활 프로필을 등록합니다.")
    @app_commands.describe(입대일="YYYY-MM-DD", 군종="군종을 선택하면 전역일을 자동 계산합니다.", 전역예정일="기타 군종이거나 실제 전역일을 알고 있으면 직접 입력 (선택)")
    @app_commands.choices(군종=BRANCH_CHOICES)
    async def register(self, interaction: discord.Interaction, 입대일: str, 군종: app_commands.Choice[str], 전역예정일: Optional[str] = None):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        try:
            enlistment = parse_date(입대일)
            discharge = parse_date(전역예정일) if 전역예정일 else estimated_discharge_date(enlistment, 군종.value)
            validate_range(enlistment, discharge)
            if enlistment == discharge:
                raise ValueError("입대일과 전역예정일은 같은 날일 수 없습니다.")
            with session_scope() as session:
                profile = upsert_profile(session, interaction.guild.id, interaction.user.id, interaction.user.display_name, enlistment, discharge, 군종.value)
            await interaction.response.send_message(embed=profile_embed(profile, today(), None))
            logger.info("profile upserted guild=%s user=%s", interaction.guild.id, interaction.user.id)
        except ValueError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @military.command(name="정보", description="군생활 정보를 확인합니다.")
    @app_commands.describe(사용자="확인할 서버 구성원 (생략하면 본인)")
    async def info(self, interaction: discord.Interaction, 사용자: Optional[discord.Member] = None):
        if not interaction.guild:
            await interaction.response.send_message(embed=error_embed("서버 안에서만 사용할 수 있습니다."), ephemeral=True)
            return
        target = 사용자 or interaction.user
        with session_scope() as session:
            profile = get_profile(session, interaction.guild.id, target.id)
            if profile:
                profile.display_name = target.display_name
            next_leave = next_leave_for_user(session, interaction.guild.id, target.id, today()) if profile else None
        if not profile:
            await interaction.response.send_message(embed=error_embed(f"{target.display_name}님의 군생활 프로필이 등록되지 않았습니다."), ephemeral=True)
            return
        await interaction.response.send_message(embed=profile_embed(profile, today(), next_leave))
