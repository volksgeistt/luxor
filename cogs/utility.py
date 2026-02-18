import discord
from discord.ui import View, Button
from discord.ext import commands
from discord.ext.commands import Cog, Context
from reactionmenu import ViewMenu, ViewButton
import os, io
import sys
from pytube import YouTube
import asyncio, json
import helper as util
import re
from typing import Union
from config import config
import json
from tempfile import TemporaryDirectory

def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed


class Utility(Cog):

  def __init__(self, bot):
    self.bot = bot
    self.client = bot
    self.color = config.hex
    self.snipedxd = {"s1": {}}
    self.esnipedxd = {"s1": {}}
    self.tasks = []

  

  @Cog.listener()
  async def on_message_delete(self, message) -> None:
    author = message.author
    if author.bot:
      return
    content = message.content
    guild = message.guild
    channel = message.channel
    deleted_at = discord.utils.format_dt(discord.utils.utcnow())
    if not content is None:
      self.snipedxd["s1"][str(guild.id)] = {}
      self.snipedxd["s1"][str(guild.id)]["content"] = content
      self.snipedxd["s1"][str(guild.id)]["author"] = str(author.id)
      self.snipedxd["s1"][str(guild.id)]["channel"] = str(channel.id)
      self.snipedxd["s1"][str(guild.id)]["delete_at"] = deleted_at

  @Cog.listener()
  async def on_message_edit(self, before, after) -> None:
    message = after
    author = message.author
    if author.bot:
      return
    content = message.content
    guild = message.guild
    channel = message.channel
    edit_at = discord.utils.format_dt(message.edited_at)
    if not content is None:
      self.esnipedxd["s1"][str(guild.id)] = {}
      self.esnipedxd["s1"][str(guild.id)]["acontent"] = content
      self.esnipedxd["s1"][str(guild.id)]["bcontent"] = before.content
      self.esnipedxd["s1"][str(guild.id)]["author"] = str(author.id)
      self.esnipedxd["s1"][str(guild.id)]["channel"] = str(channel.id)
      self.esnipedxd["s1"][str(guild.id)]["edit_at"] = edit_at

  @commands.command(name="snipe", help="snipes last deleted message")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_messages=True)
  async def snipe(self, ctx: Context):
    guild = ctx.guild
    s = str(guild.id)
    try:
      l = self.snipedxd["s1"][s]["content"]
    except KeyError:
      await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: there's nothing to snipe!"
      ))
      return
    else:
      data = self.snipedxd["s1"][s]
      author = await ctx.bot.fetch_user(int(data["author"]))
      content = data["content"]
      channel = guild.get_channel(int(data["channel"]))
      delxd = data['delete_at']
      embed = discord.Embed(
          color=self.color,
          description=
          f"> {config.arrow_emoji} Message sent by {author.mention} deleted in {channel.mention} at {delxd}\n\n**Content:**\n{content}"
      )
      embed.set_footer(text=f"Requested by {ctx.author}",
                       icon_url=ctx.author.avatar)
      await ctx.reply(embed=embed)

  @commands.command(name="esnipe",
                    help="snipes last edited message",
                    aliases=["editsnipe", "edit-snipe"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_messages=True)
  async def editsnipe(self, ctx: Context):
    guild = ctx.guild
    s = str(guild.id)
    try:
      self.esnipedxd["s1"][s]["acontent"]
    except KeyError:
      await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: there's nothing to snipe!"
      ))
      return
    data = self.esnipedxd["s1"][s]
    ac = data["acontent"]
    bc = data["bcontent"]
    us = await ctx.bot.fetch_user(int(data["author"]))
    cn = ctx.guild.get_channel(int(data["channel"]))
    edit = data["edit_at"]
    embed = discord.Embed(
        description=
        f"> {config.arrow_emoji} Message sent by {us.mention} edited at {edit}\n\n**Before:** {bc}\n**After:** {ac}",
        color=self.color)
    embed.set_footer(text=f"Requested by {ctx.author}",
                     icon_url=ctx.author.avatar)
    await ctx.send(embed=embed)
            
  @commands.command(name="ping", help="pings the bot")
  async def ping(self, ctx: Context):
    await ctx.reply(embed=create_embed(
        f"{config.config_emoji} {self.bot.user.mention}: `{round(self.bot.latency * 1000)}ms`"
    ))

  @commands.command(name="nuke",
                    aliases=["clone"],
                    help="clones a channel and deletes the older one")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_channels=True)
  async def _nooooook(self, ctx, channel: discord.TextChannel = None):
    if ctx.guild.me.top_role.position >= ctx.message.author.top_role.position and ctx.message.author.id != ctx.guild.owner.id:
      await ctx.reply(embed=discord.Embed(description=f"{config.cross} {ctx.author.mention}: you must have role above me to use this command.",color=config.hex))
      return
    msg4 = None
    chan = channel or ctx.channel
    if chan == ctx.guild.rules_channel or chan == ctx.guild.public_updates_channel or chan == ctx.guild.system_channel:
      await ctx.reply(
          f"{config.error_emoji} {ctx.author.mention}: cannot delete a channel required for community servers."
      )
      return
    button1 = Button(label="Confirm", style=discord.ButtonStyle.green)
    button2 = Button(label="Cancel", style=discord.ButtonStyle.red)
    view = View(timeout=60)
    wk = "this channel" if chan == ctx.channel else f'{chan.mention}'
    embed = discord.Embed(
        description=
        f"{config.error_emoji} {ctx.author.mention}: are you sure you want to clone {wk}",
        color=config.hex)

    async def button_callback1(interaction):
      if interaction.user.id == ctx.message.author.id:
        pos = chan.position
        view.stop()
        await msg4.delete()
        chann = await chan.clone(
            reason=f"{self.bot.user.name} @ clone channel command used by {interaction.user}")
        await chan.delete(
            reason=f"{self.bot.user.name} @ clone channel command used by {interaction.user}")
        await chann.edit(position=pos)
      else:
        await interaction.response.send_message(f"This is not for you.",
                                                ephemeral=True)

    async def button_cl(interaction):
      if interaction.user.id == ctx.author.id:
        if chan == ctx.channel:
          v = "this channel"
        else:
          v = f"{chan.mention} channel"
        await ctx.send(
            f"{config.cross} {interaction.user.mention}: okay i will not clone {v}"
        )
        view.stop()
        await msg4.delete()
      else:
        await interaction.response.send_message("This is not for you.",
                                                ephemeral=True)

    button1.callback = button_callback1
    button2.callback = button_cl
    view.add_item(button1)
    view.add_item(button2)

    async def on_tm():
      view.stop()
      await msg4.delete()
      if chan == ctx.channel:
        vv = "this channel"
      else:
        vv = f'{chan.mention} channel'
      await ctx.send(
          f"{config.cross} {ctx.user.mention}: okay i will not clone {vv}.")

    view.on_timeout = on_tm
    msg4 = await ctx.reply(embed=embed, mention_author=False, view=view)

  @commands.command(name="roleinfo",
                    aliases=["ri"],
                    help=f"shows info about a role")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def roleinfo(self, ctx: Context, *, role: discord.Role):
    embed = discord.Embed(color=self.color)
    embed.set_author(name=f"{role.name}", icon_url=ctx.bot.user.avatar)

    embed.add_field(name="Id", value=f"`{role.id}`")
    embed.add_field(name="Hex Code", value=f"`{role.color}`")
    embed.add_field(name="Position", value=f"`{role.position}`")
    embed.add_field(name="Created at",
                    value=f"{discord.utils.format_dt(role.created_at)}")
    if len(role.members) > 10:
      member_str = f"{config.error_emoji} too many members to show"
      embed.add_field(name=f"Members ({len(role.members)})", value=member_str)
    elif len(role.members) < 10 and len(role.members) != 0:
      members_str = " ".join([f"{member}" for member in role.members])
      embed.add_field(name=f"Members ({len(role.members)})", value=members_str)

    embed.set_footer(text=f"Requested by {ctx.author}",
                     icon_url=ctx.author.avatar)
    await ctx.send(embed=embed)

  @commands.command(aliases=["mc", "members"], help="shows the member count")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def membercount(self, ctx):
    bots_count = sum(1 for member in ctx.guild.members if member.bot)
    humans_count = ctx.guild.member_count - bots_count

    embed = discord.Embed(
        color=config.hex,
        description=
        f"`{len(ctx.guild.members)}` members `({humans_count} humans & {bots_count} bots)`"
    )
    embed.set_author(name=f"{ctx.guild.name}", icon_url=ctx.guild.icon)
    await ctx.send(embed=embed)

  @commands.command(name="userinfo",
                    aliases=["ui"],
                    help="shows info about a user")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def userinfo(self, ctx: Context, *, member: discord.User = None):
    user = member if member else ctx.author
    guild = ctx.guild
    us = await ctx.bot.fetch_user(user.id)
    gl = guild.get_member(user.id)
    badges = ""
    if int(us.public_flags.value) == 0:
      badges += "None"
    else:
      for w in us.public_flags:
        badgexd = w[0]
        badgexdvalue = w[1]
        if badgexdvalue:
          badges += f"{badgexd.replace('_', ' ')}"
          badges += ", "
      badges.strip(",")

    embed = discord.Embed(
        color=self.color,
        description=f">>> Created: {discord.utils.format_dt(us.created_at)}")
    embed.set_author(name=f"{us.name}", icon_url=us.avatar)
    embed.set_thumbnail(url=us.avatar)
    embed.add_field(name="ID", value=f"{us.id}")
    embed.add_field(name="Badges", value=f"{badges.rsplit(',', 1)[0]}")
    if us.banner:
      embed.set_image(url=us.banner.url)
    if gl == None:
      embed.set_footer(text=f"{us.name} is not in this server.",
                       icon_url=ctx.message.author.avatar)
    else:
      embed.description += f"\nJoined: {discord.utils.format_dt(gl.joined_at)}"
      rlsxd = ""
      if len(gl.roles) > 10:
        rlsxd += f"{config.error_emoji} too many roles to show"
      else:
        for role in gl.roles:
          if not role.id == guild.default_role.id:
            rlsxd += f"{role.mention}, "
        rlsxd.strip(",")
      if rlsxd == "":
        rlsxd += "None"

      embed.add_field(name="Roles", value=f"{rlsxd.rsplit(',', 1)[0]}")

      vlue = ""
      if gl == guild.owner:
        vlue += "Server Owner"
      if gl.bot:
        vlue += "Server Bot"
      if gl.guild_permissions.administrator:
        if vlue == "":
          vlue += 'Server Administrator'
      if gl.guild_permissions.manage_channels or gl.guild_permissions.manage_roles or gl.guild_permissions.kick_members or gl.guild_permissions.ban_members or gl.guild_permissions.manage_guild or gl.guild_permissions.manage_messages:
        if vlue == "":
          vlue += "Server Moderator"
      if vlue == "":
        vlue += "Server Member"
      embed.add_field(name="Acknowledgements", value=vlue)
      embed.set_footer(text=f"Requested by {ctx.author}",
                       icon_url=ctx.author.avatar)
      if us.banner:
        embed.set_image(url=us.banner.url)
    await ctx.send(embed=embed)

  @commands.command(name="serverinfo",
                    aliases=["si"],
                    help=f"shows info about the server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def serverinfo(self, ctx):
    guild = ctx.guild
    bstc = guild.premium_subscription_count
    totalm = guild.member_count
    totalhb = sum(1 for member in guild.members if not member.bot)
    totalh = totalm - totalhb
    embed = discord.Embed(color=config.hex,
                          description=f'''>>> {guild.description or None}
''')
    embed.set_thumbnail(url=guild.icon)
    embed.set_author(name=ctx.guild.name, icon_url=guild.icon)
    embed.add_field(name="Owner", value=f"{guild.owner} `({guild.owner.id})`")
    embed.add_field(name="Created at",
                    value=f"{discord.utils.format_dt(guild.created_at)}")
    embed.add_field(name="Boosts", value=bstc)
    embed.add_field(
        name="Members",
        value=f"Total: {totalm}\nHumans: {totalhb}\nBots: {totalh}")
    embed.add_field(
        name=f"Channels",
        value=
        f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)} \nCatogories: {len(guild.categories)}"
    )
    embed.add_field(
        name="Count",
        value=
        f"Emoji: {len(guild.emojis)}\nStickers: {len(guild.stickers)} \nRoles: {len(guild.roles)}"
    )
    embed.set_footer(text=f"ID: {guild.id}", icon_url=ctx.author.avatar)
    await ctx.send(embed=embed)


  @commands.command(name="servericon",
                    aliases=["icon", "sicon"],
                    help=f"shows the server icon")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def servericon(self, ctx):
    g = self.bot.get_guild(ctx.guild.id)

    if g.icon is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: this server doesn't have an icon"
      ))

    embed = discord.Embed(color=config.hex)
    embed.set_author(name=f"{g.name}", icon_url=g.icon, url=g.icon.url)
    embed.set_image(url=g.icon)
    await ctx.reply(embed=embed)

  @commands.command(name="avatar",
                    aliases=["av"],
                    help=f"shows the avatar of a user")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def avatar(self, ctx, *, member: discord.User = None):
    user = member if member else ctx.author
    u = await self.bot.fetch_user(user.id)

    if u.avatar is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: this user doesn't have an avatar"
      ))

    embed = discord.Embed(color=config.hex)
    embed.set_author(name=f"{u.name}", icon_url=u.avatar, url=u.avatar.url)
    embed.set_image(url=u.avatar)
    await ctx.reply(embed=embed)

  @commands.command(name="banner", help=f"shows the banner of a user")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def banner(self, ctx, *, member: discord.User = None):
    user = member if member else ctx.author
    u = await self.bot.fetch_user(user.id)

    if u.banner is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: this user doesn't have a banner"
      ))

    embed = discord.Embed(color=config.hex)
    embed.set_author(name=f"{u.name}", icon_url=u.avatar, url=u.banner.url)
    embed.set_image(url=u.banner)
    await ctx.reply(embed=embed)

  @commands.command(name="serverbanner", help="shows the banner of the server", aliases=['sbanner'])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def serverbanner(self, ctx):
    g = self.bot.get_guild(ctx.guild.id)

    if g.banner is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: this server doesn't have a banner"
      ))

    embed = discord.Embed(color=config.hex)
    embed.set_author(name=f"{g.name}", icon_url=g.banner, url=g.banner.url)
    embed.set_image(url=g.banner)
    await ctx.reply(embed=embed)


  @commands.command(name="downloadyt", aliases=["ytdl"], help="download a youtube video")
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def downloadyt(self, ctx, url: str):
    if not url.startswith("https://youtu.be/"):
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: please provide a valid youtube url"
      ))
    msg = await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: downloading your video"
    ))
    video = YouTube(url)
    stream = video.streams.get_highest_resolution()
    with TemporaryDirectory() as d:
      fn = stream.download(output_path=d)
      with open(fn, 'rb') as f:
          await msg.reply(file=discord.File(f))

  @commands.command(name="enlarge", aliases=["enl"], help="enlarge an emoji")
  async def enlarge(self, ctx, emoji: discord.PartialEmoji):
    em = create_embed(None)
    em.set_image(url=emoji.url)
    em.set_author(name=f"{emoji.name}", icon_url=emoji.url)
    await ctx.reply(embed=em)

  
  @commands.group(name="list", invoke_without_command=True)
  async def jija(self, ctx):
    embed = discord.Embed(
        title="List Subcommands:",
        description=
        f">>> `list boosters`, `list bans`, `list roles`, `list joinposition`, `list norole`, `list emojis`, `list bots`, `list admins`, `list mods`, `list early`, `list activedev`, `list botdev`\n{config.ques_emoji} Example: `,list admin`",
        color=config.hex)
    await ctx.send(embed=embed)

  @jija.command(name="boost",
                aliases=["boosters", "booster", "boosted", "boosts"],
                description="see a list of boosters in the server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def seggs(self, ctx):
    l = []
    ok = {}
    for member in ctx.guild.premium_subscribers:
      wz = sum(m.premium_since < member.premium_since
               for m in ctx.guild.premium_subscribers
               if m.premium_since is not None)
      ok[str(wz)] = str(member.id)
    for i in range(len(ctx.guild.premium_subscribers)):
      sure = ok.get(str(i))
      l.append(ctx.guild.get_member(int(sure)))
    if l == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no boosters found in the server",
          color=config.hex))

    await boost_lis(
        ctx=ctx,
        listxd=l,
        color=config.hex,
        title=f"List of Server Boosters")

  @jija.command(name="joinpos", aliases=["joinposi", "joinposition"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def list_joinpos(self, ctx):

    l = []
    ok = {}
    for member in ctx.guild.members:
      wz = sum(m.joined_at < member.joined_at for m in ctx.guild.members
               if m.joined_at is not None)
      ok[str(wz)] = str(member.id)
    for i in range(len(ctx.guild.members)):
      sure = ok.get(str(i))
      l.append(ctx.guild.get_member(int(sure)))
    await working_lister(ctx=ctx,
                         listxd=l,
                         color=config.hex,
                         title=f"List of Join Position")

  @jija.command(name="norodsdales", aliases=["noradasdoless", "norsadasdole"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def seggasdsss(self, ctx):

    l = []
    for member in ctx.guild.members:
      if len(member.roles) == 0:
        l.append(member)
    if l == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no user found in server without any role",
          color=config.hex))

    await working_lister(ctx=ctx,
                         listxd=l,
                         color=config.hex,
                         title=f"List of No Role")

  @jija.command(name="emojis", aliases=["emo", "emoji"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def listemojis(self, ctx):
    a = len(ctx.guild.emojis)
    l = []
    await working_listerr(ctx=ctx,
                          listxd=ctx.guild.emojis,
                          color=config.hex,
                          title=f"List of Emojis")

  @jija.command(name="bots",
                aliases=["bot"],
                description="Get a list of all bots in a server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def listbots(self, ctx):
    loda = []
    for member in ctx.guild.members:
      if member.bot:
        loda.append(member)
    if loda == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no bots found in the server",
          color=config.hex))

    await working_lister(listxd=loda,
                         color=config.hex,
                         title=f"List of Bots",
                         ctx=ctx)

  @jija.command(name="admins",
                aliases=["admin", "administrator", "administration"],
                description="Get a list of all admins of a server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def listadmins(self, ctx):
    loda = []
    for member in ctx.guild.members:
      if member.guild_permissions.administrator:
        loda.append(member)
    if loda == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no admins found in the server.",
          color=config.hex))

    await working_lister(listxd=loda,
                         color=config.hex,
                         title=f"List of Admins",
                         ctx=ctx)

  @jija.command(name="mods",
                aliases=["mod", "moderator"],
                description="Get a list of all mods of a server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def listmods(self, ctx):
    loda = []
    for member in ctx.guild.members:
      if member.guild_permissions.manage_guild or member.guild_permissions.manage_messages or member.guild_permissions.manage_channels or member.guild_permissions.manage_nicknames or member.guild_permissions.manage_roles or member.guild_permissions.manage_emojis_and_stickers or member.guild_permissions.manage_emojis or member.guild_permissions.moderate_members:
        if not member.guild_permissions.administrator:
          loda.append(member)
    if loda == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no mods found in the server ( admins excluded )",
          color=config.hex))

    await working_lister(listxd=loda,
                         color=config.hex,
                         title=f"List of Moderators",
                         ctx=ctx)

  @jija.command(name="early",
                aliases=["earlybadge", "earlysupporter"],
                description="Get a list of early id in a server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def listearly(self, ctx):
    loda = []
    for member in ctx.guild.members:
      if member.public_flags.early_supporter:
        loda.append(member)
    if loda == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no user with early supporter found in the server",
          color=config.hex))

    await working_lister(listxd=loda,
                         color=config.hex,
                         title=f"List of Early Supporters",
                         ctx=ctx)

  @jija.command(name="active-dev",
                aliases=["activedev", "activedeveloper"],
                description="Get a list of early id in a server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def activedev(self, ctx):
    loda = []
    for member in ctx.guild.members:
      if member.public_flags.active_developer:
        loda.append(member)
    if loda == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no early developer found in the server.",
          color=config.hex))

    await working_lister(listxd=loda,
                         color=config.hex,
                         title=f"List of Active Developers",
                         ctx=ctx)

  @jija.command(name="botdev",
                aliases=["developer", "botdeveloper"],
                description="Get a list of bot developer in a server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def botdev(self, ctx):
    loda = []
    for member in ctx.guild.members:
      if member.public_flags.early_verified_bot_developer:
        loda.append(member)
    if loda == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no bot developer badge found in the server",
          color=config.hex))

    await working_lister(listxd=loda,
                         color=config.hex,
                         title=f"List of Bot Developers",
                         ctx=ctx)

  @jija.command(
      name="inrole",
      aliases=["inside-role"],
      description="See a list of members that are in the seperate role")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def list_inrole(self, ctx, role: discord.Role):
    l = list(role.members)
    await working_lister(ctx=ctx,
                         listxd=l,
                         color=config.hex,
                         title=f"List of Members In {role.name}")

  @jija.command(name="bans",
                aliases=["ban"],
                description="See a list of banned user")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def list_bans(self, ctx):
    ok = []
    async for idk in ctx.guild.bans(limit=None):
      ok.append(idk)
    if ok == []:
      return await ctx.send(embed=discord.Embed(
          description=
          f"{config.error_emoji} {ctx.author.mention}: no banned users found in the server.",
          color=config.hex))

    await lister_bn(ctx=ctx,
                    listxd=ok,
                    color=config.hex,
                    title=f"List of Banned Members")

  @jija.command(name="roles",
                aliases=["role"],
                description="See a list of roles in the server")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def list_roles(self, ctx):
    l = [r for r in ctx.guild.roles if not r.id == ctx.guild.default_role.id]
    l.reverse()
    await rolis(ctx=ctx, listxd=l, color=config.hex, title=f"List of Roles")


