import disnake
from disnake.ext import commands

class PollCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def poll(self, inter, question: str, option1: str, option2: str):
        """Создать опрос с двумя вариантами ответа"""
        embed = disnake.Embed(title="📊 Опрос", description=question, color=disnake.Color.blue())
        embed.add_field(name="1️⃣", value=option1, inline=True)
        embed.add_field(name="2️⃣", value=option2, inline=True)
        
        message = await inter.channel.send(embed=embed)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await inter.response.send_message("Опрос создан!", ephemeral=True)

def setup(bot):
    bot.add_cog(PollCommands(bot))
