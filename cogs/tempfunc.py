import discord
from discord.ext import commands, tasks
import json
import datetime
from typing import Optional
from config import config

class TempActions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_data_file = "db/temp_actions.json"
        self.temp_data = self.load_data()
        self.check_temp_actions.start()

    def load_data(self):
        try:
            with open(self.temp_data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"temp_bans": {}, "temp_roles": {}}

    def save_data(self):
        with open(self.temp_data_file, 'w') as f:
            json.dump(self.temp_data, f, indent=4)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def tempban(self, ctx, member: discord.Member, duration: str, *, reason: Optional[str] = "No reason provided"):
        """Temporarily ban a member
        Duration format: 1d, 1h, 1m (days, hours, minutes)"""
        
        duration_seconds = 0
        time_units = {'d': 86400, 'h': 3600, 'm': 60}
        
        try:
            amount = int(duration[:-1])
            unit = duration[-1].lower()
            if unit in time_units:
                duration_seconds = amount * time_units[unit]
            else:
                raise ValueError
        except ValueError:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: invalid duration format. Use: 1d, 1h, 1m",color=config.hex))
            return

        expiry_time = datetime.datetime.now().timestamp() + duration_seconds

        self.temp_data["temp_bans"][str(member.id)] = {
            "guild_id": ctx.guild.id,
            "expiry_time": expiry_time,
            "reason": reason
        }
        
        self.save_data()

        try:
            await member.ban(reason=f"Temporary ban: {reason}")
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: banned {member.name} for `{duration}`",color=config.hex))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: I don't have permission to ban this member.",color=config.hex))

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def temprole(self, ctx, member: discord.Member, duration: str, role: discord.Role, *, reason: Optional[str] = "No reason provided"):
        """Temporarily assign a role to a member
        Duration format: 1d, 1h, 1m (days, hours, minutes)"""
        
        duration_seconds = 0
        time_units = {'d': 86400, 'h': 3600, 'm': 60}
        
        try:
            amount = int(duration[:-1])
            unit = duration[-1].lower()
            if unit in time_units:
                duration_seconds = amount * time_units[unit]
            else:
                raise ValueError
        except ValueError:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: invalid duration format. Use: 1d, 1h, 1m",color=config.hex))
            return

        expiry_time = datetime.datetime.now().timestamp() + duration_seconds

        self.temp_data["temp_roles"][f"{member.id}_{role.id}"] = {
            "guild_id": ctx.guild.id,
            "expiry_time": expiry_time,
            "role_id": role.id,
            "reason": reason
        }
        
        self.save_data()

        try:
            await member.add_roles(role, reason=f"Temporary role: {reason}")
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added role {role.mention} to {member.mention} for `{duration}`.",color=config.hex))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: I don't have permission to manage roles for this member.",color=config.hex))

    @tasks.loop(minutes=5)
    async def check_temp_actions(self):
        current_time = datetime.datetime.now().timestamp()
        
        for user_id, ban_data in list(self.temp_data["temp_bans"].items()):
            if current_time >= ban_data["expiry_time"]:
                guild = self.bot.get_guild(ban_data["guild_id"])
                if guild:
                    try:
                        await guild.unban(discord.Object(id=int(user_id)), reason="Temporary ban expired")
                    except (discord.NotFound, discord.Forbidden):
                        pass
                del self.temp_data["temp_bans"][user_id]
                self.save_data()

        for key, role_data in list(self.temp_data["temp_roles"].items()):
            if current_time >= role_data["expiry_time"]:
                user_id, role_id = map(int, key.split('_'))
                guild = self.bot.get_guild(role_data["guild_id"])
                if guild:
                    member = guild.get_member(user_id)
                    role = guild.get_role(role_id)
                    if member and role:
                        try:
                            await member.remove_roles(role, reason="Temporary role expired")
                        except discord.Forbidden:
                            pass
                del self.temp_data["temp_roles"][key]
                self.save_data()

    @check_temp_actions.before_loop
    async def before_check_temp_actions(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TempActions(bot))