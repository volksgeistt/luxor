import json
import discord
from discord.ext import commands
from typing import Dict, List
from config import config

class AutoReact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data: Dict[str, List[Dict[str, str]]] = {}
        self.file_path = "db/autoreact.json"
        self.MAX_REACTIONS = 10 
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}
            self._save_data()

    def _save_data(self) -> None:
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    @commands.group(
        help="Set autoreact message for the guild.",)
    async def autoreact(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title=f"Auto-React",description=f"`autoreact add`, `autoreact remove`, `autoreact clear`, `autoreact list`\n{config.ques_emoji} Example: `autoreact add <trigger> <emoji>`",color=config.hex))

    @autoreact.command(help="adds an autoreact message")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx, trigger: str, reaction: str):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.data:
            self.data[guild_id] = []
        
        if len(self.data[guild_id]) >= self.MAX_REACTIONS:
            embed = discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: max limit of {self.MAX_REACTIONS} auto-reactions reached. ",
                color=config.hex
            )
            await ctx.reply(embed=embed)
            return
        
        self.data[guild_id].append({
            "trigger": trigger,
            "emoji": reaction
        })
        self._save_data()
        
        embed = discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: created an autoreaction for `{trigger}`",
            color=config.hex
        )
        await ctx.reply(embed=embed)

    @autoreact.command(aliases=['remove'],help="deletes an autoreact message")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx, *, msg: str):
        guild_id = str(ctx.guild.id)
        if guild_id in self.data:
            self.data[guild_id] = [item for item in self.data[guild_id] if item["trigger"] != msg]
            self._save_data()
            
        embed = discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: deleted the autoreaction for `{msg}`",
            color=config.hex
        )
        await ctx.reply(embed=embed)

    @autoreact.command(aliases=['list'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def show(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.data and self.data[guild_id]:
            auto = ""
            for num, item in enumerate(self.data[guild_id], 1):
                auto += f"\n`{num}` {item['trigger']}: {item['emoji']}"
            
            embed = discord.Embed(description=auto, color=config.hex)
            embed.set_author(name="Auto-reactions:", icon_url=ctx.author.display_avatar)
        else:
            embed = discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: No auto reaction triggers have been set up",
                color=config.hex
            )
        await ctx.reply(embed=embed)

    @autoreact.command(help="deletes all autoreacts messages of the guild")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def clear(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.data:
            self.data[guild_id] = []
            self._save_data()
        
        embed = discord.Embed(
            description=f"{config.tick} {ctx.author.mention}: deleted all triggers for this guild.",
            color=0xd3d3d3
        )
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.data:
            return

        for item in self.data[guild_id]:
            if item["trigger"].lower() in message.content.lower():
                await message.add_reaction(item["emoji"])

async def setup(bot):
    await bot.add_cog(AutoReact(bot))