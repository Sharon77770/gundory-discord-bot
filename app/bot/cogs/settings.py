import discord
from discord import app_commands
from discord.ext import commands

from app.database.database import session_scope
from app.services.notification_service import save_channel, set_enabled, settings_for
from app.utils.embeds import error_embed


class SettingsCog(commands.Cog):
    settings = app_commands.Group(name="설정", description="Briar Bot 서버 설정")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_manage_guild(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=error_embed("서버 관리 권한이 필요합니다."), ephemeral=True)
            return False
        return True

    @settings.command(name="알림채널", description="현재 채널을 자동 알림 채널로 설정합니다.")
    async def notification_channel(self, interaction: discord.Interaction):
        if not await self._require_manage_guild(interaction):
            return
        with session_scope() as session:
            save_channel(session, interaction.guild.id, interaction.channel_id)
        await interaction.response.send_message(embed=discord.Embed(title="🔔 알림 채널 설정 완료", description=f"이 채널(<#{interaction.channel_id}>)로 알림을 보냅니다.", color=discord.Color.dark_red()))

    @settings.command(name="알림켜기", description="자동 알림을 켭니다.")
    async def notification_on(self, interaction: discord.Interaction):
        if not await self._require_manage_guild(interaction):
            return
        with session_scope() as session:
            set_enabled(session, interaction.guild.id, True)
        await interaction.response.send_message("✅ 자동 알림을 켰습니다.", ephemeral=True)

    @settings.command(name="알림끄기", description="자동 알림을 끕니다.")
    async def notification_off(self, interaction: discord.Interaction):
        if not await self._require_manage_guild(interaction):
            return
        with session_scope() as session:
            set_enabled(session, interaction.guild.id, False)
        await interaction.response.send_message("✅ 자동 알림을 껐습니다.", ephemeral=True)
