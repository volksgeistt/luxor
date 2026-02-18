import discord
from discord.ext import commands
import json
import os
import asyncio
import threading
from typing import Optional, Union
from config import config

class GreetSys(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "db/ServerGreetings.json"
        self.db_lock = threading.Lock()
        self.db = self.load_db()
        self.auto_reload_db()

    def load_db(self):
        try:
            if os.path.exists(self.db_path):
                with self.db_lock:
                    with open(self.db_path, "r") as f:
                        return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading database: {e}")
            return {}

    def save_db(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with self.db_lock:
                with open(self.db_path, "w") as f:
                    json.dump(self.db, f, indent=4)
        except Exception as e:
            print(f"Error saving database: {e}")

    def auto_reload_db(self):
        async def reload_task():
            while True:
                await asyncio.sleep(60)
                self.db = self.load_db()
        self.bot.loop.create_task(reload_task())

    def format_message(self, member: discord.Member, message_template: str) -> str:
        placeholders = {
            '{user}': str(member),
            '{user.mention}': member.mention,
            '{user.name}': member.name,
            '{user.tag}': str(member),
            '{guild.name}': member.guild.name,
            '{guild.count}': str(member.guild.member_count),
            '{user.joined_at}': discord.utils.format_dt(member.joined_at, style="R")
        }
        for key, value in placeholders.items():
            message_template = message_template.replace(key, value)
        return message_template

    @commands.group(name="greet", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def greet_command(self, ctx):
        help_embed = discord.Embed(
            title="Greet",
            description=f"`greet`, `greet setup`, `greet reset`, `greet config`, `greet test`\n{config.ques_emoji} Example: `greet setup`",
            color=config.hex
        )
        await ctx.send(embed=help_embed)

    @greet_command.command(name="setup", help="setup the greet message and channel for the guild.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def greet_setup(self, ctx):
        guild_id = str(ctx.guild.id)
        await ctx.send("Mention the channel where greetings should be sent:")
        try:
            channel_msg = await self.bot.wait_for(
                'message', 
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=60.0
            )
            channel = channel_msg.channel_mentions[0] if channel_msg.channel_mentions else None
        except asyncio.TimeoutError:
            return await ctx.send("Setup Timed Out.. Please Try Again.")
        await ctx.send(embed=discord.Embed(description="""
```
{user}
{user.mention}
{user.name}
{user.tag}
{user.joined_at}
{guild.name}
{guild.count}
```
""",color=config.hex))
        await ctx.send("Enter your greeting message, using the above variables in the message:")
        try:
            message_msg = await self.bot.wait_for(
                'message', 
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=120.0
            )
            message = message_msg.content
        except asyncio.TimeoutError:
            return await ctx.send("Setup Timed Out.. Please Try Again.")

        self.db[guild_id] = {
            "channel_id": channel.id if channel else None,
            "message": message,
            "enabled": True
        }
        self.save_db()
        confirmation_embed = discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: greeting will be sent to {channel.mention if channel else '**No channel set**'}",
            color=config.hex
        )
        await ctx.send(embed=confirmation_embed)

    @greet_command.command(name="reset", aliases=["delete","del","clear"], help="reset the greet setup data for the guild.")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def greet_reset(self, ctx):
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.db:
            del self.db[guild_id]
            self.save_db()
            
            embed = discord.Embed(
                description=f"{config.tick} {ctx.author.mention}: all greeting configurations for this server have been cleared.",
                color=config.hex
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: this server does not have any greeting configuration to reset.",
                color=config.hex
            )
            await ctx.send(embed=embed)

    @greet_command.command(name="test", help="test the greet message setup in your guild.")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def greet_test(self, ctx):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.db:
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: no greeting configuration found, please setup greet first.",
                color=config.hex
            ))
        
        greet_config = self.db[guild_id] 
        channel_id = greet_config.get('channel_id')
        message_template = greet_config.get('message')
        
        if not (channel_id and message_template):
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: incomplete greeting configuration, please setup greet properly..",
                color=config.hex
            ))
        
        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: configured greet channel not found.",
                color=config.hex
            ))
        
        formatted_message = self.format_message(ctx.author, message_template)
        test_embed = discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: test message sent to {channel.mention}",
            color=config.hex
        )
        await channel.send(formatted_message)
        await ctx.send(embed=test_embed)

    @greet_command.command(name="config", help="config your greet setup message.")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def greet_config(self, ctx):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.db:
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: no greeting configuration found.",
                color=config.hex
            ))
        
        greet_config = self.db[guild_id]  # renamed to avoid shadowing
        channel_id = greet_config.get('channel_id')
        message_template = greet_config.get('message')
        is_enabled = greet_config.get('enabled', False)
        
        config_embed = discord.Embed(
            title="Greeting System Configuration",
            color=discord.Color.blurple()
        )
        
        if channel_id:
            channel = ctx.guild.get_channel(channel_id)
            config_embed.add_field(
                name="Greeting Channel", 
                value=channel.mention if channel else f"Channel ID: {channel_id} (Not found)", 
                inline=False
            )
        else:
            config_embed.add_field(
                name="Greeting Channel", 
                value="No channel configured", 
                inline=False
            )
        
        config_embed.add_field(
            name="Greeting Message", 
            value=f"```{message_template or "No message set"}```", 
            inline=False
        )        
        await ctx.send(embed=config_embed)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        
        if guild_id not in self.db or not self.db[guild_id].get('enabled', False):
            return

        config = self.db[guild_id]
        channel_id = config.get('channel_id')
        message_template = config.get('message')

        if not (channel_id and message_template):
            return

        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        try:
            formatted_message = self.format_message(member, message_template)
            await channel.send(formatted_message)
        except Exception as e:
            print(f"Greeting error in {member.guild.name}: {e}")

async def setup(bot):
    await bot.add_cog(GreetSys(bot))