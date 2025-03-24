import disnake
from disnake.ext import commands
from datetime import datetime

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def userinfo(self, inter, member: disnake.Member = None):
        """Показать информацию о пользователе"""
        await inter.response.defer()
        
        member = member or inter.author
        roles = [role.mention for role in member.roles[1:]]
        
        embed = disnake.Embed(color=member.color, timestamp=datetime.now())
        # Убираем #0 из отображения имени
        display_name = member.name if member.discriminator == "0" else f"{member.name}#{member.discriminator}"
        embed.set_author(name=f"Информация о {display_name}", icon_url=member.display_avatar)
        embed.set_thumbnail(url=member.display_avatar)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Никнейм", value=member.display_name)
        embed.add_field(name="Аккаунт создан", value=member.created_at.strftime("%d.%m.%Y"))
        embed.add_field(name="Присоединился", value=member.joined_at.strftime("%d.%m.%Y"))
        embed.add_field(name=f"Роли ({len(roles)})", value=" ".join(roles) or "Нет ролей")
        
        await inter.edit_original_response(embed=embed)

    @commands.slash_command()
    async def avatar(self, inter, member: disnake.Member = None):
        """Показать аватар пользователя"""
        await inter.response.defer()
        
        member = member or inter.author
        embed = disnake.Embed(title=f"Аватар {member.display_name}", color=member.color)
        embed.set_image(url=member.display_avatar.url)
        
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(UserInfo(bot))
