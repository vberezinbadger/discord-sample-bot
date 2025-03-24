import disnake
from disnake.ext import commands
import random

class RandomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def random_number(self, inter, min_value: int = 1, max_value: int = 100):
        """Сгенерировать случайное число"""
        number = random.randint(min_value, max_value)
        await inter.response.send_message(f"🎲 Случайное число: **{number}**")

    @commands.slash_command()
    async def say(self, inter, *, text: str):
        """Сказать что-то от имени бота"""
        await inter.response.send_message("Сообщение отправлено!", ephemeral=True)
        await inter.channel.send(f'💬 {text}')

def setup(bot):
    bot.add_cog(RandomCommands(bot))
