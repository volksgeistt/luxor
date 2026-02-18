import discord
from discord.ext import commands
from config import mongo, config

class UsernameTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = mongo.db.username_tracker

    @commands.group(name='username', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def username_group(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Username-Tracker Subcommands:",description=f"`username channel`, `username delete`\n{config.ques_emoji} Example: `username channel #usernames`", color=config.hex))

    @username_group.command(name='channel', aliases=['set'], help="set a log channel for username tracking")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def set_username_channel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await self.db.update_one(
            {'guild_id': ctx.guild.id},
            {'$set': {'username_log_channel_id': channel.id}},
            upsert=True
        )
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: username logs will be sent to {channel.mention}", color=config.hex))

    @username_group.command(name='unset', aliases=['remove', 'reset'],help="remove a channel from username tracking")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def unset_username_channel(self, ctx):
        result = await self.db.find_one_and_delete({'guild_id': ctx.guild.id})
        if result and result.get('username_log_channel_id'):
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: username logging has been disabled.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no username log channel was found in this server.", color=config.hex))

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.name != after.name:
            for guild in after.mutual_guilds:
                try:
                    config = await self.db.find_one({'guild_id': guild.id})
                    
                    if config and 'username_log_channel_id' in config:
                        log_channel = guild.get_channel(config['username_log_channel_id'])
                        if log_channel:
                            embed = discord.Embed(
                                description=f"> **{before.name}** has been **dropped**.",
                                color=discord.Color.blurple()
                            )
                            await log_channel.send(embed=embed)
                except Exception as e:
                    print(f"Error logging username change: {e}")

async def setup(bot):
    await bot.add_cog(UsernameTracker(bot))