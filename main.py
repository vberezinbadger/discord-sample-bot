import os
from dotenv import load_dotenv
import disnake
from disnake.ext import commands
import json
from urllib.parse import urlparse
import aiohttp
import asyncio
from datetime import datetime
import random

# Загрузка переменных окружения
load_dotenv()

# Настройка интентов
intents = disnake.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# Инициализация бота
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    test_guilds=[int(os.getenv('GUILD_ID'))]  # Замените на ID вашего сервера
)

# Загрузка предупреждений
warnings = {}
try:
    with open('warnings.json', 'r') as f:
        warnings = json.load(f)
except FileNotFoundError:
    pass

# Система уровней
levels = {}
try:
    with open('levels.json', 'r') as f:
        levels = json.load(f)
except FileNotFoundError:
    pass

# Создаем сессию aiohttp при запуске бота
@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession()
    print(f"Бот {bot.user} готов к работе!")

# Закрываем сессию при выключении
@bot.event
async def on_shutdown():
    if hasattr(bot, 'session'):
        await bot.session.close()

# Команды модерации
@bot.slash_command()
@commands.has_permissions(kick_members=True)
async def kick(inter, member: disnake.Member, *, reason=None):
    """Кикнуть участника"""
    await member.kick(reason=reason)
    await inter.response.send_message(f"Участник {member.mention} был кикнут. Причина: {reason}")

@bot.slash_command()
@commands.has_permissions(ban_members=True)
async def ban(inter, member: disnake.Member, *, reason=None):
    """Забанить участника"""
    await member.ban(reason=reason)
    await inter.response.send_message(f"Участник {member.mention} был забанен. Причина: {reason}")

@bot.slash_command()
@commands.has_permissions(ban_members=True)
async def unban(inter, user_id: str):
    """Разбанить участника по ID"""
    try:
        user = await bot.fetch_user(int(user_id))
        await inter.guild.unban(user)
        await inter.response.send_message(f"Участник {user.mention} разбанен")
    except:
        await inter.response.send_message("Ошибка при разбане пользователя")

@bot.slash_command()
@commands.has_permissions(moderate_members=True)
async def mute(inter, member: disnake.Member, duration: int, *, reason=None):
    """Замутить участника (duration в минутах)"""
    await member.timeout(duration=duration*60, reason=reason)
    await inter.response.send_message(f"Участник {member.mention} замучен на {duration} минут. Причина: {reason}")

@bot.slash_command()
@commands.has_permissions(moderate_members=True)
async def unmute(inter, member: disnake.Member):
    """Размутить участника"""
    await member.timeout(duration=0)
    await inter.response.send_message(f"Участник {member.mention} размучен")

# Система предупреждений
@bot.slash_command()
@commands.has_permissions(moderate_members=True)
async def warn(inter, member: disnake.Member, *, reason=None):
    """Выдать предупреждение участнику"""
    guild_id = str(inter.guild.id)
    member_id = str(member.id)
    
    if guild_id not in warnings:
        warnings[guild_id] = {}
    
    if member_id not in warnings[guild_id]:
        warnings[guild_id][member_id] = []
    
    warnings[guild_id][member_id].append(reason or "Причина не указана")
    
    # Сохранение предупреждений
    with open('warnings.json', 'w') as f:
        json.dump(warnings, f)
    
    warn_count = len(warnings[guild_id][member_id])
    await inter.response.send_message(f"Участник {member.mention} получил предупреждение ({warn_count}/3). Причина: {reason}")
    
    if warn_count >= 3:
        await member.kick(reason="Превышен лимит предупреждений")
        await inter.channel.send(f"Участник {member.mention} был кикнут за превышение лимита предупреждений")
        warnings[guild_id][member_id] = []

@bot.slash_command()
@commands.has_permissions(moderate_members=True)
async def clear_warnings(inter, member: disnake.Member):
    """Очистить все предупреждения участника"""
    guild_id = str(inter.guild.id)
    member_id = str(member.id)
    
    if guild_id in warnings and member_id in warnings[guild_id]:
        warnings[guild_id][member_id] = []
        with open('warnings.json', 'w') as f:
            json.dump(warnings, f)
        await inter.response.send_message(f"Все предупреждения участника {member.mention} очищены")
    else:
        await inter.response.send_message(f"У участника {member.mention} нет предупреждений")

# Изменяем broadcast команду
@bot.slash_command()
@commands.has_permissions(administrator=True)
async def broadcast(inter, *, message: str):
    """Отправить сообщение от имени бота"""
    await inter.response.defer(ephemeral=True)
    await inter.channel.send(message)
    await inter.edit_original_response(content="Сообщение отправлено")

@bot.slash_command()
async def clear(inter, amount: int):
    """Очистить указанное количество сообщений"""
    if not inter.author.guild_permissions.manage_messages:
        return await inter.response.send_message("У вас нет прав для использования этой команды!", ephemeral=True)
    
    await inter.response.defer(ephemeral=True)
    deleted = await inter.channel.purge(limit=amount)
    await inter.edit_original_response(content=f"Удалено {len(deleted)} сообщений")

