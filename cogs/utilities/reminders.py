import disnake
from disnake.ext import commands
import asyncio
from datetime import datetime

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}
        self.reminder_tasks = {}

    @commands.slash_command()
    async def remind(self, inter, time: int, *, message: str):
        """Установить напоминание (время в минутах)"""
        try:
            if time < 1 or time > 1440:
                return await inter.response.send_message(
                    "⚠️ Время должно быть от 1 до 1440 минут (24 часа)", 
                    ephemeral=True
                )

            reminder_id = len(self.reminders) + 1
            self.reminders[reminder_id] = {
                'user_id': inter.author.id,
                'channel_id': inter.channel.id,
                'message': message,
                'time': time,
                'created_at': datetime.now()
            }

            await inter.response.send_message(
                f"⏰ Напоминание #{reminder_id} установлено!\n"
                f"Сообщение: {message}\n"
                f"Время: через {time} минут",
                ephemeral=True
            )

            await asyncio.sleep(time * 60)
            
            await inter.channel.send(
                f"🔔 {inter.author.mention}, напоминаю (#{reminder_id}):\n{message}"
            )
            del self.reminders[reminder_id]

        except Exception:
            await inter.response.send_message(
                "❌ Произошла ошибка при установке напоминания", 
                ephemeral=True
            )

    @commands.slash_command()
    async def list_reminders(self, inter):
        """Показать список активных напоминаний"""
        user_reminders = {
            rid: rem for rid, rem in self.reminders.items() 
            if rem['user_id'] == inter.author.id
        }
        
        if not user_reminders:
            return await inter.response.send_message(
                "У вас нет активных напоминаний", 
                ephemeral=True
            )
        
        embed = disnake.Embed(title="📝 Ваши напоминания", color=disnake.Color.blue())
        for rid, rem in user_reminders.items():
            embed.add_field(
                name=f"Напоминание #{rid}",
                value=f"Через {rem['time']} мин: {rem['message']}",
                inline=False
            )
        
        await inter.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Reminders(bot))
