import disnake
from disnake.ext import commands
import json
import random

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels = {}
        self.load_levels()

    def load_levels(self):
        try:
            with open('levels.json', 'r') as f:
                self.levels = json.load(f)
        except FileNotFoundError:
            pass

    def save_levels(self):
        with open('levels.json', 'w') as f:
            json.dump(self.levels, f)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        
        if guild_id not in self.levels:
            self.levels[guild_id] = {}
        
        if user_id not in self.levels[guild_id]:
            self.levels[guild_id][user_id] = {"xp": 0, "level": 1}
        
        self.levels[guild_id][user_id]["xp"] += random.randint(15, 25)
        xp = self.levels[guild_id][user_id]["xp"]
        lvl = self.levels[guild_id][user_id]["level"]
        
        xp_required = (lvl * 100)
        
        if xp >= xp_required:
            self.levels[guild_id][user_id]["level"] += 1
            self.levels[guild_id][user_id]["xp"] = 0
            await message.channel.send(
                f"🎉 Поздравляем {message.author.mention}! Вы достигли {lvl + 1} уровня!"
            )
        
        self.save_levels()

    @commands.slash_command()
    async def rank(self, inter, member: disnake.Member = None):
        """Показать ранг пользователя"""
        member = member or inter.author
        guild_id = str(inter.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.levels or user_id not in self.levels[guild_id]:
            return await inter.response.send_message(
                "У пользователя пока нет ранга!", ephemeral=True
            )
        
        level = self.levels[guild_id][user_id]["level"]
        xp = self.levels[guild_id][user_id]["xp"]
        xp_required = (level * 100)
        
        embed = disnake.Embed(title=f"Ранг {member.display_name}", color=member.color)
        embed.add_field(name="Уровень", value=level)
        embed.add_field(name="XP", value=f"{xp}/{xp_required}")
        embed.set_thumbnail(url=member.display_avatar)
        
        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(LevelSystem(bot))
