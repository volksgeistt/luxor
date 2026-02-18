from __future__ import annotations
import os
from motor.motor_asyncio import AsyncIOMotorClient
import config as config
from discord.ext import commands, tasks
import discord
import asyncio
from colorama import Fore
import asyncio

os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"

intents = discord.Intents.all()
intents.presences = False

prefix = ","
bot = commands.Bot(command_prefix=prefix,
                   case_insensitive=True,
                   intents=intents,
                   strip_after_prefix=True,
                   status=discord.Status.idle,
                   owner_ids=config.owner_ids,
                   allowed_mentions=discord.AllowedMentions(
                       everyone=False, replied_user=False, roles=False))
bot.remove_command("help")

@bot.event
async def on_ready():
  print(f"{Fore.CYAN}[ READY ] : {bot.user.name} Is Ready.. :DD"+Fore.RESET)
  
   
async def load_cogs():
   for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
      try:
        await bot.load_extension(f'cogs.{filename[:-3]}')
        print(f"{Fore.GREEN}[ COGS ] : ✅ Loaded :- {filename}" + Fore.RESET)
      except Exception as e:
        print(f"{Fore.RED}[ COGS ] : ❌ Error Loading : {filename}:\n( {e} )" +
              Fore.RESET)
        pass


asyncio.run(load_cogs())

@bot.event
async def on_message(message):
    if message.content.strip() == f'<@{bot.user.id}>':
        embed = discord.Embed(
            color=config.hex,
            description=f"{config.utility} {message.author.mention}: my prefix is `{prefix}` use `{prefix}help` for help"
        )
        await message.reply(embed=embed, mention_author=False)
    
    await bot.process_commands(message)
    
    
@bot.event
async def on_connect():
  await bot.load_extension("jishaku")
  await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.listening, name=",help"))


bot.run(config.token)