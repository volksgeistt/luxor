from os import strerror
from discord.ext import commands, tasks
import discord
import json
import random
from config import config

def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed

class AutoPost(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.color = config.hex
    self.iconurluwu = "https://cdn.discordapp.com/avatars/1201066120908656712/1d9da0fabf158e40ae2bb41238a44f0e.png?size=1024"

    self.send_male.start()
    self.send_female.start()
    self.send_banner.start()
    self.send_anime.start()

  def load_data(self):
    try:
      with open("./db/autopost.json", "r") as f:
        return json.load(f)
    except FileNotFoundError:
      return {}

  def save_data(self, data):
    with open("db/autopost.json", "w") as f:
      json.dump(data, f, indent=4)

  def fetch_anime(self):
    try:
      with open("pfps/anime.txt", "r") as file:
        return file.readlines()
    except FileNotFoundError:
      return []
  
  def fetch_female(self):
    try:
      with open("pfps/female.txt", "r") as file:
        return file.readlines()
    except FileNotFoundError:
      return []

  def fetch_males(self):
    try:
      with open("pfps/males.txt", "r") as file:
        return file.readlines()
    except FileNotFoundError:
      return []

      return {}

  def fetch_banner(self):
    try:
      with open("pfps/banners.txt", "r") as file:
        return file.readlines()
    except FileNotFoundError:
      return []

  @tasks.loop(seconds=150)
  async def send_male(self):
    data = self.load_data()
    for guild_id in data:
      guild = self.bot.get_guild(int(guild_id))
      guild_data = data[guild_id]["male"]

      if guild_data['toggle'] == False:
        continue
      else:
       try:
        channel_id = guild_data['channel']
        channel = guild.get_channel(int(channel_id))
        if channel is None:
          continue
        else:
          males = self.fetch_males()
          male = random.choice(males).strip()
          embed = discord.Embed(color=config.hex).set_image(url=male)
          embed.set_footer(text=f"{self.bot.user.name} male autopost",
                           icon_url=self.bot.user.avatar)
          embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
          await channel.send(embed=embed)
       except:
          continue 

  @tasks.loop(seconds=150)
  async def send_female(self):
    data = self.load_data()
    for guild_id in data:
      guild = self.bot.get_guild(int(guild_id))
      guild_data = data[guild_id]["female"]

      if guild_data['toggle'] == False:
        continue
      else:
       try:
        channel_id = guild_data['channel']
        channel = guild.get_channel(int(channel_id))
        if channel is None:
          continue
        else:
          females = self.fetch_female()
          female = random.choice(females).strip()
          embed = discord.Embed(
              color=config.hex).set_image(url=female)
          embed.set_footer(text=f"{self.bot.user.name} female autopost",
                           icon_url=self.bot.user.avatar)
          embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
          await channel.send(embed=embed)
       except:
        continue 

  @tasks.loop(seconds=150)
  async def send_banner(self):
    data = self.load_data()
    for guild_id in data:
      guild = self.bot.get_guild(int(guild_id))
      guild_data = data[guild_id]["banner"]

      if guild_data['toggle'] == False:
        continue
      else:
       try:
        channel_id = guild_data['channel']
        channel = guild.get_channel(int(channel_id))
        if channel is None:
          continue
        else:
          banners = self.fetch_banner()
          banner = random.choice(banners).strip()
          embed = discord.Embed(
              color=config.hex).set_image(url=banner)
          embed.set_footer(text=f"{self.bot.user.name} banner autopost",
                           icon_url=self.bot.user.avatar)
          embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)

          await channel.send(embed=embed)
       except:
        continue 

  @tasks.loop(seconds=150)
  async def send_anime(self):
    data = self.load_data()
    for guild_id in data:
      guild_data = data[guild_id]["anime"]
      if guild_data['toggle'] == False:
        continue
      else:
       try:
        channel_id = guild_data['channel']
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
          continue
        else:
          animes = self.fetch_anime()
          anime = random.choice(animes).strip()
          embed = discord.Embed(
              color=config.hex).set_image(url=anime)
          embed.set_footer(text=f"{self.bot.user.name} anime autopost",
                           icon_url=self.bot.user.avatar)
          embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
          await channel.send(embed=embed)
       except:
        continue 

  @commands.group(name="autopost", invoke_without_command=True, aliases=["ap"])
  async def auto_post(self, ctx):
    embed = discord.Embed(
        title="Autopost Subcommands:",
        description=
        f">>> `autopost male`, `autopost female`, `autopost banner`, `autopost anime`\n{config.ques_emoji} Example: `autopost male enable #males`",
        color=config.hex)
    await ctx.reply(embed=embed)

  @auto_post.command(name="male",help="enable or disable male avatar autopost for your server")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def autopost_male(self,
                          ctx,
                          toggle: str,
                          channel: discord.TextChannel = None):
    data = self.load_data()

    if toggle.lower() not in ["enable", "disable"]:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `enable` and `disable`"
      ))

    bool = True if toggle.lower() == "enable" else False

    if bool == True and channel == None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: please mention a channel to enable autopost"
      ))

    if str(ctx.guild.id) not in data:
      data[str(ctx.guild.id)] = {
        "male": {
                "toggle": bool,
                "channel": channel.id if bool else None
            },
            "female": {
                "toggle": False,
                "channel": None
            },
            "banner": {
                "toggle": False,
                "channel": None
            },
            "anime":{
              "toggle":False,
              "channel": None
            }
        }
    else:
      guild_data = data[str(ctx.guild.id)]
      if guild_data['male']['toggle'] == bool:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: this server already has **{'enabled' if bool else 'disabled'}** male avatars"
        ))

      data[str(ctx.guild.id)]["male"]["toggle"] = bool
      data[str(ctx.guild.id)]["male"]["channel"] = channel.id if bool else None

    self.save_data(data)
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully **{'enabled' if bool else 'disabled'}** autopost for male avatars {f'in {channel.mention}' if bool else 'in this server'}"
    ))

