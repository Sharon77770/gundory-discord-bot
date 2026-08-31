import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="도움", description="봇 사용법과 개발자 연락처를 확인합니다.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🪖 브라이어 봇 도움말",
            description="군생활 일정과 휴가를 서버 구성원들과 함께 관리하는 봇입니다.",
            color=discord.Color.dark_red(),
        )
        embed.add_field(
            name="시작하기",
            value="1. `/군생활 등록`으로 입대일과 군종을 등록합니다.\n"
            "2. `/일정 등록`으로 휴가·외출·외박 일정을 추가합니다.\n"
            "3. `/캘린더` 또는 `/이번주`로 모두의 일정을 확인합니다.",
            inline=False,
        )
        embed.add_field(
            name="내 군생활 · 일정",
            value="`/군생활 등록` · `/군생활 정보`\n"
            "`/일정 등록` · `/일정 목록` · `/일정 수정` · `/일정 삭제`",
            inline=False,
        )
        embed.add_field(
            name="함께 보기",
            value="`/캘린더` · `/이번주` · `/다음휴가` · `/겹치는휴가` · `/전역랭킹`",
            inline=False,
        )
        embed.add_field(
            name="관리자 설정",
            value="`/설정 알림채널` · `/설정 알림켜기` · `/설정 알림끄기`\n"
            "자동 알림은 서버 관리자만 설정할 수 있습니다.",
            inline=False,
        )
        embed.add_field(
            name="개발자 연락처",
            value="Instagram: [@sharon77770](https://www.instagram.com/sharon77770/)",
            inline=False,
        )
        embed.set_footer(text="날짜는 YYYY-MM-DD 형식으로 입력해 주세요. · 기본 시간대: Asia/Seoul")
        await interaction.response.send_message(embed=embed)
