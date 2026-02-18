import discord
from discord.ext import commands
import json
import asyncio
import os
from config import config

class AntiBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "db/antibot.json"
        self.load_database()

    def load_database(self):
        if not os.path.exists(self.db_path):
            self.db = {}
            self.save_database()
        else:
            with open(self.db_path, 'r') as f:
                self.db = json.load(f)

    def save_database(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.db, f, indent=4)

    def get_guild_data(self, guild_id: int):
        guild_id = str(guild_id)
        if guild_id not in self.db:
            self.db[guild_id] = {
                "channels": [],
                "bypassed_bots": []
            }
            self.save_database()
        return self.db[guild_id]

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def antibot(self, ctx):
        await ctx.send(embed=discord.Embed(title="Anti-Bot Subcommands",description=f">>> `antibot`, `antibot channel add`, `antibot channel remove`, `antibot channel show`, `antibot channel reset`, `antibot bypass`, `antibot bypass add`, `antibot bypass remove`, `antibot bypass show`, `antibot bypass reset`\n{config.ques_emoji} Example: `antibot channel add <#channel>`", color=discord.Color.blurple()))

    @antibot.group(name="channel",aliases=["cnl"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def antibot_channel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title="Anti-Bot Channel Subcommands",description=f">>> `antibot`, `antibot channel add`, `antibot channel remove`, `antibot channel show`, `antibot channel reset`\n{config.ques_emoji} Example: `antibot channel add <#channel>`", color=discord.Color.blurple()))

    @antibot_channel.command(name="add", help="setup a channel for antibot module")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def channel_add(self, ctx, channel: discord.TextChannel):
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if str(channel.id) in guild_data["channels"]:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: the following channel is already added as anti-bot channel.", color=discord.Color.blurple()))
        
        if len(guild_data["channels"]) >= 5:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: there's a limit of upto 5 channels only for anti-bot protection.", color=discord.Color.blurple()))
        
        guild_data["channels"].append(str(channel.id))
        self.save_database()
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: enabled anti-bot for {channel.mention}.", color=discord.Color.blurple()))

    @antibot_channel.command(name="remove", help="removes channel for antibot module")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def channel_remove(self, ctx, channel: discord.TextChannel):
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if str(channel.id) not in guild_data["channels"]:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this channel is not in anti-bot list.", color=discord.Color.blurple()))
        
        guild_data["channels"].remove(str(channel.id))
        self.save_database()
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: disabled anti-bot for {channel.mention}.", color=discord.Color.blurple()))

    @antibot.group(name="bypass",aliases=["byp"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)    
    async def antibot_bypass(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title="Anti-Bot Bypass Subcommands",description=f">>> `antibot bypass`, `antibot bypass add`, `antibot bypass remove`, `antibot bypass show`, `antibot bypass reset`\n{config.ques_emoji} Example: `antibot bypass add <@bot>`", color=discord.Color.blurple()))

    @antibot_bypass.command(name="add", help="adds a bot to antibot bypass")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def bypass_add(self, ctx, user: discord.User):
        if not user.bot:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you can only add bots to the bypass list.", color=discord.Color.blurple()))
        
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if str(user.id) in guild_data["bypassed_bots"]:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this bot is already in bypass list.", color=discord.Color.blurple()))
        
        if len(guild_data["bypassed_bots"]) >= 10:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you can only add up to 10 bots to the bypass list.", color=discord.Color.blurple()))
        
        guild_data["bypassed_bots"].append(str(user.id))
        self.save_database()
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added {user.mention} to anti-bot bypass list.", color=discord.Color.blurple()))

    @antibot_bypass.command(name="remove", help="removes a bot from antibot bypass")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def bypass_remove(self, ctx, user: discord.User):
        guild_data = self.get_guild_data(ctx.guild.id)
        
        if str(user.id) not in guild_data["bypassed_bots"]:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this bot is not in bypass list.", color=discord.Color.blurple()))
        
        guild_data["bypassed_bots"].remove(str(user.id))
        self.save_database()
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed {user.mention} from anti-bot bypass list.", color=discord.Color.blurple()))

    @antibot_bypass.command(name="show", help="shows lists of bypassed bots from antibot")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def bypass_show(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        if not guild_data["bypassed_bots"]:
            description = f"{config.error_emoji} {ctx.author.mention}: no bots in bypass list."
        else:
            description = f"**Anti-Bot Bypassed Bots:**\n " + ", ".join([f"<@{bot_id}>" for bot_id in guild_data["bypassed_bots"]])
        await ctx.send(embed=discord.Embed(description=description, color=discord.Color.blurple()))

    @antibot_channel.command(name="show",help="shows list of bypasses channels from antibot")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def channel_show(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        if not guild_data["channels"]:
            description = f"{config.error_emoji} {ctx.author.mention}: no channels in anti-bot list."
        else:
            description = f"**Anti-Bot Bypassed Channels:**\n " + ", ".join([f"<#{channel_id}>" for channel_id in guild_data["channels"]])
        await ctx.send(embed=discord.Embed(description=description, color=discord.Color.blurple()))

    @antibot_bypass.command(name="reset")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def bypass_reset(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["bypassed_bots"] = []
        self.save_database()
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: cleared all bypassed bots.", color=discord.Color.blurple()))

    @antibot_channel.command(name="reset")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def channel_reset(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["channels"] = []
        self.save_database()
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: cleared all protected channels.", color=discord.Color.blurple()))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot and message.author.id != self.bot.user.id:
            guild_data = self.get_guild_data(message.guild.id)
            
            if str(message.channel.id) in guild_data["channels"]:
                if str(message.author.id) not in guild_data["bypassed_bots"]:
                    await message.delete()
                    warning = await message.channel.send(embed=discord.Embed(description=f"{config.error_emoji} anti-bot is enabled in this channel only bypassed bots commands can be executed here.", color=discord.Color.blurple()))
                    await asyncio.sleep(7)
                    await warning.delete()

async def setup(bot):
    await bot.add_cog(AntiBot(bot))