# FEMALE

  @auto_post.command(name="female",help="enable or disable female avatar autopost for your server")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def autopost_female(self,
                            ctx,
                            toggle: str,
                            channel: discord.TextChannel = None):
    data = self.load_data()

    if toggle.lower() not in ["enable", "disable"]:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `enable` and `disable`"
      ))

    bool = True if toggle.lower() == "enable" else False

    if bool == True and channel == None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: please mention a channel to enable autopost"
      ))

    if str(ctx.guild.id) not in data:
      data[str(ctx.guild.id)] = {
        "male": {
                "toggle": False,
                "channel": None
            },
            "female": {
                "toggle": bool,
                "channel": channel.id if bool else None
            },
            "banner": {
                "toggle": False,
                "channel": None
            },
            "anime":{
              "toggle":False,
              "channel": None
            }
        }
    else:
      guild_data = data[str(ctx.guild.id)]
      if guild_data['female']['toggle'] == bool:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: this server already has **{'enabled' if bool else 'disabled'}** female avatars"
        ))

      data[str(ctx.guild.id)]["female"]["toggle"] = bool
      data[str(
          ctx.guild.id)]["female"]["channel"] = channel.id if bool else None

    self.save_data(data)
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully **{'enabled' if bool else 'disabled'}** autopost for female avatars {f'in {channel.mention}' if bool else 'in this server'}"
    ))


#Banner

  @auto_post.command(name="banner",help="enable or disable banner autopost for your server")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def autopost_banner(self,
                            ctx,
                            toggle: str,
                            channel: discord.TextChannel = None):
    data = self.load_data()

    if toggle.lower() not in ["enable", "disable"]:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `enable` and `disable`"
      ))

    bool = True if toggle.lower() == "enable" else False

    if bool == True and channel == None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: please mention a channel to enable autopost"
      ))

    if str(ctx.guild.id) not in data:
      data[str(ctx.guild.id)] = {
          "male": {
              "toggle": False,
              "channel": None
          },
          "female": {
              "toggle": False,
              "channel": None
          },
          "banner": {
              "toggle": bool,
              "channel": channel.id if bool else None
          },
          "anime":{
            "toggle":False,
            "channel": None
          }
      }
    else:
      guild_data = data[str(ctx.guild.id)]
      if guild_data['banner']['toggle'] == bool:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: this server already has **{'enabled' if bool else 'disabled'}** banners autopost"
        ))

      data[str(ctx.guild.id)]["banner"]["toggle"] = bool
      data[str(
          ctx.guild.id)]["banner"]["channel"] = channel.id if bool else None

    self.save_data(data)
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully **{'enabled' if bool else 'disabled'}** autopost for banners {f'in {channel.mention}' if bool else 'in this server'}"
    ))

