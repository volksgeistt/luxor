import discord
from discord.ext import commands
import json
import os
from typing import List, Dict, Union
from config import config

class MediaCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CONFIG_FILE = 'db/media_config.json'
        self.BYPASS_FILE = 'db/media_bypass.json'

    def load_media_config(self) -> Dict[str, List[int]]:
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_media_config(self, media_config: Dict[str, List[int]]):
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(media_config, f)

    def load_bypass(self) -> Dict[str, List[int]]:
        if os.path.exists(self.BYPASS_FILE):
            with open(self.BYPASS_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_bypass(self, bypass: Dict[str, List[int]]):
        with open(self.BYPASS_FILE, 'w') as f:
            json.dump(bypass, f)

    @commands.group(name='media')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def media(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title=f"Media Commands",description=f"`media`, `media channel add`, `media channel remove`, `media channel show`, `media bypass`, `media bypass add`, `media bypass remove`, `media bypass show`, `media bypass reset`\n{config.ques_emoji} Example: `media bypass add <@user>`",color=config.hex))

    @media.group(name='channel')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def media_channel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title=f"Media Channel Commands",description=f">>> `media`, `media channel add`, `media channel remove`, `media channel show`\n{config.ques_emoji} Example: `media channel add <#channel>`",color=config.hex))

    @media_channel.command(name='add',help="enable media-only for a channel")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def add_media_channel(self, ctx, channel: discord.TextChannel):
        media_config = self.load_media_config()
        guild_id = str(ctx.guild.id)
        if guild_id not in media_config:
            media_config[guild_id] = []
        if channel.id not in media_config[guild_id]:
            media_config[guild_id].append(channel.id)
            self.save_media_config(media_config)
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added {channel.mention} to media-only channel.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: {channel.mention} is already a media-only channel.",color=config.hex))

    @media_channel.command(name='remove',help="disable media-only for a channel")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def remove_media_channel(self, ctx, channel: discord.TextChannel):
        media_config = self.load_media_config()
        guild_id = str(ctx.guild.id)
        if guild_id in media_config and channel.id in media_config[guild_id]:
            media_config[guild_id].remove(channel.id)
            self.save_media_config(media_config)
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed {channel.mention} from media-only channel.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: {channel.mention} is not a media-only channel.",color=config.hex))

    @media_channel.command(name='show')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def show_media_channels(self, ctx):
        media_config = self.load_media_config()
        guild_id = str(ctx.guild.id)
        if guild_id in media_config and media_config[guild_id]:
            channels = [ctx.guild.get_channel(channel_id).mention for channel_id in media_config[guild_id] if ctx.guild.get_channel(channel_id)]
            await ctx.send(embed=discord.Embed(description=f"**Below are the media-only channels:**\n{', '.join(channels)}",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no media-only channel is configured in this guild.",color=config.hex))

    @media.group(name='bypass')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def media_bypass(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title=f"Media Bypass Commands",description=f">>> `media bypass`, `media bypass add`, `media bypass remove`, `media bypass show`, `media bypass reset`\n{config.ques_emoji} Example: `media bypass add <@user>`",color=config.hex))

    @media_bypass.command(name='add',help="adds a channel to media bypass")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def add_media_bypass(self, ctx, user: Union[discord.Member, discord.User]):
        bypass = self.load_bypass()
        guild_id = str(ctx.guild.id)
        if guild_id not in bypass:
            bypass[guild_id] = []
        if user.id not in bypass[guild_id]:
            bypass[guild_id].append(user.id)
            self.save_bypass(bypass)
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added {user.mention} to media bypass.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: {user.mention} is already added as media bypass.",color=config.hex))

    @media_bypass.command(name='remove',help="removes a channel from media bypass")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def remove_media_bypass(self, ctx, user: Union[discord.Member, discord.User]):
        bypass = self.load_bypass()
        guild_id = str(ctx.guild.id)
        if guild_id in bypass and user.id in bypass[guild_id]:
            bypass[guild_id].remove(user.id)
            self.save_bypass(bypass)
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed {user.mention} from media bypass.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: {user.mention} is not added as media bypass.",color=config.hex))

    @media_bypass.command(name='reset',help="reset media bypass for a guild")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def reset_media_bypass(self, ctx):
        bypass = self.load_bypass()
        guild_id = str(ctx.guild.id)
        if guild_id in bypass:
            bypass[guild_id] = []
            self.save_bypass(bypass)
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: media bypass list has been reset for this guild.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no media bypass list found in this server.",color=config.hex))

    @media_bypass.command(name='show')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def show_media_bypass(self, ctx):
        bypass = self.load_bypass()
        guild_id = str(ctx.guild.id)
        if guild_id in bypass and bypass[guild_id]:
            users = [f"{i+1} : <@{user_id}>" for i, user_id in enumerate(bypass[guild_id])]
            pages = [users[i:i+10] for i in range(0, len(users), 10)]
            
            class PaginationView(discord.ui.View):
                def __init__(self, pages):
                    super().__init__()
                    self.pages = pages
                    self.current_page = 0

                @discord.ui.button(emoji="<:prev:1229446062335328306>", style=discord.ButtonStyle.grey)
                async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.current_page > 0:
                        self.current_page -= 1
                        await self.update_message(interaction)

                @discord.ui.button(emoji="<:next:1229446448777527327>", style=discord.ButtonStyle.grey)
                async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.current_page < len(self.pages) - 1:
                        self.current_page += 1
                        await self.update_message(interaction)

                async def update_message(self, interaction: discord.Interaction):
                    embed = discord.Embed(title="Media Bypass Users", color=discord.Color.blue())
                    embed.description = "\n".join(self.pages[self.current_page])
                    embed.set_footer(text=f"Page {self.current_page+1}/{len(self.pages)}")
                    await interaction.response.edit_message(embed=embed, view=self)

            view = PaginationView(pages)
            embed = discord.Embed(title="Media Bypass Users", color=discord.Color.blue())
            embed.description = "\n".join(pages[0])
            embed.set_footer(text=f"Page 1/{len(pages)}")
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no users found for media bypass for this server.",color=config.hex))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if message.author == self.bot.user:
            return
        media_config = self.load_media_config()
        bypass = self.load_bypass()
        guild_id = str(message.guild.id)

        if guild_id in media_config and message.channel.id in media_config[guild_id]:
            if not message.attachments:
                if guild_id not in bypass or message.author.id not in bypass[guild_id]:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, only media content is allowed in this channel.", delete_after=3)

async def setup(bot):
    await bot.add_cog(MediaCommands(bot))