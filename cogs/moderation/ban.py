import disnake
from disnake.ext import commands

class BanCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, inter, member: disnake.Member, *, reason=None):
        """Забанить участника"""
        await member.ban(reason=reason)
        await inter.response.send_message(f"Участник {member.mention} был забанен. Причина: {reason}")

    @commands.slash_command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, inter, user_id: str):
        """Разбанить участника по ID"""
        try:
            user = await self.bot.fetch_user(int(user_id))
            await inter.guild.unban(user)
            await inter.response.send_message(f"Участник {user.mention} разбанен")
        except:
            await inter.response.send_message("Ошибка при разбане пользователя")

def setup(bot):
    bot.add_cog(BanCommands(bot))