# ANIME AUTOPOST 
  @auto_post.command(name="anime",help="enable or disable anime avatar autopost for your server")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def autopost_anime(self,ctx,toggle: str,channel: discord.TextChannel = None):
    data = self.load_data()
    if toggle.lower() not in ["enable", "disable"]:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `enable` and `disable`"))
    bool = True if toggle.lower() == "enable" else False
    if bool == True and channel == None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: please mention a channel to enable autopost"))
    if str(ctx.guild.id) not in data:
      data[str(ctx.guild.id)] = {
        "male": {
            "toggle": False,
            "channel": None
        },
        "female": {
            "toggle": False,
            "channel": None
        },
        "banner": {
            "toggle": False,
            "channel": None
        },
        "anime":{
          "toggle":bool,
          "channel": channel.id if bool else None
        }
    }
    else:
      guild_data = data[str(ctx.guild.id)]
      if guild_data['anime']['toggle'] == bool:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: this server already has **{'enabled' if bool else 'disabled'}** anime avatars"))
      data[str(ctx.guild.id)]["anime"]["toggle"] = bool
      data[str(ctx.guild.id)]["anime"]["channel"] = channel.id if bool else None

    self.save_data(data)
    await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully **{'enabled' if bool else 'disabled'}** autopost for anime avatars {f'in {channel.mention}' if bool else 'in this server'}"))
# PFP Commands
  @commands.group(name="pfp", invoke_without_command=True, aliases=["pfpp"])
  async def avatar(self, ctx):
    embed = discord.Embed(
        title="Pfps Subcommands:",
        description=
        f">>> `pfp male`, `pfp female`, `pfp anime`\n{config.ques_emoji} Example: `,pfp male`",
        color=config.hex)
    await ctx.reply(embed=embed)
    
  @avatar.command(name='female',help="sends a random female avatar", aliases=['fem'])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def female_(self, ctx):
      with open('pfps/female.txt', 'r') as file:
          lines = file.readlines()
          if lines:
              random_line = random.choice(lines).strip()
              if random_line:
                  embed = discord.Embed(color=config.hex)
                  embed.set_image(url=random_line)
                  embed.set_footer(icon_url=self.bot.user.avatar,text=f"Requested by {ctx.author}")
                  embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                  await ctx.send(embed=embed)

  @avatar.command(name='male',help="sends a random male avatar", aliases=['masc'])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def male_(self, ctx):
      with open('pfps/males.txt', 'r') as file:
          lines = file.readlines()
          if lines:
              random_line = random.choice(lines).strip()
              if random_line:
                  embed = discord.Embed(color=config.hex)
                  embed.set_image(url=random_line)
                  embed.set_footer(icon_url=self.bot.user.avatar,text=f"Requested by {ctx.author}")
                  embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                  await ctx.send(embed=embed)

  @avatar.command(name='anime',help="sends a random anime avatar", aliases=['anim'])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def anime_(self, ctx):
      with open('pfps/anime.txt', 'r') as file:
          lines = file.readlines()
          if lines:
              random_line = random.choice(lines).strip()
              if random_line:
                  embed = discord.Embed(color=config.hex)
                  embed.set_image(url=random_line)
                  embed.set_footer(icon_url=self.bot.user.avatar,text=f"Requested by {ctx.author}")
                  embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar)
                  await ctx.send(embed=embed)

async def setup(bot):
  await bot.add_cog(AutoPost(bot))
