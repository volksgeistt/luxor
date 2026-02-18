import discord
from discord.ext import commands
import json
from pathlib import Path
from config import config

data_file = Path("db/medialog.json")
if data_file.exists():
    with data_file.open("r") as f:
        data = json.load(f)
else:
    data = {}

class MediaLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_media(self, message):
        if message.attachments:
            server_id = str(message.guild.id)
            channel_id = str(message.channel.id)
            if server_id in data:
                log_channel_id = data[server_id]
                log_channel = message.guild.get_channel(int(log_channel_id))
                if log_channel is not None:
                    for attachment in message.attachments:
                        file_extension = attachment.filename.split(".")[-1].lower()
                        if file_extension in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "psd", "svg", "webp", "heic", "heif", "ico"]:
                            embed=discord.Embed(description=f"**{config.autopost} Logged An Image\n\t {config.joindm} Sent By: `{message.author.name}`\n\t {config.ar} Sent In: {message.channel.mention}**",color=config.hex)
                            embed.set_footer(text="media logger",icon_url=self.bot.user.avatar)
                            embed.set_image(url=attachment.url)
                            await log_channel.send(embed=embed)
                        elif file_extension in ["mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "m4v", "3gp", "m4p"]:
                            embed=discord.Embed(description=f"**{config.autopost} Logged Video\n\t {config.joindm} Sent By: `{message.author.name}`\n\t {config.ar} Sent In: {message.channel.mention}**",color=config.hex)
                            embed.set_footer(text="media logger",icon_url=self.bot.user.avatar)
                            embed.add_field(name="Video", value=attachment.url)
                            await log_channel.send(embed=embed)
                        else:
                            embed=discord.Embed(description=f"**{config.autopost} Logged {file_extension} File\n\t {config.joindm} Sent By: `{message.author.name}`\n\t {config.ar} Sent In: {message.channel.mention}**",color=config.hex)
                            embed.set_footer(text=f"{self.bot.user.name} Media Logger",icon_url=self.bot.user.avatar)
                            await log_channel.send(embed=embed, file=await attachment.to_file())
                else:
                    print(f"Log channel not found for server {message.guild.name} ({server_id})")

    @commands.group(name="medialogger", aliases=["attachlogger","medialog"],invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def logger(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"media logger Subcommands",description=f">>> `medialog add`, `medialog remove`, `medialog clear`",color=config.hex))

    @logger.command(help="adds a channel to medialogger")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)    
    async def add(self, ctx, channel_id: int):
        server_id = str(ctx.guild.id)
        data[server_id] = str(channel_id)
        with data_file.open("w") as f:
            json.dump(data, f)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added media log of guild ({server_id}) to log channel ({channel_id})",color=config.hex))

    @logger.command(help="removes a channel from medialogger")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, server_id: int):
        server_id = str(server_id)
        if server_id in data:
            del data[server_id]
            with data_file.open("w") as f:
                json.dump(data, f)
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed guild ({server_id}) from media logging.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: guild ({server_id}) not found.",color=config.hex))

    @logger.command()
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def reset(self, ctx):
        data.clear()
        with data_file.open("w") as f:
            json.dump(data, f)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: cleared media logging module for whole bot uwu.",color=config.hex))

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            await self.log_media(message)

async def setup(bot):
    await bot.add_cog(MediaLogger(bot))