async def boost_lis(ctx, color, listxd, *, title):
  embed_array = []
  t = title
  clr = color
  sent = []
  your_list = listxd
  count = 0
  embed = discord.Embed(color=clr, description="", title=t)
  embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(listxd) > 1:
    for i in range(len(listxd)):
      for i__ in range(10):
        if not your_list[i].id in sent:
          count += 1
          if str(count).endswith("0") or len(str(count)) != 1:
            actualcount = str(count)
          else:
            actualcount = f"0{count}"
          embed.description += f"`{actualcount}` {your_list[i]} ({your_list[i].mention}) : <t:{round(your_list[i].premium_since.timestamp())}:R>\n"
          sent.append(your_list[i].id)
      if str(count).endswith("0") or str(count) == str(len(your_list)):
        embed_array.append(embed)
        embed = discord.Embed(color=clr, description="", title=t)
        embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(embed_array) == 0:
    embed_array.append(embed)
  pag = PaginationViewWallah(embed_array, ctx)
  if len(embed_array) == 1:
    await pag.start(ctx, True)
  else:
    await pag.start(ctx)


async def boost_liss(ctx, color, listxd, *, title):
  embed_array = []
  t = title
  clr = color
  sent = []
  your_list = listxd
  count = 0
  embed = discord.Embed(color=clr, description="", title=t)
  embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(listxd) > 1:
    for i in range(len(listxd)):
      for i__ in range(10):
        if not your_list[i].id in sent:
          count += 1
          if str(count).endswith("0") or len(str(count)) != 1:
            actualcount = str(count)
          else:
            actualcount = f"0{count}"
          embed.description += f"`{actualcount}` {your_list} `lnd`\n"
          sent.append(your_list[i].id)
      if str(count).endswith("0") or str(count) == str(len(your_list)):
        embed_array.append(embed)
        embed = discord.Embed(color=clr, description="", title=t)
        embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(embed_array) == 0:
    embed_array.append(embed)
  pag = PaginationViewWallah(embed_array, ctx)
  if len(embed_array) == 1:
    await pag.start(ctx, True)
  else:
    await pag.start(ctx)


