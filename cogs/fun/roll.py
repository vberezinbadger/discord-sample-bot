import disnake
from disnake.ext import commands
import random

class DiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def roll(self, inter, dice: str = "1d6"):
        """Бросить кости (формат: NdM, где N - количество костей, M - число граней)"""
        try:
            if 'd' not in dice:
                raise ValueError("Неверный формат")
                
            count, sides = map(int, dice.lower().split('d'))
            if count < 1 or sides < 2 or count > 100 or sides > 100:
                raise ValueError("Недопустимые значения")
            
            results = [random.randint(1, sides) for _ in range(count)]
            total = sum(results)
            
            await inter.response.send_message(
                f"🎲 Результаты броска {dice}:\n"
                f"Броски: {', '.join(map(str, results))}\n"
                f"Сумма: {total}"
            )
        except ValueError:
            await inter.response.send_message(
                "❌ Ошибка: используйте формат NdM (например: 2d6)"
            )

    @commands.slash_command()
    async def coin(self, inter):
        """Подбросить монетку"""
        result = random.choice(["Орёл", "Решка"])
        await inter.response.send_message(f"🪙 {result}!")

def setup(bot):
    bot.add_cog(DiceCommands(bot))
