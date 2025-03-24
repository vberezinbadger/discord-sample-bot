import disnake
from disnake.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def serverinfo(self, inter):
        """Показать информацию о сервере"""
        guild = inter.guild
        embed = disnake.Embed(title=f"Информация о {guild.name}", color=disnake.Color.blue())
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="Владелец", value=guild.owner.mention)
        embed.add_field(name="Участников", value=guild.member_count)
        embed.add_field(name="Создан", value=guild.created_at.strftime("%d.%m.%Y"))
        embed.add_field(name="Каналов", value=len(guild.channels))
        embed.add_field(name="Ролей", value=len(guild.roles))
        
        await inter.response.send_message(embed=embed)

    @commands.slash_command()
    async def members(self, inter):
        """Показать статистику участников сервера"""
        guild = inter.guild
        total = guild.member_count
        online = len([m for m in guild.members if m.status != disnake.Status.offline])
        bots = len([m for m in guild.members if m.bot])
        
        embed = disnake.Embed(title="📊 Статистика участников", color=disnake.Color.blue())
        embed.add_field(name="Всего", value=total)
        embed.add_field(name="Онлайн", value=online)
        embed.add_field(name="Ботов", value=bots)
        
        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(ServerInfo(bot))