async def rolis(ctx, color, listxd, *, title):
  embed_array = []
  t = title
  clr = color
  sent = []
  your_list = listxd
  count = 0
  embed = discord.Embed(color=clr, description="", title=t)
  embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(listxd) > 1:
    for i in range(len(listxd)):
      for i__ in range(10):
        if not your_list[i].id in sent:
          count += 1
          if str(count).endswith("0") or len(str(count)) != 1:
            actualcount = str(count)
          else:
            actualcount = f"0{count}"
          embed.description += f"`{actualcount}` {your_list[i].mention} `({your_list[i].id})` : {len(your_list[i].members)} member(s)\n"
          sent.append(your_list[i].id)
      if str(count).endswith("0") or str(count) == str(len(your_list)):
        embed_array.append(embed)
        embed = discord.Embed(color=clr, description="", title=t)
        embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(embed_array) == 0:
    embed_array.append(embed)
  pag = PaginationViewWallah(embed_array, ctx)
  if len(embed_array) == 1:
    await pag.start(ctx, True)
  else:
    await pag.start(ctx)


async def lister_bn(ctx, color, listxd, *, title):
  embed_array = []
  t = title
  clr = color
  sent = []
  your_list = listxd
  count = 0
  embed = discord.Embed(color=clr, description="", title=t)
  embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(listxd) > 1:
    for i in range(len(listxd)):
      for i__ in range(10):
        if not your_list[i].user.id in sent:
          count += 1
          if str(count).endswith("0") or len(str(count)) != 1:
            actualcount = str(count)
          else:
            actualcount = f"0{count}"
          embed.description += f"`{actualcount}` {your_list[i].user} `({your_list[i].user.id})`\n"
          sent.append(your_list[i].user.id)
      if str(count).endswith("0") or str(count) == str(len(your_list)):
        embed_array.append(embed)
        embed = discord.Embed(color=clr, description="", title=t)
        embed.set_footer(icon_url=ctx.bot.user.avatar)
  if len(embed_array) == 0:
    embed_array.append(embed)
  pag = PaginationViewWallah(embed_array, ctx)
  if len(embed_array) == 1:
    await pag.start(ctx, True)
  else:
    await pag.start(ctx)


