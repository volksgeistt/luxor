import discord
from discord.ext import commands
import json
from datetime import datetime, timezone
from config import config

def load_config():
    try:
        with open('db/alt.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    with open('db/alt.json', 'w') as f:
        json.dump(config, f)

class AntiAltID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    def get_guild_config(self, guild_id):
        str_guild_id = str(guild_id)
        if str_guild_id not in self.config:
            self.config[str_guild_id] = {"enabled": False, "threshold": 30}
            save_config(self.config)
        return self.config[str_guild_id]

    def is_new_account(self, member: discord.Member):
        guild_config = self.get_guild_config(member.guild.id)
        account_age = (datetime.now(timezone.utc) - member.created_at).days
        return account_age < guild_config['threshold']

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_config = self.get_guild_config(member.guild.id)
        if guild_config['enabled'] and self.is_new_account(member):
            try:
                await member.send(f"{config.error_emoji} {member.mention}: you've been kicked from **{member.guild.name}** because you don't fulfill the minimum account age requirement to join the guild.")
                await member.kick(reason=f"{self.bot.user.name} @ anti-alt triggered : potential alt acc")
            except Exception as e:
                print(f"Nahi kar paya ban {member.name} ko in {member.guild.name}: {e}")

    @commands.group(name="antialt", invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def antialt(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Anti-Alt Subcommand:",description=f"`antialt toggle`, `antialt threshold`, `antialt config`\n{config.ques_emoji} Example: `antialt threshold 7`",color=config.hex))

    @antialt.command(help="enable/disable the anti-alt module for guild.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def toggle(self, ctx):
        guild_config = self.get_guild_config(ctx.guild.id)
        guild_config['enabled'] = not guild_config['enabled']
        save_config(self.config)
        status = "enabled" if guild_config['enabled'] else "disabled"
        await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.tick} {ctx.author.mention}: **{status}** anti-alt module for this guild."))

    @antialt.command(aliases=["limit", "accage"], help="set the account age limit for anti-alt module.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def threshold(self, ctx, days: int):
        if days < 1:
            await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: minimum threshold should be atleast 1 day."))
        elif days > 3650:
            await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: max threshold can be set to 3650 days."))
            return
        guild_config = self.get_guild_config(ctx.guild.id)
        guild_config['threshold'] = days
        save_config(self.config)
        await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.tick} {ctx.author.mention}: anti-alt threshold set to {days} day(s)."))

    @antialt.command(aliases=["config","setting"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def status(self, ctx):
        guild_config = self.get_guild_config(ctx.guild.id)
        status = "enabled" if guild_config['enabled'] else "disabled"
        embed=discord.Embed(color=config.hex,description=f"{config.ques_emoji} {ctx.author.mention}: anti-alt module is **{status}** and threshold limit is **{guild_config['threshold']}** days(s).")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiAltID(bot))