import disnake
from disnake.ext import commands
import os
from typing import Dict, Optional

class VoiceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channels: Dict[int, dict] = {}
        self.main_voice_id = int(os.getenv('VOICE_CHANNEL_ID'))

    async def get_or_create_control_channel(self, category: disnake.CategoryChannel) -> disnake.TextChannel:
        """Получить или создать канал управления"""
        control_channel = disnake.utils.get(category.text_channels, name="voice-control")
        
        if not control_channel:
            # Создаём канал для управления
            control_channel = await category.create_text_channel(
                name="voice-control",
                topic="Канал для управления голосовыми комнатами",
                position=0
            )
            # Скрываем канал от всех
            await control_channel.set_permissions(category.guild.default_role, read_messages=False)
            
        return control_channel

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if after.channel and after.channel.id == self.main_voice_id:
            # Создаём новый канал
            channel = await member.guild.create_voice_channel(
                name=f"🔊 Комната {member.display_name}",
                category=after.channel.category,
                user_limit=0
            )
            
            # Перемещаем пользователя
            await member.move_to(channel)
            
            # Создаём права для владельца канала
            await channel.set_permissions(member, 
                manage_channels=True, 
                mute_members=True, 
                deafen_members=True,
                view_channel=True,
                connect=True
            )
            
            # Скрываем канал от остальных по умолчанию
            await channel.set_permissions(channel.guild.default_role,
                view_channel=False,
                connect=False
            )
            
            # Создаём текстовый канал для управления
            text_channel = await channel.guild.create_text_channel(
                name=f"управление-{channel.name}",
                category=channel.category
            )
            
            # Настраиваем права для текстового канала
            await text_channel.set_permissions(member, 
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
            await text_channel.set_permissions(channel.guild.default_role,
                view_channel=False
            )
            
            # Создаём панель управления
            embed = await self.create_control_panel(member, channel)
            control_msg = await text_channel.send(
                embed=embed,
                components=self.get_control_buttons()
            )
            
            self.voice_channels[channel.id] = {
                "owner": member.id,
                "panel_msg": control_msg.id,
                "text_channel": text_channel.id
            }

        # Обновляем права при входе пользователя
        elif after.channel and after.channel.id in self.voice_channels:
            await after.channel.set_permissions(member, view_channel=True, connect=True)
            text_channel = self.bot.get_channel(self.voice_channels[after.channel.id]["text_channel"])
            if text_channel:
                await text_channel.set_permissions(member, view_channel=True, read_message_history=True)

        # Очищаем права при выходе
        if before.channel and before.channel.id in self.voice_channels:
            if member.id != self.voice_channels[before.channel.id]["owner"]:
                await before.channel.set_permissions(member, overwrite=None)
                text_channel = self.bot.get_channel(self.voice_channels[before.channel.id]["text_channel"])
                if text_channel:
                    await text_channel.set_permissions(member, overwrite=None)

            if len(before.channel.members) == 0:
                channel_info = self.voice_channels[before.channel.id]
                text_channel = self.bot.get_channel(channel_info["text_channel"])
                if text_channel:
                    await text_channel.delete()
                await before.channel.delete()
                del self.voice_channels[before.channel.id]

    def get_control_buttons(self):
        return [
            disnake.ui.Button(style=disnake.ButtonStyle.primary, label="Изменить название", custom_id="vc_rename", row=0),
            disnake.ui.Button(style=disnake.ButtonStyle.primary, label="Установить лимит", custom_id="vc_limit", row=0),
            disnake.ui.Button(style=disnake.ButtonStyle.danger, label="Замутить всех", custom_id="vc_muteall", row=1),
            disnake.ui.Button(style=disnake.ButtonStyle.success, label="Передать права", custom_id="vc_transfer", row=1),
            # Новые кнопки
            disnake.ui.Button(style=disnake.ButtonStyle.secondary, label="Скрыть канал", custom_id="vc_hide", row=2),
            disnake.ui.Button(style=disnake.ButtonStyle.secondary, label="Показать канал", custom_id="vc_unhide", row=2),
            disnake.ui.Button(style=disnake.ButtonStyle.danger, label="Кикнуть пользователя", custom_id="vc_kick", row=3),
        ]

    async def create_control_panel(self, owner: disnake.Member, channel: disnake.VoiceChannel) -> disnake.Embed:
        embed = disnake.Embed(
            title="🎮 Панель управления голосовым каналом",
            description=f"Владелец: {owner.mention}\nКанал: {channel.name}",
            color=disnake.Color.blue()
        )
        embed.add_field(
            name="Доступные действия:",
            value="• Изменить название канала\n"
                  "• Установить лимит пользователей\n"
                  "• Замутить всех пользователей\n"
                  "• Передать права другому пользователю\n"
                  "• Скрыть/Показать канал\n"
                  "• Кикнуть пользователя"
        )
        return embed

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith("vc_"):
            return

        if not inter.author.voice or inter.author.voice.channel.id not in self.voice_channels:
            return await inter.response.send_message(
                "❌ Вы должны находиться в голосовом канале!", 
                ephemeral=True
            )

        channel_info = self.voice_channels[inter.author.voice.channel.id]
        if channel_info["owner"] != inter.author.id:
            return await inter.response.send_message(
                "❌ У вас нет прав на управление этим каналом!", 
                ephemeral=True
            )

        if inter.component.custom_id == "vc_rename":
            await inter.response.send_modal(
                title="Переименование канала",
                custom_id="vc_rename_modal",
                components=[
                    disnake.ui.TextInput(
                        label="Новое название",
                        custom_id="new_name",
                        style=disnake.TextInputStyle.short,
                        max_length=32
                    )
                ]
            )

        elif inter.component.custom_id == "vc_limit":
            await inter.response.send_modal(
                title="Установка лимита",
                custom_id="vc_limit_modal",
                components=[
                    disnake.ui.TextInput(
                        label="Лимит пользователей (0-99)",
                        custom_id="user_limit",
                        style=disnake.TextInputStyle.short,
                        max_length=2
                    )
                ]
            )

        elif inter.component.custom_id == "vc_muteall":
            channel = inter.author.voice.channel
            for member in channel.members:
                if member.id != inter.author.id:
                    await member.edit(mute=True)
            await inter.response.send_message("Все пользователи замучены!", ephemeral=True)

        elif inter.component.custom_id == "vc_transfer":
            await inter.response.send_modal(
                title="Передача прав",
                custom_id="vc_transfer_modal",
                components=[
                    disnake.ui.TextInput(
                        label="ID пользователя",
                        custom_id="new_owner",
                        style=disnake.TextInputStyle.short,
                        max_length=20
                    )
                ]
            )

        elif inter.component.custom_id == "vc_hide":
            channel = inter.author.voice.channel
            await channel.set_permissions(channel.guild.default_role, view_channel=False, connect=False)
            await inter.response.send_message("Канал скрыт от других пользователей", ephemeral=True)

        elif inter.component.custom_id == "vc_unhide":
            channel = inter.author.voice.channel
            await channel.set_permissions(channel.guild.default_role, view_channel=True, connect=True)
            await inter.response.send_message("Канал теперь виден всем", ephemeral=True)

        elif inter.component.custom_id == "vc_kick":
            await inter.response.send_modal(
                title="Кик пользователя",
                custom_id="vc_kick_modal",
                components=[
                    disnake.ui.TextInput(
                        label="ID пользователя",
                        custom_id="user_id",
                        style=disnake.TextInputStyle.short,
                        max_length=20
                    )
                ]
            )

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if not inter.custom_id.startswith("vc_"):
            return

        channel = inter.author.voice.channel
        if not channel or channel.id not in self.voice_channels:
            return await inter.response.send_message(
                "Ошибка: канал не найден", 
                ephemeral=True
            )

        if inter.custom_id == "vc_rename_modal":
            new_name = inter.text_values["new_name"]
            await channel.edit(name=f"🔊 {new_name}")
            await inter.response.send_message(f"Канал переименован в: {new_name}", ephemeral=True)

        elif inter.custom_id == "vc_limit_modal":
            try:
                limit = int(inter.text_values["user_limit"])
                if 0 <= limit <= 99:
                    await channel.edit(user_limit=limit)
                    await inter.response.send_message(
                        f"Установлен лимит: {limit} пользователей", 
                        ephemeral=True
                    )
                else:
                    raise ValueError()
            except:
                await inter.response.send_message(
                    "Ошибка: введите число от 0 до 99", 
                    ephemeral=True
                )

        elif inter.custom_id == "vc_transfer_modal":
            try:
                new_owner_id = int(inter.text_values["new_owner"])
                new_owner = await self.bot.fetch_user(new_owner_id)
                if new_owner and new_owner in channel.members:
                    old_owner = inter.author
                    # Обновляем права
                    await channel.set_permissions(old_owner, overwrite=None)
                    await channel.set_permissions(
                        new_owner, 
                        manage_channels=True, 
                        mute_members=True, 
                        deafen_members=True
                    )
                    self.voice_channels[channel.id]["owner"] = new_owner_id
                    await inter.response.send_message(
                        f"Права переданы пользователю {new_owner.mention}", 
                        ephemeral=True
                    )
                else:
                    raise ValueError()
            except:
                await inter.response.send_message(
                    "Ошибка: пользователь не найден или не находится в канале", 
                    ephemeral=True
                )

        elif inter.custom_id == "vc_kick_modal":
            try:
                user_id = int(inter.text_values["user_id"])
                channel = inter.author.voice.channel
                member = channel.guild.get_member(user_id)
                channel_info = self.voice_channels[channel.id]
                
                if member and member in channel.members and member.id != channel_info["owner"]:
                    await member.move_to(None)
                    await channel.set_permissions(member, connect=False)
                    await inter.response.send_message(
                        f"Пользователь {member.mention} кикнут из канала", 
                        ephemeral=True
                    )
                else:
                    raise ValueError()
            except:
                await inter.response.send_message(
                    "Ошибка: пользователь не найден или не находится в канале",
                    ephemeral=True
                )

def setup(bot):
    bot.add_cog(VoiceManager(bot))