async def working_lister(ctx, color, listxd, *, title):
  embed_array = []
  t = title
  clr = color
  sent = []
  your_list = listxd
  count = 0
  idkh = True
  embed = discord.Embed(color=clr, description="", title=t)
  embed.set_footer(icon_url=ctx.bot.user.avatar)
  if idkh:
    for i in range(len(listxd)):
      for i__ in range(10):
        if not your_list[i].id in sent:
          count += 1
          if str(count).endswith("0") or len(str(count)) != 1:
            actualcount = str(count)
          else:
            actualcount = f"0{count}"
          embed.description += f"`{actualcount}` {your_list[i]} (<@{your_list[i].id}>)\n"
          sent.append(your_list[i].id)
      if str(count).endswith("0") or str(count) == str(len(your_list)):
        embed_array.append(embed)
        embed = discord.Embed(color=clr, description="", title=t)
        embed.set_footer(icon_url=ctx.bot.user.avatar)

  if len(embed_array) == 0:
    embed_array.append(embed)
  pag = PaginationViewWallah(embed_array, ctx)
  if len(embed_array) == 1:
    await pag.start(ctx, True)
  else:
    await pag.start(ctx)


async def working_listerr(ctx, color, listxd, *, title):
  embed_array = []
  t = title
  clr = color
  sent = []
  your_list = listxd
  count = 0
  idkh = True
  embed = discord.Embed(color=clr, description="", title=t)
  embed.set_footer(icon_url=ctx.bot.user.avatar)
  if idkh:
    for i in range(len(listxd)):
      for i__ in range(10):
        if not your_list[i].id in sent:
          count += 1
          if str(count).endswith("0") or len(str(count)) != 1:
            actualcount = str(count)
          else:
            actualcount = f"0{count}"
          embed.description += f"`{actualcount}` {your_list[i]} `{your_list[i]}`\n"
          sent.append(your_list[i].id)
      if str(count).endswith("0") or str(count) == str(len(your_list)):
        embed_array.append(embed)
        embed = discord.Embed(color=clr, description="", title=t)
        embed.set_footer(icon_url=ctx.bot.user.avatar)

  if len(embed_array) == 0:
    embed_array.append(embed)
  pag = PaginationViewWallah(embed_array, ctx)
  if len(embed_array) == 1:
    await pag.start(ctx, True)
  else:
    await pag.start(ctx)

