import discord
from discord.ext import commands
import json
import os
import datetime
from typing import List, Dict
from config import config

class PaginationButtons(discord.ui.View):
    def __init__(self, pages: List[discord.Embed], timeout: int = 60):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        
    @discord.ui.button(emoji="<:prev:1229446062335328306>", style=discord.ButtonStyle.blurple)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()
            
    @discord.ui.button(emoji="<:next:1229446448777527327>", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        else:
            await interaction.response.defer()

class GuildBlacklist:
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_file = "db/guildBlacklist.json"
        self.blacklisted_guilds = self.load_blacklist()

    def load_blacklist(self) -> Dict:
        if os.path.exists(self.blacklist_file):
            with open(self.blacklist_file, 'r') as f:
                return json.load(f)
        return {}

    def save_blacklist(self):
        with open(self.blacklist_file, 'w') as f:
            json.dump(self.blacklisted_guilds, f, indent=4)
    
    def clear_blacklist(self):
        self.blacklisted_guilds = {}
        self.save_blacklist()

    async def check_guilds(self):
        for guild in self.bot.guilds:
            if str(guild.id) in self.blacklisted_guilds:
                self.blacklisted_guilds[str(guild.id)]['guild_name'] = guild.name
                self.save_blacklist()
                
                try:
                    embed = discord.Embed(
                        description=f">>> your server has been blacklisted from using this bot.\nIf you think this is a mistake, please consider opening a ticket in the [Support Server]({config.support_server})",
                        color=discord.Color.blurple()
                    )
                    embed.set_author(name="Guild Blacklist Notification",icon_url=self.bot.user.avatar)
                    embed.set_footer(text=f"Sent From ~ {guild.name}",icon_url=self.bot.user.avatar)
                    await guild.owner.send(embed=embed)
                except:
                    pass  
                await guild.leave()

class BlacklistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_manager = GuildBlacklist(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.blacklist_manager.check_guilds()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if str(guild.id) in self.blacklist_manager.blacklisted_guilds:
            self.blacklist_manager.blacklisted_guilds[str(guild.id)]['guild_name'] = guild.name
            self.blacklist_manager.save_blacklist()
            try:
                embed = discord.Embed(
                    description=f">>> your server has been blacklisted from using this bot.\nIf you think this is a mistake, please consider opening a ticket in the [Support Server]({config.support_server})",
                    color=discord.Color.blurple()
                )
                embed.set_author(name="Guild Blacklist Notification",icon_url=self.bot.user.avatar)
                embed.set_footer(text=f"Sent From ~ {guild.name}",icon_url=self.bot.user.avatar)
                await guild.owner.send(embed=embed)
            except:
                pass
            await guild.leave()

    @commands.group(name="guild")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner() 
    async def guild_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title="Guild Blacklisting",description=f">>> `guild blacklist`, `guild blacklist add`, `guild blacklist remove`, `guild blacklist view`, `guild blacklist clear`",color=config.hex))

    @guild_group.group(name="blacklist",aliases=["bl","blist"])
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    async def blacklist_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title="Guild Blacklisting",description=f">>> `guild blacklist`, `guild blacklist add`, `guild blacklist remove`, `guild blacklist view`, `guild blacklist clear`",color=config.hex))

    @blacklist_group.command(name="add")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    async def blacklist_add(self, ctx, guild_id: str, *, reason: str = "No reason provided"):
        """Add a guild to the blacklist"""
        try:
            guild = self.bot.get_guild(int(guild_id))
            guild_name = guild.name if guild else "Unknown Guild"
            
            if guild:
                guild_name = guild.name
            
            self.blacklist_manager.blacklisted_guilds[guild_id] = {
                "reason": reason,
                "added_by": ctx.author.id,
                "added_at": int(datetime.datetime.utcnow().timestamp()),
                "guild_name": guild_name
            }
            self.blacklist_manager.save_blacklist()

            embed = discord.Embed(
                description=f">>> Guild ID: {guild_id}\nGuild Name: {guild_name}\nReason: {reason}",
                color=discord.Color.blurple()
            )
            embed.set_author(name="Guild Blacklisted",icon_url=self.bot.user.avatar)
            embed.set_footer(text=f"Executed By ~ {ctx.author.name}",icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)

            if guild:
                await self.blacklist_manager.check_guilds()
        except ValueError:
            await ctx.send(f"{ctx.author.mention}: please check the guild id that you're trying to blacklist.")


    @blacklist_group.command(name="remove")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    async def blacklist_remove(self, ctx, guild_id: str):
        """Remove a guild from the blacklist"""
        if guild_id in self.blacklist_manager.blacklisted_guilds:
            guild_info = self.blacklist_manager.blacklisted_guilds.pop(guild_id)
            self.blacklist_manager.save_blacklist()
            
            embed = discord.Embed(
                description=f">>> Guild ID: {guild_id}\nGuild Name: {guild_info.get('guild_name', 'Unknown')}",
                color=discord.Color.blurple()
            )
            embed.set_author(name="Guild Blacklist Removed",icon_url=self.bot.user.avatar)
            embed.set_footer(text=f"Executed By ~ {ctx.author.name}",icon_url=self.bot.user.avatar)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{ctx.author.mention}: the guild with provided id, is not blacklisted.")

    @blacklist_group.command(name="show",aliases=["config","view"])
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    async def blacklist_show(self, ctx):
        """Show all blacklisted guilds"""
        if not self.blacklist_manager.blacklisted_guilds:
            await ctx.send(f"{ctx.author.mention}: no guilds are blacklisted.")
            return

        embeds = []
        items_per_page = 5
        items = list(self.blacklist_manager.blacklisted_guilds.items())
        
        for i in range(0, len(items), items_per_page):
            embed = discord.Embed(
                color=discord.Color.blurple(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(name="Blacklisted Guilds",icon_url=self.bot.user.avatar)

            
            page_items = items[i:i + items_per_page]
            for guild_id, info in page_items:
                added_timestamp = info.get('added_at', 0)
                timestamp_display = f"<t:{added_timestamp}:R>" if isinstance(added_timestamp, int) else "Unknown"
                
                embed.add_field(
                    name=f"Guild: {info.get('guild_name', 'Unknown')}",
                    value=f"> ID: {guild_id}\n"
                          f"> Reason: {info.get('reason', 'No reason provided')}\n"
                          f"> Added by: <@{info.get('added_by', 'Unknown')}>\n"
                          f"> Added: {timestamp_display}\n",
                    inline=False
                )
            
            embed.set_footer(text=f"Page {len(embeds) + 1}/{-(-len(items) // items_per_page)}",icon_url=self.bot.user.avatar)

            embeds.append(embed)

        view = PaginationButtons(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @blacklist_group.command(name="clear")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_owner()
    async def blacklist_clear(self, ctx):
        count = len(self.blacklist_manager.blacklisted_guilds)
        self.blacklist_manager.clear_blacklist()
        
        embed = discord.Embed(
            description=f">>> Successfully cleared {count} guilds from the blacklist.",
            color=discord.Color.blurple()
        )
        embed.set_author(name="Guild Blacklist Cleared", icon_url=self.bot.user.avatar)
        embed.set_footer(text=f"Executed By ~ {ctx.author.name}", icon_url=self.bot.user.avatar)
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(BlacklistCog(bot))