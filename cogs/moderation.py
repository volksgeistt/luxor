import discord
from discord.ui import View, Button, select
from discord.ext import commands
import os
import datetime
import sys
import asyncio
from typing import Union, Optional
from config import config
from config.helper import colors
import json, requests
import aiohttp

def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed


class Moderation(commands.Cog):
  """Moderation commands which will
  help you to manage server"""

  def __init__(self,
               bot,
               help="Sends a list of usable commands for this server.",
               name="Moderation"):
    self.bot = bot
    self.client = bot
    self.help = help
    self.color = config.hex

  def convert(self, time):
    pus = ["s", "m", "h", "d"]
    time_dictx = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}
    uni = time[-1]
    if uni not in pus:
      return -1
    try:
      vl = int(time[:-1])
    except:
      return -2
    return vl * time_dictx[uni]

  @commands.command(name="lock", help="locks the channel in guild.")
  @commands.cooldown(1, 2, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def _lock(self, ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    try:
      overwrite = channel.overwrites_for(ctx.guild.default_role)
      overwrite.send_messages = False
      await channel.set_permissions(ctx.guild.default_role,overwrite=overwrite,reason=f"Channel locked by : {ctx.author}")
      await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully locked {channel.mention}"))
    except:
        await ctx.reply(embed=create_embed(f"	{config.error_emoji} {ctx.author.mention}: failed to lock {channel.mention}"))

  @commands.command(name="unlock", help="unlocks the channel in guild.")
  @commands.cooldown(1, 2, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def _unlock(self, ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await channel.set_permissions(ctx.guild.default_role,
                                  overwrite=overwrite,
                                  reason=f"Channel unlocked by : {ctx.author}")
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully unlocked {channel.mention}"
    ))
  @commands.command(name="hide", help="hides the channel in guild.")
  @commands.cooldown(1, 2, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def _hide(self, ctx, channel: discord.TextChannel = None):
    allowed = discord.AllowedMentions(everyone=False)
    channel = channel or ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.view_channel = False
    await channel.set_permissions(ctx.guild.default_role,
                                  overwrite=overwrite,
                                  reason=f"Channel hidden by : {ctx.author}")
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully hidden {channel.mention}"
    ))
    
  @commands.command(name="unhide", help="unhides the channel in guild.")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def _unhide(self, ctx, channel: discord.TextChannel = None):
    allowed = discord.AllowedMentions(everyone=False)
    channel = channel or ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.view_channel = True
    await channel.set_permissions(ctx.guild.default_role, 
                                  overwrite=overwrite,
                                  reason=f"Channel Unhidden By {ctx.author}")
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully unhidden {channel.mention}"
    ))

  @commands.command(name="mute", help="timeouts a member.")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(manage_roles=True)
  async def _mute(self, ctx, member: discord.Member, duration):
    idk = duration[:-1]
    tim = self.convert(duration)
    till = duration[-1]

    if tim == -1:
      await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: please enter a time duration ( eg: 10s, 10m, 10d )"
      ))
    elif tim == -2:
      await ctx.reply(embed=create_embed(
          f"{config.error_emoji}: sorry time duration can only be an integer value."
      ))
    else:
      if till.lower() == "d":
        t = datetime.timedelta(seconds=tim)
        msg = f"{config.tick} {ctx.author.mention}: successfully muted {member.mention} for `{idk}` day(s)"
      elif till.lower() == "m":
        t = datetime.timedelta(seconds=tim)
        msg = f"{config.tick} {ctx.author.mention}: successfully muted {member.mention} for `{idk}` minute(s)"
      elif till.lower() == "s":
        t = datetime.timedelta(seconds=tim)
        msg = f"{config.tick} {ctx.author.mention}: successfully muted {member.mention} for `{idk}` second(s)"
      elif till.lower() == "h":
        t = datetime.timedelta(seconds=tim)
        msg = f"{config.tick} {ctx.author.mention}: successfully muted {member.mention} for `{idk}` hour(s)"
    try:
      if member.guild_permissions.administrator:
        return await ctx.reply(embed=create_embed(
            f"{config.cross}  {ctx.author.mention}: you can't mute an admin"
        ))
      else:
        await member.timeout(discord.utils.utcnow() + t,
                             reason=f"muted by {ctx.author}")
      await ctx.reply(embed=create_embed(msg))

    except:
      await ctx.reply(f"{config.error_emoji} {ctx.author.mention}: failed to mute {member.mention}")

  @commands.command(name="unmute", help="removes timeout from a member.")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  @commands.has_permissions(manage_roles=True)
  async def _unmute(self, ctx, user: discord.Member):
    if user.is_timed_out():
      try:
        await user.edit(timed_out_until=None)
        await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully unmuted {user.mention}"))
      except Exception as e:
        await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: failed to unmute {user.mention}"))
    else:
      await ctx.reply(embed=create_embed(f"{config.cross} {ctx.author.mention}: {user.mention} is not muted"))

  @commands.hybrid_command(name="kick", help="kicks a member from guild.")
  @commands.has_permissions(kick_members=True)
  @commands.guild_only()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  async def _kick(self, ctx, member: discord.Member, *, reason=None):
    if ctx.author == ctx.guild.owner:
      if ctx.guild.me.top_role > member.top_role:
        try:
          await member.send(f"You have been kicked from {ctx.guild.name} , reason: {reason}")
          await member.kick(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully kicked {member.mention}"))
        except:
          await member.kick(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully kicked {member.mention}"))
      else:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: my highest role is below or equal to {member.mention}"))
    elif ctx.guild.me.top_role >= ctx.author.top_role:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: your role must be higher than me to use this command."))
        return
    elif member == ctx.author:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: dumb! you cannot kick yourself"))
    else:
      if ctx.guild.me.top_role > member.top_role:
        try:
          await member.send(f"You have been kicked from {ctx.guild.name} , reason: {reason}")
          await member.kick(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully kicked {member.mention}"))
        except:
          await member.kick(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully kicked {member.mention}"))
      else:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: my highest role is below or equal to {member.mention}"))

  @commands.hybrid_command(name="softban", help="softbans a member from the guild.")
  @commands.has_permissions(ban_members=True)
  @commands.guild_only()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  async def softban_(self, ctx, member: discord.Member, *, reason=None):
      if ctx.author == ctx.guild.owner:
          if ctx.guild.me.top_role > member.top_role:
              try:
                  await member.send(f"You have been banned from {ctx.guild.name}, reason: {reason}")
                  await member.ban(reason=f"Softbanned by {ctx.author} for {reason}")
                  await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully soft banned {member.mention}"))
              except:
                  await member.ban(reason=f"soft-banned  by {ctx.author} for {reason}")
                  await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully soft banned {member.mention}"))
          else:
              await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: my highest role is below or equal to {member.mention}"))
      elif ctx.guild.me.top_role >= ctx.author.top_role:
          await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: your role must be higher than mine to use this command."))
          return
      elif member == ctx.author:
          await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: you cannot soft-ban yourself."))
      else:
          if ctx.guild.me.top_role > member.top_role:
              try:
                  await member.send(f"you have been banned from {ctx.guild.name}, reason: {reason}")
                  await member.ban(reason=f"soft-banned by {ctx.author} for {reason}")
                  await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully soft-banned {member.mention}"))
              except:
                  await member.ban(reason=f"soft-banned by {ctx.author} for {reason}")
                  await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully soft-banned {member.mention}"))
          else:
              await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: my highest role is below or equal to {member.mention}."))

      async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
          if entry.target == member:
              await member.unban(reason=f"{self.bot.user.name} @ softban : immediately unbans a member after banning.")
              break

  

  @commands.hybrid_command(name="ban", help="bans a member from guild.")
  @commands.has_permissions(ban_members=True)
  @commands.guild_only()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  async def _ban(self, ctx, member: discord.Member, *, reason=None):
    if ctx.author == ctx.guild.owner:
      if ctx.guild.me.top_role > member.top_role:
        try:
          await member.send(f"you have been banned from {ctx.guild.name} , reason: {reason}")
          await member.ban(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully banned {member.mention}"))
        except:
          await member.ban(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully banned {member.mention}"))
      else:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: my highest role is below or equal to {member.mention}"))
    elif ctx.guild.me.top_role >= ctx.author.top_role:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: your role must be higher than me to use this command."))
        return
    elif member == ctx.author:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: dumb! you cannot ban yourself."))
    else:
      if ctx.guild.me.top_role > member.top_role:
        try:
          await member.send(f"you have been banned from {ctx.guild.name} , reason: {reason}")
          await member.ban(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully banned {member.mention}"))
        except:
          await member.ban(reason=f"by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully banned {member.mention}"))
      else:
        await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: my highest role is below or equal to {member.mention}."))

  @commands.hybrid_command(name="unban", help="Unbans a member")
  @commands.has_permissions(ban_members=True)
  @commands.guild_only()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  async def _unban(self, ctx, user: discord.User, *, reason=None):
      try:
          await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author} for {reason}")
          await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully unbanned {user.mention}"))
      except discord.NotFound:
          await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: the user {user.mention} is not banned."))
      except discord.Forbidden:
          await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: i don't have permission to unban users."))
      except discord.HTTPException as e:
          await ctx.send(embed=create_embed(f"{config.cross} {ctx.author.mention}: an error occurred: {e}"))
                     
  @commands.hybrid_command(name="unbanall", help="Unbans all members in the guild.")
  @commands.has_permissions(ban_members=True)
  @commands.guild_only()
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  async def _unbanall(self, ctx):
      async def btn_callback(interaction: discord.Interaction):
          if interaction.user == ctx.author:
              guild = interaction.guild
              if guild.me.guild_permissions.ban_members:
                  await interaction.response.edit_message(embed=create_embed(f"{config.tick} {ctx.author.mention}: unbanning all banned members.."), view=None)
                  count = 0
                  async for i in guild.bans():
                      await guild.unban(i.user, reason=f"unbanned all by {ctx.author}")
                      count += 1
                  await interaction.followup.send(f"{config.tick} {ctx.author.mention}: successfully unbanned {count}  members.!")
              else:
                  await interaction.response.send_message(content=f"{config.cross} {ctx.author.mention}: bot is missing permissions to unban members")
          else:
              await interaction.response.send_message(content=f"{config.cross} {ctx.author.mention}: you are not the author of this interaction")

      async def btn1_callback(interaction: discord.Interaction):
          if interaction.user == ctx.author:
              await interaction.response.edit_message(content=f"{config.tick} {ctx.author.mention}: cancelled", view=None)
          else:
              await interaction.response.send_message(content=f"{config.cross} {ctx.author.mention}: you are not the author of this interaction")

      embed = discord.Embed(color=config.hex, description="Are you sure you want to unban all members?")
      view = discord.ui.View()
      btn = discord.ui.Button(style=discord.ButtonStyle.green, label="Confirm")
      btn1 = discord.ui.Button(style=discord.ButtonStyle.red, label="Cancel")
      btn.callback = btn_callback
      btn1.callback = btn1_callback
      view.add_item(btn)
      view.add_item(btn1)
      await ctx.send(embed=embed, view=view)

  @commands.command(
    aliases = ['nickname', 'nickn', 'nic', 'rename', 'setnick'],
    help = "Change a specified users nickname in the server")
  @commands.has_permissions(manage_nicknames=True)
  @commands.guild_only()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def nick(self, ctx, member: discord.Member=None, *, nickname):
    if member == None:
        member == ctx.author
    if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you can only change nicknames below your top role", color=config.hex))
    else:
        await member.edit(nick=nickname)
        embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: successfully changed {member.mention}'s nickname.",color=config.hex)
        await ctx.send(embed=embed)

  
  @commands.command(name="edithex", aliases=["editcolor"],help="edits color of a role using hex code (#) or color name (if available)")
  @commands.guild_only()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def edithex_(self, ctx, role: discord.Role, color: str):
      if not ctx.author.guild_permissions.manage_roles:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you don't have permission to manage roles.",color=config.hex))
          return
      if color.lower() in colors:
          hex_code = colors[color.lower()]
      else:
          if not (color.startswith("#") and len(color) == 7 and all(c in "0123456789ABCDEFabcdef" for c in color[1:])):
              await ctx.send(embed=discord.Embed(f"{config.error_emoji} {ctx.author.mention}: the hex code you have provided is invalid.\n{config.ques_emoji} **Format:** `#318FF3`",color=config.hex))
              return
          hex_code = color
      try:
          await role.edit(color=discord.Color(int(hex_code.lstrip("#"), 16)))
          await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: changed the hex of {role.mention} to {color}",color=config.hex))
      except discord.Forbidden:
        await ctx.send(embed=discord.Embed(f"{config.error_emoji} {ctx.author.mention}: i don't have permissions to edit role in your guild.",color=config.hex))
      except discord.HTTPException:
        await ctx.send(embed=discord.Embed(f"{config.error_emoji} {ctx.author.mention}: failed to udpate hex code.",color=config.hex))

  @commands.command(name="steal", aliases=['addemoji'], help="steal emojis from other servers")
  @commands.has_permissions(manage_emojis=True)
  async def steal_(self, ctx, emoji: discord.PartialEmoji, name=None):
    namee = name or "stolen_emoji"
    try:
      
      response = requests.get(emoji.url)
      emoi = await ctx.guild.create_custom_emoji(name=namee,
                                                 image=response.content)
      await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully stolen {emoi}"))
    except:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: failed to steal emoji"))
      
  @commands.command(aliases=["giverole","gr", "addr"], help="give role to members")
  @commands.has_permissions(manage_roles=True)
  @commands.guild_only()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def addrole(self, ctx, member: discord.Member, role: discord.Role):
    auth = ctx.author
    own = ctx.guild.owner
    if auth.top_role.position <= member.top_role.position and own.id != auth.id:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you can only give role to members below you"))
    elif auth.top_role.position <= ctx.guild.me.top_role.position and auth.id != own.id:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: your top role should be above my top role"))
    elif auth.id == member.id:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you can not give role to yourself"))
                      
    elif member.top_role.position >= ctx.guild.me.top_role.position:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: my top role should be above member's role"))
    else:
      try:
        await member.add_roles(role, reason=f"role given by {ctx.author}")
        await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully given {role.mention} to {member.mention}"))
      except:
        await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: failed to give role"))

  @commands.command(aliases=["r"], help="Add or remove a role from a member")
  @commands.has_permissions(manage_roles=True)
  @commands.guild_only()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def role(self, ctx, member: discord.Member, role: discord.Role):
   auth = ctx.author
   own = ctx.guild.owner
  
   if auth.top_role.position <= member.top_role.position and own.id != auth.id:
    await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: You can only modify roles of members below you"))
    return
  
   if auth.top_role.position <= ctx.guild.me.top_role.position and auth.id != own.id:
    await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: Your top role should be above my top role"))
    return
  
   if auth.id == member.id:
    await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: You cannot modify your own roles"))
    return
  
   if member.top_role.position >= ctx.guild.me.top_role.position:
    await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: My top role should be above the member's role"))
    return
  
   try:
    if role in member.roles:
     await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
     await ctx.reply(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed {role.mention} from {member.mention}", color=config.hex))
    else:
     await member.add_roles(role, reason=f"Role added by {ctx.author}")
     await ctx.reply(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added {role.mention} to {member.mention}", color=config.hex))
   except discord.Forbidden:
    await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: I don't have permission to modify this role"))
   except discord.HTTPException:
    await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: Failed to modify role due to a network error"))
   except Exception as e:
    await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: An unexpected error occurred: {str(e)}"))

  def create_embed(self, description):
   return discord.Embed(description=description, color=config.hex)


  @commands.command(aliases=["takerole","tr", "remover"], help="remove role from members")
  @commands.has_permissions(manage_roles=True)
  @commands.guild_only()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def removerole(self, ctx, member: discord.Member, role: discord.Role):
    auth = ctx.author
    own = ctx.guild.owner
    if auth.top_role.position <= member.top_role.position and own.id != auth.id:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you can only give role to members below you"))
    elif auth.top_role.position <= ctx.guild.me.top_role.position and auth.id != own.id:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: your top role should be above my top role"))
    elif auth.id == member.id:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you can not give role to yourself"))

    elif member.top_role.position >= ctx.guild.me.top_role.position:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: my top role should be above member's role"))
    else:
      try:
        await member.remove_roles(role, reason=f"role removed by {ctx.author}")
        await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully removed {role.mention} from {member.mention}"))
      except:
        await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: failed to remove role"))

  @commands.group(name="purge", aliases=['clear'], help="purge messages", invoke_without_command=True)
  @commands.has_permissions(manage_messages=True)
  @commands.guild_only()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def purge_grp(self, ctx, amount:int):
      if int(amount) > 1000 or int(amount) < 1:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: amount should be between 1-1000"))
        
      deleted = await ctx.channel.purge(limit=amount)
      await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully purged {len(deleted)} messages"))

  @purge_grp.command(name="bots", help=f"purge bot messages")
  @commands.has_permissions(manage_messages=True)
  @commands.guild_only()
  async def purge_bots(self, ctx, amount:int):
      if amount > 1000 or amount < 1:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: amount should be between 1-1000"))

      deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.author.bot)
      await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: succesfully purged {len(deleted)} messages"))
    
  @purge_grp.command(name="humans", help=f"purge human messages")
  @commands.has_permissions(manage_messages=True)
  @commands.guild_only()
  async def purge_humans(self, ctx, amount:int):
      if amount > 1000 or amount < 1:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: amount should be between 1-1000"))

      deleted = await ctx.channel.purge(limit=amount, check=lambda m: not m.author.bot)
      await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: succesfully purged {len(deleted)} messages"))
    
  @purge_grp.command(name="embeds", help=f"purge embed messages")
  @commands.has_permissions(manage_messages=True)
  @commands.guild_only()
  async def purge_embeds(self, ctx, amount:int):
      if amount > 1000 or amount < 1:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: amount should be between 1-1000"))

      deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.embeds)
      await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: succesfully purged {len(deleted)} messages"))
    
      
  @purge_grp.command(name="files", help=f"purge file messages")
  @commands.has_permissions(manage_messages=True)
  @commands.guild_only()
  async def purge_files(self, ctx, amount:int):
      if amount > 1000 or amount < 1:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: amount should be between 1-1000"))

      deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.attachments)
      await ctx.send(embed=create_embed(f"{config.tick} {ctx.author.mention}: succesfully purged {len(deleted)} messages"))

  @commands.command(name="roleicon", aliases=['ricon'], help="change icon of a role")
  @commands.has_permissions(manage_roles=True)
  @commands.guild_only()
  async def roleicon(self, ctx, role: discord.Role, icon:discord.PartialEmoji):
    try:
      icon_url = requests.get(icon.url).content
      await role.edit(display_icon=icon_url, reason=f"role icon changed by {ctx.author}")
      await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: succssfully changed role icon of {role.mention}"))
    except:
      await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: failed to change role icon"))

  @commands.command(name="lockall", help="Locks all the channels in the guild.")
  @commands.has_permissions(manage_channels=True)
  async def lockall_(self, ctx):
      x = await ctx.send(embed=discord.Embed(description=f"{config.utility} {ctx.author.mention}: locking down all channels.",color=config.hex))
      for channel in ctx.guild.channels:
          if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
              await channel.set_permissions(ctx.guild.default_role, send_messages=False)
      await x.edit(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: locked down all channels available in the guild.",color=config.hex))

  @commands.command(name="unlockall", help="unlocks all the channels in the guild.")
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def unlockall_(self, ctx):
      y = await ctx.send(embed=discord.Embed(description=f"{config.utility} {ctx.author.mention}: unlocking all channels.",color=config.hex))
      for channel in ctx.guild.channels:
          if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
              await channel.set_permissions(ctx.guild.default_role, send_messages=True)
      await y.edit(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: unlocked all channels available in the guild.",color=config.hex))

  @commands.command(name="hideall", help="hides all the channels in the guild.")
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def hideall_(self, ctx):
      y = await ctx.send(embed=discord.Embed(description=f"{config.utility} {ctx.author.mention}: hiding all channels.",color=config.hex))
      for channel in ctx.guild.channels:
          if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
              await channel.set_permissions(ctx.guild.default_role, view_channel=False)
      await y.edit(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: all channels available in the guild are hidden.",color=config.hex))

  @commands.command(name="unhideall", help="unhides all the channels in the guild.")
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def unhideall_(self, ctx):
      y = await ctx.send(embed=discord.Embed(description=f"{config.utility} {ctx.author.mention}: unhiding all channels.",color=config.hex))
      for channel in ctx.guild.channels:
          if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
              await channel.set_permissions(ctx.guild.default_role, view_channel=True)
      await y.edit(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: all channels available in the guild are visible.",color=config.hex))

  @commands.command(name="sneaky", help="enables NSFW in channel")
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def sneaky(self, ctx, channel: discord.TextChannel = None):
      channel = channel or ctx.channel
      if ctx.guild and not channel.is_nsfw():
          await channel.edit(nsfw=True)
          await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: enabled NSFW in {channel.mention}",color=config.hex))
      else:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: NSFW is already enabled in {channel.mention}",color=config.hex))

  @commands.command(name="unsneaky", help="disables NSFW in channel")
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def unsneaky(self, ctx, channel: discord.TextChannel = None):
      channel = channel or ctx.channel
      if ctx.guild and channel.is_nsfw():
          await channel.edit(nsfw=False)
          await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: disabled NSFW in {channel.mention}",color=config.hex))
      else:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: NSFW is not enabled in {channel.mention}",color=config.hex))

    
        
async def setup(bot):
  await bot.add_cog(Moderation(bot))
