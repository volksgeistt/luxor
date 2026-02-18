import discord
from discord.ext import commands
import json
from config import config
import os

class IgnoreChannelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignored_channels = {}
        self.db_file = "db/ignoredChannels.json"
        self._create_data_folder()
        self.load_ignored_channels()
        
    def _create_data_folder(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.db_file):
            with open(self.db_file, "w") as f:
                json.dump({}, f, indent=4)

    def load_ignored_channels(self):
        try:
            with open(self.db_file, "r") as f:
                data = json.load(f)
                self.ignored_channels = {int(k): v for k, v in data.items()}
        except FileNotFoundError:
            self.ignored_channels = {}
            self._save_to_db()

    def _save_to_db(self):
        with open(self.db_file, "w") as f:
            json.dump(self.ignored_channels, f, indent=4)

    @commands.group(name="ignore")
    @commands.has_permissions(administrator=True)
    async def ignore(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(
                title=f"Ignore Channel Commands",
                description=f"`ignore channel`, `ignore channel add`, `ignore channel remove`, `ignore channel list`, `ignore channel reset`\n{config.ques_emoji} Example: `ignore channel add <#channel>`",
                color=config.hex
            ))

    @ignore.group(name="channel")
    async def channel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(
                title=f"Ignore Channel Commands",
                description=f"`ignore channel`, `ignore channel add`, `ignore channel remove`, `ignore channel list`, `ignore channel reset`\n{config.ques_emoji} Example: `ignore channel add <#channel>`",
                color=config.hex
            ))

    @channel.command(name="add",help="add a channel to ignored channels list",aliases=["set"])
    async def add_channel(self, ctx, channel: discord.TextChannel):
        guild_id = ctx.guild.id
        
        if guild_id not in self.ignored_channels:
            self.ignored_channels[guild_id] = []
            
        if channel.id in self.ignored_channels[guild_id]:
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: {channel.mention} is already in ignored channels list.",
                color=config.hex
            ))
            return
            
        if len(self.ignored_channels[guild_id]) >= 5:
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: max limit reached, you can only add ignore up to 5 channels.",
                color=config.hex
            ))
            return
            
        self.ignored_channels[guild_id].append(channel.id)
        self._save_to_db()
        
        await ctx.send(embed=discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: added {channel.mention} to ignored channels list.",
            color=config.hex
        ))

    @channel.command(name="remove",help="remove a channel from ignored channels list",aliases=["delete"])
    async def remove_channel(self, ctx, channel: discord.TextChannel):
        guild_id = ctx.guild.id
        
        if guild_id not in self.ignored_channels or channel.id not in self.ignored_channels[guild_id]:
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: {channel.mention} is not in ignored channels list.",
                color=config.hex
            ))
            return
            
        self.ignored_channels[guild_id].remove(channel.id)
        self._save_to_db()
        
        await ctx.send(embed=discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: removed {channel.mention} from ignored channels list.",
            color=config.hex
        ))

    @channel.command(name="list",help="view all ignored channels",aliases=["view","config"])
    async def list_channels(self, ctx):
        guild_id = ctx.guild.id
        
        if guild_id not in self.ignored_channels or not self.ignored_channels[guild_id]:
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: no ignored channels set for this server.",
                color=config.hex
            ))
            return
            
        channels = []
        for channel_id in self.ignored_channels[guild_id]:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                channels.append(channel.mention)
                
        if not channels:
            description = "No valid channels found"
        else:
            description = "**Ignored Channels:**\n" + "\n".join(channels)
            
        await ctx.send(embed=discord.Embed(
            description=description,
            color=config.hex
        ))

    @channel.command(name="reset",help="reset whole ignore channel db for the guild", aliases=["clear"])
    async def reset_channels(self, ctx):
        guild_id = ctx.guild.id
        
        if guild_id not in self.ignored_channels or not self.ignored_channels[guild_id]:
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: no ignored channels to reset.",
                color=config.hex
            ))
            return
            
        self.ignored_channels[guild_id] = []
        self._save_to_db()
        
        await ctx.send(embed=discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: cleared all ignored channels.",
            color=config.hex
        ))

    async def check_ignored_channel(self, message):
        guild_id = message.guild.id
        return guild_id in self.ignored_channels and message.channel.id in self.ignored_channels[guild_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        if await self.check_ignored_channel(message):
            ctx = await self.bot.get_context(message)
            if ctx.valid:
                await message.channel.send(
                    embed=discord.Embed(
                        description=f"{config.error_emoji} {ctx.author.mention}: my commands are disabled for this channel.",
                        color=config.hex
                    ),
                    delete_after=25
                )
                return

def setup(bot):
    bot.add_cog(IgnoreChannelSystem(bot))