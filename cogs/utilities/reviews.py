import disnake
from disnake.ext import commands
import os
import asyncio
from datetime import datetime, timedelta

class Reviews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.main_channel_id = int(os.getenv('REVIEWS_MAIN_CHANNEL'))
        self.reviews_channel_id = int(os.getenv('REVIEWS_CHANNEL'))
        self.category_id = int(os.getenv('REVIEWS_CATEGORY'))
        self.active_review_channels = {}
        self.last_review_time = {}  # Словарь для хранения времени последнего отзыва
        self.cooldown_hours = 1     # Задержка в часах

    @commands.Cog.listener()
    async def on_ready(self):
        """Отправка стартового сообщения при запуске бота"""
        channel = self.bot.get_channel(self.main_channel_id)
        if channel:
            # Очищаем канал
            await channel.purge()
            
            embed = disnake.Embed(
                title="📝 Оставить отзыв",
                description=(
                    "Мы ценим ваше мнение! Нажмите на кнопку ниже, "
                    "чтобы оставить отзыв о нашем сервере.\n\n"
                    "Вы можете отправить текст, фото, видео или GIF."
                ),
                color=disnake.Color.blue()
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1234133960939012107/1353743109728637110/image.png?ex=67e2c304&is=67e17184&hm=616fc432d2a6ae8a629378156f621056e01e1f48e651a8dc79046a966adf98b4&=&format=webp&quality=lossless&width=1200&height=800")  # Замените на вашу картинку
            
            await channel.send(
                embed=embed,
                components=[
                    disnake.ui.Button(
                        style=disnake.ButtonStyle.primary,
                        label="Написать отзыв",
                        custom_id="create_review"
                    )
                ]
            )

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "create_review":
            # Проверяем время последнего отзыва
            last_time = self.last_review_time.get(inter.author.id)
            if last_time:
                time_passed = datetime.now() - last_time
                if time_passed < timedelta(hours=self.cooldown_hours):
                    time_left = timedelta(hours=self.cooldown_hours) - time_passed
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60
                    return await inter.response.send_message(
                        f"⏳ Вы сможете написать новый отзыв через "
                        f"{hours} ч. {minutes} мин.",
                        ephemeral=True
                    )

            # Проверяем, нет ли уже активного канала для отзыва у пользователя
            if inter.author.id in self.active_review_channels:
                return await inter.response.send_message(
                    "У вас уже есть активный канал для написания отзыва!",
                    ephemeral=True
                )

            # Создаём приватный канал для отзыва
            overwrites = {
                inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
                inter.author: disnake.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True
                )
            }

            review_channel = await inter.guild.create_text_channel(
                name=f"отзыв-{inter.author.name}",
                category=self.bot.get_channel(self.category_id),
                overwrites=overwrites
            )

            self.active_review_channels[inter.author.id] = review_channel.id

            # Отправляем инструкции в канал отзыва
            embed = disnake.Embed(
                title="✍️ Напишите ваш отзыв",
                description=(
                    "Просто отправьте ваш отзыв в этот канал.\n"
                    "Вы можете использовать текст, фото, видео или GIF.\n\n"
                    "Канал автоматически закроется после отправки отзыва.\n"
                    "Для отмены напишите 'отмена'"
                ),
                color=disnake.Color.green()
            )

            await review_channel.send(embed=embed)
            await inter.response.send_message(
                f"Канал для отзыва создан: {review_channel.mention}",
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # Проверяем, является ли канал каналом для отзыва
        if (message.channel.id in self.active_review_channels.values() and 
            not message.author.bot):
            
            if message.content.lower() == "отмена":
                await message.channel.delete()
                # Безопасно удаляем запись из словаря
                self.active_review_channels = {
                    k: v for k, v in self.active_review_channels.items() 
                    if v != message.channel.id
                }
                return

            # Сохраняем время отправки отзыва
            self.last_review_time[message.author.id] = datetime.now()

            # Создаём эмбед с отзывом
            embed = disnake.Embed(
                title=f"Новый отзыв от {message.author.display_name}",
                description=message.content or "_ _",
                color=disnake.Color.blue(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"ID: {message.author.id}")
            embed.set_thumbnail(url=message.author.display_avatar.url)

            # Получаем канал для отзывов
            reviews_channel = self.bot.get_channel(self.reviews_channel_id)

            # Отправляем отзыв с медиафайлами, если они есть
            files = []
            for attachment in message.attachments:
                files.append(await attachment.to_file())

            review_message = await reviews_channel.send(embed=embed, files=files)
            
            # Добавляем реакции для оценки отзыва
            await review_message.add_reaction("👍")
            await review_message.add_reaction("👎")

            # Отправляем благодарность и удаляем канал
            thank_embed = disnake.Embed(
                title="Спасибо за ваш отзыв! ❤️",
                description="Канал будет удален через 10 секунд.",
                color=disnake.Color.green()
            )
            await message.channel.send(embed=thank_embed)
            
            await asyncio.sleep(10)
            await message.channel.delete()
            # Безопасно удаляем запись из словаря
            self.active_review_channels = {
                k: v for k, v in self.active_review_channels.items() 
                if v != message.channel.id
            }

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.TextChannel):
        """Очищаем запись о канале при его удалении"""
        for user_id, channel_id in list(self.active_review_channels.items()):
            if channel_id == channel.id:
                del self.active_review_channels[user_id]
                break

def setup(bot):
    bot.add_cog(Reviews(bot))
