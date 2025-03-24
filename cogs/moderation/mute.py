import disnake
from disnake.ext import commands

class MuteCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @commands.has_permissions(moderate_members=True)
    async def mute(self, inter, member: disnake.Member, duration: int, *, reason=None):
        """Замутить участника (duration в минутах)"""
        await member.timeout(duration=duration*60, reason=reason)
        await inter.response.send_message(
            f"Участник {member.mention} замучен на {duration} минут. Причина: {reason}"
        )

    @commands.slash_command()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, inter, member: disnake.Member):
        """Размутить участника"""
        await member.timeout(duration=0)
        await inter.response.send_message(f"Участник {member.mention} размучен")

def setup(bot):
    bot.add_cog(MuteCommands(bot))