@bot.slash_command()
async def poll(inter, question: str, option1: str, option2: str):
    """Создать опрос с двумя вариантами ответа"""
    await inter.response.defer()
    
    embed = disnake.Embed(title="📊 Опрос", description=question, color=disnake.Color.blue())
    embed.add_field(name="1️⃣", value=option1, inline=True)
    embed.add_field(name="2️⃣", value=option2, inline=True)
    
    message = await inter.edit_original_response(embed=embed)
    await message.add_reaction("1️⃣")
    await message.add_reaction("2️⃣")

@bot.slash_command()
async def userinfo(inter, member: disnake.Member = None):
    """Показать информацию о пользователе"""
    member = member or inter.author
    
    roles = [role.mention for role in member.roles[1:]]
    embed = disnake.Embed(color=member.color, timestamp=datetime.now())
    embed.set_author(name=f"Информация о {member}", icon_url=member.display_avatar)
    embed.set_thumbnail(url=member.display_avatar)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Никнейм", value=member.display_name)
    embed.add_field(name="Аккаунт создан", value=member.created_at.strftime("%d.%m.%Y"))
    embed.add_field(name="Присоединился", value=member.joined_at.strftime("%d.%m.%Y"))
    embed.add_field(name=f"Роли ({len(roles)})", value=" ".join(roles) or "Нет ролей")
    
    await inter.response.send_message(embed=embed)

@bot.slash_command()
async def serverinfo(inter):
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

@bot.slash_command()
async def random_number(inter, min_value: int = 1, max_value: int = 100):
    """Сгенерировать случайное число"""
    number = random.randint(min_value, max_value)
    await inter.response.send_message(f"🎲 Случайное число: **{number}**")

@bot.slash_command()
async def coin(inter):
    """Подбросить монетку"""
    result = random.choice(["Орёл", "Решка"])
    await inter.response.send_message(f"🪙 {result}!")

@bot.slash_command()
async def weather(inter, city: str):
    """Показать погоду в городе (демо)"""
    await inter.response.send_message(f"🌤️ Погода в городе {city}: +20°C, солнечно\n(Это демо-версия команды)")

# Система напоминаний
reminders = {}

@bot.slash_command()
async def remind(inter, time: int, *, message: str):
    """Установить напоминание (время в минутах)"""
    try:
        if time < 1 or time > 1440:
            await inter.response.send_message(
                "⚠️ Время должно быть от 1 до 1440 минут (24 часа)", 
                ephemeral=True
            )
            return

        reminder_id = len(reminders) + 1
        reminders[reminder_id] = {
            'user_id': inter.author.id,
            'channel_id': inter.channel.id,
            'message': message,
            'time': time,
            'created_at': datetime.now()
        }

        # Отправляем сообщение сразу
        await inter.response.send_message(
            f"⏰ Напоминание #{reminder_id} установлено!\n"
            f"Сообщение: {message}\n"
            f"Время: через {time} минут",
            ephemeral=True
        )

        # Запускаем задачу напоминания
        await asyncio.sleep(time * 60)
        
        try:
            await inter.channel.send(
                f"🔔 {inter.author.mention}, напоминаю (#{reminder_id}):\n{message}"
            )
        finally:
            if reminder_id in reminders:
                del reminders[reminder_id]

    except Exception as e:
        try:
            await inter.response.send_message(
                "❌ Произошла ошибка при установке напоминания", 
                ephemeral=True
            )
        except:
            pass

@bot.slash_command()
async def cancel_reminder(inter, reminder_id: int):
    """Отменить напоминание по ID"""
    if reminder_id not in reminders or reminders[reminder_id]['user_id'] != inter.author.id:
        return await inter.response.send_message("❌ Напоминание не найдено", ephemeral=True)
    
    if reminder_id in reminder_tasks:
        reminder_tasks[reminder_id].cancel()
        del reminders[reminder_id]
        del reminder_tasks[reminder_id]
        
    await inter.response.send_message(f"✅ Напоминание #{reminder_id} отменено", ephemeral=True)

@bot.slash_command()
async def list_reminders(inter):
    """Показать список активных напоминаний"""
    user_reminders = {
        rid: rem for rid, rem in reminders.items() 
        if rem['user_id'] == inter.author.id
    }
    
    if not user_reminders:
        await inter.response.send_message("У вас нет активных напоминаний", ephemeral=True)
        return
    
    embed = disnake.Embed(title="📝 Ваши напоминания", color=disnake.Color.blue())
    for rid, rem in user_reminders.items():
        embed.add_field(
            name=f"Напоминание #{rid}",
            value=f"Через {rem['time']} мин: {rem['message']}",
            inline=False
        )
    
    await inter.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command()
