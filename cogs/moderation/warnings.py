import disnake
from disnake.ext import commands
import json

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}
        self.load_warnings()

    def load_warnings(self):
        try:
            with open('warnings.json', 'r') as f:
                self.warnings = json.load(f)
        except FileNotFoundError:
            pass

    def save_warnings(self):
        with open('warnings.json', 'w') as f:
            json.dump(self.warnings, f)

    @commands.slash_command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, inter, member: disnake.Member, *, reason=None):
        """Выдать предупреждение участнику"""
        guild_id = str(inter.guild.id)
        member_id = str(member.id)
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        
        if member_id not in self.warnings[guild_id]:
            self.warnings[guild_id][member_id] = []
        
        self.warnings[guild_id][member_id].append(reason or "Причина не указана")
        self.save_warnings()
        
        warn_count = len(self.warnings[guild_id][member_id])
        await inter.response.send_message(
            f"Участник {member.mention} получил предупреждение ({warn_count}/3). Причина: {reason}"
        )
        
        if warn_count >= 3:
            await member.kick(reason="Превышен лимит предупреждений")
            await inter.channel.send(
                f"Участник {member.mention} был кикнут за превышение лимита предупреждений"
            )
            self.warnings[guild_id][member_id] = []
            self.save_warnings()

    @commands.slash_command()
    @commands.has_permissions(moderate_members=True)
    async def clear_warnings(self, inter, member: disnake.Member):
        """Очистить все предупреждения участника"""
        guild_id = str(inter.guild.id)
        member_id = str(member.id)
        
        if guild_id in self.warnings and member_id in self.warnings[guild_id]:
            self.warnings[guild_id][member_id] = []
            self.save_warnings()
            await inter.response.send_message(f"Все предупреждения участника {member.mention} очищены")
        else:
            await inter.response.send_message(f"У участника {member.mention} нет предупреждений")

def setup(bot):
    bot.add_cog(Warnings(bot))
