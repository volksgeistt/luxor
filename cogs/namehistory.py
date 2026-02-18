import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import asyncio
from typing import List
from config import config

class NameHistoryPaginator(discord.ui.View):
    def __init__(self, pages: List[discord.Embed]):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        
    @discord.ui.button(emoji="<:prev:1229446062335328306>", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()
            
    @discord.ui.button(emoji="<:next:1229446448777527327>", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()

class NameHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_file = "db/namehistory.json"
        self.status = {}
        self.load_database()
        
    def load_database(self):
        if not os.path.exists(self.db_file):
            with open(self.db_file, "w") as f:
                json.dump({}, f)
        
        with open(self.db_file, "r") as f:
            self.database = json.load(f)
            
    def save_database(self):
        with open(self.db_file, "w") as f:
            json.dump(self.database, f, indent=4)
            
    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.name != after.name:
            try:
                now = datetime.now()
                dt_string = now.strftime("%m/%d/%Y")
                user_id = str(before.id)
                
                if user_id not in self.database:
                    self.database[user_id] = {
                        "nameHistory": [
                            f'"{before.name}" ➡️ [`{dt_string}`]',
                            f'"{after.name}" ➡️ [`{dt_string}`]'
                        ]
                    }
                else:
                    self.database[user_id]["nameHistory"].append(
                        f'"{after.name}" ➡️ [`{dt_string}`]'
                    )
                    
                self.save_database()
            except Exception as e:
                print(f"Error in on_user_update: {e}")
                
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        now = datetime.now()
        statuses = ['online', 'dnd', 'idle']
        user_id = str(before.id)
        
        if str(before.status) in statuses and str(after.status) == 'offline':
            self.status[user_id] = now
        elif str(before.status) == 'offline' and str(after.status) in statuses:
            self.status[user_id] = now
            
    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        self.status[str(user.id)] = datetime.now()
        
    def create_name_history_embed(self, user: discord.User, entries: List[str], page: int, total_pages: int) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"{user.display_name}'s name-history", icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
   
        start_idx = page * 10
        end_idx = min(start_idx + 10, len(entries))
        
        for idx, entry in enumerate(entries[start_idx:end_idx], start=start_idx + 1):
            name, timestamp = entry.split("➡️")
            embed.add_field(name=f"{idx}", value=f"{name} **-** {timestamp}", inline=False)
            
        embed.set_footer(text=f'Page {page + 1}/{total_pages} • identical history is not filtered')
        return embed
        
    @commands.command(aliases=['nhistory', 'names', 'allnames', 'nh'],help="shows namehistory of a user")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def namehistory(self, ctx, user: discord.User = None):
        try:
            if user is None:
                user = ctx.author
                
            user_id = str(user.id)
            if user_id not in self.database:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no past name history is available for **{user}**.",color=config.hex))
                
            entries = self.database[user_id]["nameHistory"]
            pages = []
            total_pages = (len(entries) + 9) // 10
            
            for page in range(total_pages):
                embed = self.create_name_history_embed(user, entries, page, total_pages)
                pages.append(embed)
                
            view = NameHistoryPaginator(pages)
            await ctx.send(embed=pages[0], view=view)
            
        except Exception as e:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: some error occurred: {str(e)}",color=config.hex))
            
    @commands.command(aliases=["clearnamehistory","clearnh","cnh"], help="clears name history of the command executor")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def clearnames(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in self.database:
            del self.database[user_id]
            self.save_database()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: cleared all your name history."))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no name history logged for you."))
            
    @commands.command(aliases=['seen', 'ls'], help="shows lastseen of a user")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def lastseen(self, ctx, user: discord.User = None):
        if user is None:
            user = ctx.author
            
        user_id = str(user.id)
        last_seen = self.status.get(user_id)
        
        if last_seen:
            return await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: **{user}**'s last seen was {discord.utils.format_dt(last_seen, style='R')}"))
        else:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no last seen records for **{user}** is available yet."))

async def setup(bot):
    await bot.add_cog(NameHistory(bot))