class PaginationViewWallah:

 def __init__(self, embed_list, ctx):
  self.elist = embed_list
  self.context = ctx

 def disable_button(self, menu):
  tax = str(menu.message.embeds[0].footer.text).replace(" ", "").replace(
      "Page", "")
  num = int(tax[0])
  if num == 1:
    fis = menu.get_button("2", search_by="id")
    bax = menu.get_button("1", search_by="id")

 def enable_button(self, menu):
  tax = str(menu.message.embeds[0].footer.text).replace(" ", "").replace(
      "Page", "")
  num = int(tax[0])
  if num != 1:
    fis = menu.get_button("2", search_by="id")
    bax = menu.get_button("1", search_by="id")
    print(bax)

 async def dis_button(self, menu):
  self.disable_button(menu)

 async def ene_button(self, menu):
  self.ene_button(menu)

 async def start(self, ctx, disxd=False):
  style = f"{ctx.bot.user.name} • Page $/&"
  menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed, style=style)
  for xem in self.elist:
    menu.add_page(xem)
  lax = ViewButton(style=discord.ButtonStyle.secondary,
                   label=None,
                   emoji='<:previous:1229446011286720513>',
                   custom_id=ViewButton.ID_GO_TO_FIRST_PAGE)
  menu.add_button(lax)
  bax = ViewButton(style=discord.ButtonStyle.secondary,
                   label=None,
                   emoji='<:prev:1229446062335328306>',
                   custom_id=ViewButton.ID_PREVIOUS_PAGE)
  menu.add_button(bax)
  bax2 = ViewButton(style=discord.ButtonStyle.secondary,
                    label=None,
                    emoji='<:stop_white:1229447092175376534>',
                    custom_id=ViewButton.ID_END_SESSION)
  menu.add_button(bax2)
  bax3 = ViewButton(style=discord.ButtonStyle.secondary,
                    label=None,
                    emoji='<:next:1229446448777527327>',
                    custom_id=ViewButton.ID_NEXT_PAGE)
  menu.add_button(bax3)
  sax = ViewButton(style=discord.ButtonStyle.secondary,
                   label=None,
                   emoji='<:_next:1229445926414848061>',
                   custom_id=ViewButton.ID_GO_TO_LAST_PAGE)
  menu.add_button(sax)
  if disxd:
    menu.disable_all_buttons()
  menu.disable_button(lax)
  menu.disable_button(bax)

  async def all_in_one_xd(payload):

    newmsg = await ctx.channel.fetch_message(menu.message.id)
    tax = str(newmsg.embeds[0].footer.text).replace(
        f"{ctx.bot.user.name}",
        "").replace(" ", "").replace("Page", "").replace("•", "")
    saxl = tax.split("/")
    num = int(saxl[0])
    numw = int(saxl[1])
    if num == 1:
      menu.disable_button(lax)
      menu.disable_button(bax)
    else:
      menu.enable_button(lax)
      menu.enable_button(bax)
    if num == numw:
      menu.disable_button(bax3)
      menu.disable_button(sax)
    else:
      menu.enable_button(bax3)
      menu.enable_button(sax)
    await menu.refresh_menu_items()

  menu.set_relay(all_in_one_xd)
  await menu.start()
  
async def setup(bot):
  await bot.add_cog(Utility(bot))
