import logging

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.cogs.calendar import CalendarCog
from app.bot.cogs.events import EventsCog
from app.bot.cogs.help import HelpCog
from app.bot.cogs.military import MilitaryCog
from app.bot.cogs.settings import SettingsCog
from app.bot.cogs.special import SpecialCog
from app.config import Settings
from app.scheduler.scheduler import BriarScheduler

logger = logging.getLogger("briar.bot")


class BriarBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.none()
        # Required for guild-scoped slash-command sync and member/channel lookup.
        # Message Content and other privileged intents remain disabled.
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents, application_id=settings.application_id or None)
        self.settings = settings
        self.briar_scheduler = BriarScheduler(self, settings.timezone)

    async def setup_hook(self) -> None:
        await self.add_cog(MilitaryCog(self))
        await self.add_cog(EventsCog(self))
        await self.add_cog(CalendarCog(self))
        await self.add_cog(SpecialCog(self))
        await self.add_cog(SettingsCog(self))
        await self.add_cog(HelpCog(self))
        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("synced %s commands to development guild=%s", len(synced), self.settings.dev_guild_id)
        else:
            synced = await self.tree.sync()
            logger.info("synced %s global commands", len(synced))
        self.briar_scheduler.start()

    async def on_ready(self) -> None:
        logger.info("Briar Bot ready user=%s guilds=%s", self.user, len(self.guilds))

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        logger.exception("discord event error event=%s", event_method)
