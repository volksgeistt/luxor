import discord
from discord.ext import commands
from config import config

class VoiceCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="voice", aliases=["vc"], invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def voice_group(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Voice Manage Subcommands:",description=f">>> `voice deafen`, `voice undeafen`, `voice mute`, `voice unmute`, `voice kick`, `voice move`, `voice mte`, `voice unmte`\n{config.ques_emoji} Example: `voice mte <@user>`",color=config.hex))

    @voice_group.command(name="deafen", aliases=["def"])
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def deafen(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(deafen=True, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: deafened **{member.display_name}**",color=config.hex))

    @voice_group.command(name="undeafen", aliases=["undef"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def undeafen(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(deafen=False, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: undeafened **{member.display_name}**",color=config.hex))

    @voice_group.command(name="mute")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(mute=True, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: muted **{member.display_name}** in voice channels.",color=config.hex))

    @voice_group.command(name="unmute")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(mute=False, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: unmuted **{member.display_name}** for voice channels.",color=config.hex))

    @voice_group.command(name="kick")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.move_to(None, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: kicked **{member.display_name}** from voice channel.",color=config.hex))

    @voice_group.command(name="move")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def move(self, ctx, member: discord.Member, channel: discord.VoiceChannel, *, reason=None):
        await member.move_to(channel, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: moved **{member.display_name}** to **#{channel.name}**",color=config.hex))

    @voice_group.command(name="mte")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def mte(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(mute=True, deafen=True)
        await member.move_to(None, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: muted, deafened and disconnected **{member.display_name}** from the voice channel.",color=config.hex))

    @voice_group.command(name="unmte")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def unmte(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(mute=False, deafen=False, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: unmuted and undeafened **{member.display_name}**",color=config.hex))

async def setup(bot):
    await bot.add_cog(VoiceCommandsCog(bot))