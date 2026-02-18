import discord
from discord.ext import commands
from datetime import datetime, timedelta
import os
import json
import re
from config import config

class AFKView(discord.ui.View):
    def __init__(self, user_id, cog):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.cog = cog

    @discord.ui.button(label="Revoke AFK", style=discord.ButtonStyle.grey)
    async def return_from_afk(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This interaction menu button is not for you!", ephemeral=True)
            return

        if str(self.user_id) in self.cog.afk_data:
            start_time = datetime.fromisoformat(self.cog.afk_data[str(self.user_id)]['start_time'])
            afk_duration = datetime.now() - start_time
            formatted_duration = self.cog.format_duration(afk_duration)
            
            del self.cog.afk_data[str(self.user_id)]
            del self.cog.afk_set_times[str(self.user_id)]
            self.cog.save_afk_data()
            
            await interaction.response.send_message(f"**{interaction.user.name}**, welcome back! You were AFK for **{formatted_duration}**")
            self.stop()
        else:
            await interaction.response.send_message(f"**{interaction.user.name}**, you're not AFK at the moment.", ephemeral=True)

class AFKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_data = {}
        self.afk_set_times = {}
        self.load_afk_data()
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+|discord\.gg/\S+')

    def load_afk_data(self):
        if os.path.exists('db/afk.json'):
            with open('db/afk.json', 'r') as f:
                data = json.load(f)
                self.afk_data = data.get('afk_data', {})
                self.afk_set_times = {k: datetime.fromisoformat(v) for k, v in data.get('afk_set_times', {}).items()}

    def save_afk_data(self):
        data = {
            'afk_data': self.afk_data,
            'afk_set_times': {k: v.isoformat() for k, v in self.afk_set_times.items()}
        }
        with open('db/afk.json', 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def format_duration(duration):
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)

    def get_history_cog(self):
        return self.bot.get_cog('AFKHistoryCog')

    def contains_mentions(self, message: str, guild) -> bool:
        """Check if the message contains any role or user mentions."""
        for role in guild.roles:
            if f"@{role.name}" in message or f"<@&{role.id}>" in message:
                return True
        
        if '@everyone' in message or '@here' in message:
            return True
        
        if re.search(r'<@!?\d+>', message):
            return True
        
        return False

    @commands.command(name="afk", help="Set yourself as AFK")
    @commands.cooldown(1, 7, commands.BucketType.user)
    @commands.guild_only()
    async def afk(self, ctx, *, reason: str = "I'm AFK!"):
        user_id = str(ctx.author.id)

        if user_id in self.afk_data:
            await ctx.send(f"**{ctx.author.name}**, you're already AFK with reason: **{self.afk_data[user_id]['reason']}**")
            return

        # Check for mentions
        if self.contains_mentions(reason, ctx.guild):
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: you cannot include user or role mentions in your AFK reason",color=config.hex))
            return

        # Check for URLs
        if self.url_pattern.search(reason):
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: you cannot include links or URLs in your AFK reason",color=config.hex))
            return

        current_time = datetime.now()
        self.afk_data[user_id] = {
            'reason': reason,
            'start_time': current_time.isoformat()
        }
        self.afk_set_times[user_id] = current_time
        self.save_afk_data()
        
        history_cog = self.get_history_cog()
        if history_cog:
            history_cog.add_afk_entry(user_id, reason, current_time.isoformat(), ctx.guild.name)
        
        view = AFKView(ctx.author.id, self)
        await ctx.send(f"**{ctx.author.name}**, your AFK is now set to: **{reason}**", view=view)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for mentioned_user in message.mentions:
            user_id = str(mentioned_user.id)
            if user_id in self.afk_data:
                afk_info = self.afk_data[user_id]
                start_time = datetime.fromisoformat(afk_info['start_time'])
                timestamp = int(start_time.timestamp())
                await message.channel.send(f"**{mentioned_user.name}** went AFK: **{afk_info['reason']}**! (<t:{timestamp}:R>)")
        author_id = str(message.author.id)
        if author_id in self.afk_data:
            if message.content.startswith('.afk') or \
               datetime.now() - self.afk_set_times[author_id] < timedelta(seconds=2):
                return
            start_time = datetime.fromisoformat(self.afk_data[author_id]['start_time'])
            afk_duration = datetime.now() - start_time
            formatted_duration = self.format_duration(afk_duration)
            del self.afk_data[author_id]
            del self.afk_set_times[author_id]
            self.save_afk_data()
            await message.channel.send(f"**{message.author.name}**, welcome back! You were AFK for **{formatted_duration}**")

async def setup(bot):
    await bot.add_cog(AFKCog(bot))