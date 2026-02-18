import discord
from discord.ext import commands
from config import config
import json
import os

class ProfileRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reward_tiers = {
            50: 1303329351714082847,   # First tier
            100: 1303329352154615808,  # Second tier
            200: 1303329352884293693,  # Third tier
            400: 1303329353316171776,  # Fourth tier
            800: 1303329357481115729,  # Fifth tier
            1000: 1303329358081036308, # Sixth tier
            1500: 1303329358487879690, # Seventh tier
            2000: 1303329359125418065, # Eighth tier
            2500: 1303329359918141440, # Ninth tier
            3000: 1303329409520107581, # Tenth tier
            3500: 1303329414477516832, # Eleventh tier
            4500: 1303329420316250243  # Twelfth tier
        }
        self.support_guild_id = 1295611048266563605

    def get_user_profile(self, user_id):
        try:
            if os.path.exists('db/profiles.json'):
                with open('db/profiles.json', 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                    return profiles.get("users", {}).get(str(user_id))
            return None
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None

    @commands.command(
        name="claim",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def claim(self, ctx):
        if ctx.guild.id != self.support_guild_id:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this can only be used in my [support server.](https://discord.gg/luxor)",color=config.hex))
        
        try:
            user_profile = self.get_user_profile(ctx.author.id)
            if not user_profile:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no profile found, please try after using some functions.",color=config.hex))
            
            command_count = user_profile.get("commands_used", 0)
            if command_count == 0:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you have not used any commands yet.",embed=config.hex))
            
            current_role_ids = {role.id for role in ctx.author.roles}
            
            eligible_roles = []
            for threshold, role_id in sorted(self.reward_tiers.items()):
                if command_count >= threshold and role_id not in current_role_ids:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        eligible_roles.append(role)
            
            if not eligible_roles:
                return await ctx.send(embed=discord.Embed(description=f"{config.premium} {ctx.author.mention}: you've already claimed all roles for which you're eligible.",color=config.hex))
            
            await ctx.author.add_roles(*eligible_roles)
            
            embed = discord.Embed(
                color=discord.Color.blurple()
            )
            
            role_names = [role.mention for role in eligible_roles]
            embed.description = (
                f"**Congratulations!** You've claimed some unique roles :tada:\n"
                f"{', '.join(role_names)}\n"
                f"Command Usage: `{command_count}`"
            )
            
            embed.set_footer(text="Luxor - Versatility at ease", icon_url=self.bot.user.avatar)
            embed.set_author(name="Role Rewards", icon_url=self.bot.user.avatar)
            
            await ctx.reply(embed=embed)
            
        except Exception as e:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an error occurred: {str(e)}",color=config.hex))
            raise e

async def setup(bot):
    await bot.add_cog(ProfileRewards(bot))