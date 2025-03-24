import os
from dotenv import load_dotenv
import disnake
from disnake.ext import commands
import aiohttp

load_dotenv()

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    test_guilds=[int(os.getenv('GUILD_ID'))]
)

@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession()
    print(f"Бот {bot.user} готов к работе!")

@bot.event
async def on_shutdown():
    if hasattr(bot, 'session'):
        await bot.session.close()

# Загрузка когов
for folder in ['moderation', 'fun', 'info', 'levels', 'utilities']:
    for file in os.listdir(f"cogs/{folder}"):
        if file.endswith(".py"):
            bot.load_extension(f"cogs.{folder}.{file[:-3]}")

bot.run(os.getenv('DISCORD_TOKEN'))
