import discord
from discord.ext import commands
from config import config
import json


class LeaveLogger(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.leave_messages = {}
    self.load_leave_messages()

  def load_leave_messages(self):
    try:
      with open('db/goodbye.json', 'r') as file:
        self.leave_messages = json.load(file)
    except FileNotFoundError:
      pass

  def save_leave_messages(self):
    with open('db/goodbye.json', 'w') as file:
      json.dump(self.leave_messages, file, indent=4)

  @commands.group(aliases=["goodbye", "leavelogger"],description='show the help menu of autoresponse')
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(administrator=True)
  async def bye(self, ctx):
    if ctx.invoked_subcommand is None:
      await ctx.send(embed=discord.Embed(
          title="Goodbye Subcommnads:",
          description=
          f">>> `goodbye`, `goodbye variable`, `goodbye test`, `goodbye enable`, `goodbye disable`, `goodbye message`, `goodbye config`\n{config.ques_emoji} Example: `goodbye enable <#channel>`",
          color=config.hex))

  @bye.command(name="variables", aliases=["vars", "var", "variable"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def variables_(self, ctx):
    embed = discord.Embed(description=""" 
```
{user}               : name#discrim of the user
{user.mention}       : @mention of the user
{user.name}          : name of the user
{user.joined_at}     : guild join date of the user
{user.discriminator} : discriminator of the user
{guild.name}         : name of the guild
{guild.count}        : member count of the guild
{guild.id}           : id of the guild
```""",
                          color=config.hex)
    embed.set_author(name="Goodbye Variables", icon_url=self.bot.user.avatar)
    await ctx.send(embed=embed)

  @bye.command(name="enable", aliases=["setup"],help="setup the goodbye channel.")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def setup_(self, ctx, channel: discord.TextChannel = None):
    if channel is None:
      channel = ctx.channel
    guild_id = str(ctx.guild.id)
    self.leave_messages[guild_id] = {'channel_id': channel.id}
    self.save_leave_messages()
    await ctx.send(embed=discord.Embed(
        description=
        f"{config.tick} {ctx.author.mention}: setup goodbye logs channel to {channel.mention}",
        color=config.hex))

  @bye.command(name="message", aliases=["text", "msg"],help="setup the goodbye msg.")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def message_(self, ctx, *, message: str):
    guild_id = str(ctx.guild.id)
    if 'channel_id' not in self.leave_messages.get(guild_id, {}):
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: setup the goodbye channel first and then try again.",
          color=config.hex))
      return

    if self.leave_messages[guild_id].get('leave_message') == message:
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: same leave message is already saved in database for this server.",
          color=config.hex))
      return

    self.leave_messages[guild_id]['leave_message'] = message
    self.save_leave_messages()
    await ctx.send(embed=discord.Embed(
        description=
        f">>> {config.tick} {ctx.author.mention}: goodbye message has been saved and updated.",
        color=config.hex).add_field(name="Message", value=f"```{message}```"))

  @bye.command(name="disable", aliases=["remove", "delete","clear"],help="clears goobye msg database for guild.")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def disable_(self, ctx):
    guild_id = str(ctx.guild.id)
    if guild_id in self.leave_messages:
      del self.leave_messages[guild_id]
      self.save_leave_messages()
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.tick} {ctx.author.mention}: disabled goodbye module for this server.",
          color=config.hex))
    else:
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: goodbye module is not enabled for this server.",
          color=config.hex))

  @bye.command(name="setting", aliases=["config", "settings"],help="shows the configured goodbye setting for guild.")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def settings_(self, ctx):
    guild_id = str(ctx.guild.id)
    if guild_id not in self.leave_messages:
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: goodbye feature is not setup for this guild.",
          color=config.hex))
      return
    channel_id = self.leave_messages[guild_id].get(
        'channel_id')  # aisa karna samja
    leave_message = self.leave_messages[guild_id].get('leave_message')  # OK
    channel= None
    if channel_id:
      channel = self.bot.get_channel(channel_id)
    if channel == None:
      channel = "not found..."
    embed = discord.Embed(
        color=config.hex,
        description=
        f">>> Goodbye channel: {channel.mention}")
    if leave_message:
       embed.add_field(name="Message", value=f"```{leave_message}```")
    else:
      embed.add_field(name="Message", value=f"{config.error_emoji} Goodbye message is not setup.")
    embed.set_author(name="Goodbye Settings", icon_url=self.bot.user.avatar)
    await ctx.send(embed=embed)

  @bye.command(name="test", aliases=["check"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def test_(self, ctx):
    guild_id = str(ctx.guild.id)
    if guild_id not in self.leave_messages:
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: goodbye feature is not setup for this guild.",
          color=config.hex))
      return

    channel_id = self.leave_messages[guild_id].get('channel_id')
    leave_message = self.leave_messages[guild_id].get('leave_message')

    if not channel_id or not leave_message:
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: goodbye feature is not fully setup for this guild.",
          color=config.hex))
      return

    channel = self.bot.get_channel(channel_id)
    if not channel:
      await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: the configured goodbye channel is not accessible.",
          color=config.hex))
      return

    formatted_message = await self.guild(ctx.author, leave_message)
    await channel.send(formatted_message)
    await ctx.send(embed=discord.Embed(
        description=
        f"{config.tick} {ctx.author.mention}: the goodbye test message has been sent to the configured channel.",
        color=config.hex))

  @commands.Cog.listener()
  async def on_member_remove(self, member):
    guild_id = str(member.guild.id)
    if guild_id in self.leave_messages:
      channel_id = self.leave_messages[guild_id].get('channel_id')
      leave_message = self.leave_messages[guild_id].get('leave_message')
      if channel_id and leave_message:
        channel = self.bot.get_channel(channel_id)
        if channel:
          leave_message = await self.guild(member, leave_message)
          await channel.send(leave_message)

  async def guild(self, user, params):
    if "{user}" in params:
      params = params.replace("{user}", str(user))
    if "{user.mention}" in params:
      params = params.replace("{user.mention}", str(user.mention))
    if "{user.name}" in params:
      params = params.replace("{user.name}", str(user.name))
    if "{user.joined_at}" in params:
      params = params.replace("{user.joined_at}", discord.utils.format_dt(user.joined_at,style="R"))
    if "{user.discriminator}" in params:
      params = params.replace("{user.discriminator}", str(user.discriminator))
    if "{guild.name}" in params:
      params = params.replace("{guild.name}", str(user.guild.name))
    if "{guild.count}" in params:
      params = params.replace("{guild.count}", str(user.guild.member_count))
    if "{guild.id}" in params:
      params = params.replace("{guild.id}", str(user.guild.id))
    return params


async def setup(bot):
  await bot.add_cog(LeaveLogger(bot))
