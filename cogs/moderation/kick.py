import disnake
from disnake.ext import commands

class KickCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, inter, member: disnake.Member, *, reason=None):
        """Кикнуть участника"""
        await member.kick(reason=reason)
        await inter.response.send_message(f"Участник {member.mention} был кикнут. Причина: {reason}")

def setup(bot):
    bot.add_cog(KickCommand(bot))