async def roll(inter, dice: str = "1d6"):
    """Бросить кости (формат: NdM, где N - количество костей, M - число граней)"""
    await inter.response.defer()
    
    try:
        if 'd' not in dice:
            raise ValueError("Неверный формат")
            
        count, sides = map(int, dice.lower().split('d'))
        if count < 1 or sides < 2 or count > 100 or sides > 100:
            raise ValueError("Недопустимые значения")
        
        results = [random.randint(1, sides) for _ in range(count)]
        total = sum(results)
        
        await inter.edit_original_response(
            content=f"🎲 Результаты броска {dice}:\n"
                   f"Броски: {', '.join(map(str, results))}\n"
                   f"Сумма: {total}"
        )
    except ValueError as e:
        await inter.edit_original_response(
            content="❌ Ошибка: используйте формат NdM (например: 2d6), где:\n"
                   "N - количество костей (1-100)\n"
                   "M - число граней (2-100)"
        )

@bot.slash_command()
async def avatar(inter, member: disnake.Member = None):
    """Показать аватар пользователя"""
    member = member or inter.author
    embed = disnake.Embed(title=f"Аватар {member.display_name}", color=member.color)
    embed.set_image(url=member.display_avatar.url)
    await inter.response.send_message(embed=embed)

@bot.slash_command()
async def servericon(inter):
    """Показать иконку сервера"""
    if not inter.guild.icon:
        return await inter.response.send_message("У сервера нет иконки!", ephemeral=True)
    
    embed = disnake.Embed(title=f"Иконка сервера {inter.guild.name}", color=disnake.Color.blue())
    embed.set_image(url=inter.guild.icon.url)
    await inter.response.send_message(embed=embed)

@bot.slash_command()
async def say(inter, *, text: str):
    """Сказать что-то от имени бота"""
    await inter.response.send_message("Сообщение отправлено!", ephemeral=True)
    await inter.channel.send(f'💬 {text}')

@bot.slash_command()
async def emoji_info(inter, emoji: str):
    """Показать информацию об эмодзи"""
    try:
        custom_emoji = await commands.EmojiConverter().convert(inter, emoji)
        embed = disnake.Embed(title="Информация об эмодзи", color=disnake.Color.blue())
        embed.add_field(name="Название", value=custom_emoji.name)
        embed.add_field(name="ID", value=custom_emoji.id)
        embed.add_field(name="Анимированный", value="Да" if custom_emoji.animated else "Нет")
        embed.set_thumbnail(url=custom_emoji.url)
        await inter.response.send_message(embed=embed)
    except:
        await inter.response.send_message("Это не кастомный эмодзи или я не могу получить информацию о нём", ephemeral=True)

@bot.slash_command()
async def members(inter):
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

# Оптимизируем анализ ссылок
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)
    
    # Поиск ссылок в сообщении
    words = message.content.split()
    for word in words:
        try:
            result = urlparse(word)
            if result.scheme and result.netloc:
                async with bot.session.get(word, timeout=5) as response:
                    info = f"Информация о ссылке:\n"
                    info += f"Домен: {result.netloc}\n"
                    info += f"Протокол: {result.scheme}\n"
                    info += f"Код ответа: {response.status}\n"
                    info += f"Тип контента: {response.headers.get('content-type', 'Неизвестно')}"
                    
                    await message.reply(info)
                    break
        except:
            continue

    # Система уровней
    guild_id = str(message.guild.id)
    user_id = str(message.author.id)
    
    if guild_id not in levels:
        levels[guild_id] = {}
    
    if user_id not in levels[guild_id]:
        levels[guild_id][user_id] = {"xp": 0, "level": 1}
    
    levels[guild_id][user_id]["xp"] += random.randint(15, 25)
    xp = levels[guild_id][user_id]["xp"]
    lvl = levels[guild_id][user_id]["level"]
    
    xp_required = (lvl * 100)
    
    if xp >= xp_required:
        levels[guild_id][user_id]["level"] += 1
        levels[guild_id][user_id]["xp"] = 0
        await message.channel.send(f"🎉 Поздравляем {message.author.mention}! Вы достигли {lvl + 1} уровня!")
    
    with open('levels.json', 'w') as f:
        json.dump(levels, f)

@bot.slash_command()
async def rank(inter, member: disnake.Member = None):
    """Показать ранг пользователя"""
    member = member or inter.author
    guild_id = str(inter.guild.id)
    user_id = str(member.id)
    
    if guild_id not in levels or user_id not in levels[guild_id]:
        return await inter.response.send_message("У пользователя пока нет ранга!", ephemeral=True)
    
    level = levels[guild_id][user_id]["level"]
    xp = levels[guild_id][user_id]["xp"]
    xp_required = (level * 100)
    
    embed = disnake.Embed(title=f"Ранг {member.display_name}", color=member.color)
    embed.add_field(name="Уровень", value=level)
    embed.add_field(name="XP", value=f"{xp}/{xp_required}")
    embed.set_thumbnail(url=member.display_avatar)
    
    await inter.response.send_message(embed=embed)

# Запуск бота
bot.run(os.getenv('DISCORD_TOKEN'))
