from datetime import date, datetime
import logging
from typing import Any
from zoneinfo import ZoneInfo

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.database import session_scope
from app.database.models import MilitaryEvent, MilitaryProfile
from app.services.notification_service import claim_notification, due_notifications, settings_for
from app.utils.dates import event_end, today

logger = logging.getLogger("briar.scheduler")


class BriarScheduler:
    def __init__(self, bot: discord.Client, timezone_name: str = "Asia/Seoul"):
        self.bot = bot
        self.timezone_name = timezone_name
        self.scheduler = AsyncIOScheduler(timezone=ZoneInfo(timezone_name))

    def start(self) -> None:
        self.scheduler.add_job(self.run_daily, "cron", hour=9, minute=0, id="daily-notifications", replace_existing=True)
        self.scheduler.start()
        logger.info("scheduler started")

    async def run_daily(self) -> None:
        target = datetime.now(ZoneInfo(self.timezone_name)).date()
        with session_scope() as session:
            due = due_notifications(session, target)
        for kind, subject, profile in due:
            event = subject if isinstance(subject, MilitaryEvent) else None
            guild_id = event.guild_id if event else profile.guild_id
            event_id = event.id if event else profile.id
            with session_scope() as session:
                settings = settings_for(session, guild_id)
                if not settings or not settings.notification_enabled or not settings.notification_channel_id:
                    continue
                if not claim_notification(session, guild_id, event_id, kind, target):
                    continue
                channel_id = settings.notification_channel_id
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except discord.DiscordException:
                    logger.exception("notification channel unavailable guild=%s channel=%s", guild_id, channel_id)
                    continue
            try:
                await channel.send(embed=self._embed(kind, subject, profile))
            except discord.DiscordException:
                logger.exception("notification failed guild=%s channel=%s kind=%s", guild_id, channel_id, kind)

    @staticmethod
    def _embed(kind: str, subject: Any, profile: MilitaryProfile) -> discord.Embed:
        if isinstance(subject, MilitaryEvent):
            end = event_end(subject.start_date, subject.end_date)
            period = f"{subject.start_date:%Y.%m.%d} ~ {end:%Y.%m.%d}"
            name = profile.display_name if profile else "알 수 없는 사용자"
            if kind == "leave_eve":
                title, description = "🩸 브라이어가 냄새를 맡았습니다!", f"{name}님이 내일 부대에서 탈출합니다."
            elif kind == "leave_start":
                title, description = "🔓 탈출 성공", f"{name}님의 휴가가 오늘 시작되었습니다."
            else:
                title, description = "⛓️ 탈출 종료", f"{name}님의 휴가가 오늘 끝납니다.\n내일부터 다시 군인입니다."
            embed = discord.Embed(title=title, description=description, color=discord.Color.dark_red())
            embed.add_field(name="일정", value=f"{period}\n{subject.title}")
            return embed
        return discord.Embed(title="🎉 탈출 성공", description=f"{profile.display_name}님이 오늘 전역했습니다.\n\n{profile.enlistment_date:%Y.%m.%d} → {profile.discharge_date:%Y.%m.%d}", color=discord.Color.gold())

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("scheduler stopped")
