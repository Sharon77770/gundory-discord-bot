import asyncio

from app.bot.bot import BriarBot
from app.bot.cogs.calendar import CalendarCog
from app.bot.cogs.events import EventsCog
from app.bot.cogs.help import HelpCog
from app.bot.cogs.military import MilitaryCog
from app.bot.cogs.settings import SettingsCog
from app.bot.cogs.special import SpecialCog
from app.config import Settings


def test_all_cogs_register_without_duplicate_commands():
    async def register():
        bot = BriarBot(Settings("token", 1, "sqlite:///:memory:", "Asia/Seoul", "INFO", None))
        for cog in (MilitaryCog, EventsCog, CalendarCog, SpecialCog, SettingsCog, HelpCog):
            await bot.add_cog(cog(bot))
        return {command.name for command in bot.tree.get_commands()}

    commands = asyncio.run(register())
    assert {"군생활", "설정", "일정", "캘린더", "겹치는휴가", "도움"}.issubset(commands)
    # Group subcommands are the public UX: /일정 등록, /일정 목록, ...
    async def register_and_read():
        bot = BriarBot(Settings("token", 1, "sqlite:///:memory:", "Asia/Seoul", "INFO", None))
        await bot.add_cog(EventsCog(bot))
        group = bot.tree.get_command("일정")
        return {command.name for command in group.commands}

    assert {"등록", "목록", "수정", "삭제"}.issubset(asyncio.run(register_and_read()))
