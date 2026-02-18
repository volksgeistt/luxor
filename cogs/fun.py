from discord.ext import commands
import discord
import requests
from discord.ext.commands import BucketType
from config import config
import random
import asyncio
import requests
import akinator
from PIL import Image
from io import BytesIO
import aiohttp

def get_gif(action):
  url = f'https://nekos.best/api/v2/{action}'
  headers = {'User-Agent': 'Mozilla/5.0'}
  response = requests.get(url, headers=headers)
  data = response.json()
  if 'results' in data and data['results']:
      return data['results'][0]['url']
  else:
      return None

class Fun(commands.Cog):
  """Fun commands which will make your day better."""
  def __init__(self, bot):
    self.bot = bot
    self.aki_sessions = {}
    self.color = config.hex
    #self.imgs = ["https://tenor.com/view/ninjala-jane-hacker-hacking-computer-gif-20337624"]
    self.lolw = ["johndoe123", "janedoe123", "samsmith", "emilyjones", "alexander", "oliviapope", "charlie", "lucybrown", "michaels", "dwightschrute", "jimhalpert", "pambeesly", "harrypot", "hermionegr", "ronweasley", "frodo", "bilbobagg", "aragorn", "legolas", "darthvad", "lukeskyw", "leiaorga", "hansolo", "captaina", "ironman", "thor", "blackwid", "hulk", "spiderma", "wolverin", "batman", "superman", "wonderwo", "aquaman", "flash", "greenlan", "captainm", "thanos", "joker", "harleyqu", "clarkken", "tonystar", "bruceway", "natashar", "peterpar", "logan"]
    self.domains = ["@yahoo.com", "@gmail.com", "@hotmail.com", "@outlook.com", "@icloud.com", "@aol.com", "@protonmail.com", "@mail.com", "@yandex.com", "@zoho.com", "@inbox.com", "@live.com", "@yahoo.co.uk", "@rediffmail.com", "@gmx.com", "@fastmail.com", "@tutanota.com", "@rocketmail.com", "@mail.ru", "@yopmail.com", "@cox.net", "@att.net", "@verizon.net", "@earthlink.net", "@sbcglobal.net", "@optonline.net", "@me.com", "@mac.com", "@msn.com"]
    self.pwds = ["ghostlost133", "@1337", "ohnodaddy", "isagoodboy", "darklord", "stardust", "gamerboy", "cosmicwarrior", "dragonslayer", "galacticpower", "magicalwizard", "spaceinvader", "fantasyhero", "epicgamer", "mythicbeast"]
    self.ips = ["57.241.186.78", "243.243.67.10", "60.6.22.252", "162.197.188.84", "105.38.74.110", "185.196.21.57", "27.207.203.164", "139.196.140.227", "157.26.188.6", "101.19.200.109", "192.168.1.1", "10.0.0.1", "172.16.0.1", "8.8.8.8", "8.8.4.4", "203.0.113.1", "198.51.100.1", "127.0.0.1", "169.254.169.254", "176.32.98.166", "91.198.174.192", "54.192.10.1", "185.32.221.200", "13.107.42.13", "192.0.2.1", "198.18.0.1", "203.0.113.1", "224.0.0.1", "240.0.0.1", "255.255.255.255"]
    self.lw = ["How To Cook", "YouTube ViewBot","how to tie a tie", "best chocolate cake recipe", "learn python programming", "how to meditate", "how to play guitar", "top 10 movies of all time", "healthy breakfast ideas", "travel destinations 2024", "home workout routines", "how to start a small business", "easy DIY home decor ideas", "popular book series", "how to improve memory", "financial planning tips", "best smartphone apps", "how to grow tomatoes", "yoga poses for beginners", "funny cat videos", "famous quotes about life", "simple dinner recipes", "how to fix a leaky faucet", "learn photography basics", "top trending songs", "how to invest in stocks", "effective time management techniques", "dog training tips", "healthy snack ideas", "popular video games 2024", "how to make money online", "interesting science experiments"]
    self.sites = ["google.com", "youtube.com", "facebook.com", "amazon.com", "twitter.com", "instagram.com", "linkedin.com", "yahoo.com", "wikipedia.org", "reddit.com", "ebay.com", "netflix.com", "microsoft.com", "apple.com", "bing.com", "wordpress.com", "adobe.com", "bbc.com", "cnn.com", "nytimes.com", "github.com", "stackoverflow.com", "spotify.com", "imdb.com", "paypal.com", "pinterest.com", "dropbox.com", "twitch.tv", "hulu.com", "forbes.com", "theguardian.com", "aliexpress.com", "salesforce.com", "bloomberg.com", "thefreedictionary.com", "booking.com", "etsy.com", "groupon.com", "quora.com", "nationalgeographic.com", "weather.com", "craigslist.org", "webmd.com", "usatoday.com", "stackexchange.com", "target.com", "booking.com", "bbc.co.uk", "time.com"]
    self.code = [("AF", "+93", "🇦🇫"), ("AL", "+355", "🇦🇱"), ("DZ", "+213", "🇩🇿"), ("AD", "+376", "🇦🇩"), ("AO", "+244", "🇦🇴"), ("AR", "+54", "🇦🇷"), ("AM", "+374", "🇦🇲"), ("AU", "+61", "🇦🇺"), ("AT", "+43", "🇦🇹"), ("AZ", "+994", "🇦🇿"), ("BS", "+1-242", "🇧🇸"), ("BH", "+973", "🇧🇭"), ("BD", "+880", "🇧🇩"), ("BB", "+1-246", "🇧🇧"), ("BY", "+375", "🇧🇾"), ("BE", "+32", "🇧🇪"), ("BZ", "+501", "🇧🇿"), ("BJ", "+229", "🇧🇯"), ("BT", "+975", "🇧🇹"), ("BO", "+591", "🇧🇴"), ("BA", "+387", "🇧🇦"), ("BW", "+267", "🇧🇼"), ("BR", "+55", "🇧🇷"), ("BN", "+673", "🇧🇳"), ("BG", "+359", "🇧🇬"), ("BF", "+226", "🇧🇫"), ("BI", "+257", "🇧🇮"), ("KH", "+855", "🇰🇭"), ("CM", "+237", "🇨🇲"), ("CA", "+1", "🇨🇦"), ("CV", "+238", "🇨🇻"), ("CF", "+236", "🇨🇫"), ("TD", "+235", "🇹🇩"), ("CL", "+56", "🇨🇱"), ("CN", "+86", "🇨🇳"), ("CO", "+57", "🇨🇴"), ("KM", "+269", "🇰🇲"), ("CG", "+242", "🇨🇬"), ("CD", "+243", "🇨🇩"), ("CR", "+506", "🇨🇷"), ("HR", "+385", "🇭🇷"), ("CU", "+53", "🇨🇺"), ("CY", "+357", "🇨🇾"), ("CZ", "+420", "🇨🇿"), ("DK", "+45", "🇩🇰"), ("DJ", "+253", "🇩🇯"), ("DM", "+1-767", "🇩🇲"), ("DO", "+1-809, +1-829, +1-849", "🇩🇴"), ("EC", "+593", "🇪🇨"), ("EG", "+20", "🇪🇬"), ("SV", "+503", "🇸🇻"), ("GQ", "+240", "🇬🇶"), ("ER", "+291", "🇪🇷"), ("EE", "+372", "🇪🇪"), ("ET", "+251", "🇪🇹"), ("FJ", "+679", "🇫🇯"), ("FI", "+358", "🇫🇮"), ("FR", "+33", "🇫🇷"), ("GA", "+241", "🇬🇦"), ("GM", "+220", "🇬🇲"), ("GE", "+995", "🇬🇪"), ("DE", "+49", "🇩🇪"), ("GH", "+233", "🇬🇭"), ("GR", "+30", "🇬🇷"), ("GD", "+1-473", "🇬🇩"), ("GT", "+502", "🇬🇹"), ("GN", "+224", "🇬🇳"), ("GW", "+245", "🇬🇼"), ("GY", "+592", "🇬🇾"), ("HT", "+509", "🇭🇹"), ("HN", "+504", "🇭🇳"), ("HU", "+36", "🇭🇺"), ("IS", "+354", "🇮🇸"), ("IN", "+91", "🇮🇳"), ("ID", "+62", "🇮🇩"), ("IR", "+98", "🇮🇷"), ("IQ", "+964", "🇮🇶"), ("IE", "+353", "🇮🇪"), ("IL", "+972", "🇮🇱"), ("IT", "+39", "🇮🇹"), ("JM", "+1-876", "🇯🇲"), ("JP", "+81", "🇯🇵"), ("JO", "+962", "🇯🇴"), ("KZ", "+7", "🇰🇿"), ("KE", "+254", "🇰🇪"), ("KI", "+686", "🇰🇮"), ("KP", "+850", "🇰🇵"), ("KR", "+82", "🇰🇷"), ("KW", "+965", "🇰🇼"), ("KG", "+996", "🇰🇬"), ("LA", "+856", "🇱🇦"), ("LV", "+371", "🇱🇻"), ("LB", "+961", "🇱🇧"), ("LS", "+266", "🇱🇸"), ("LR", "+231", "🇱🇷"), ("LY", "+218", "🇱🇾"), ("LI", "+423", "🇱🇮"), ("LT", "+370", "🇱🇹"), ("LU", "+352", "🇱🇺"), ("MK", "+389", "🇲🇰"), ("MG", "+261", "🇲🇬"), ("MW", "+265", "🇲🇼"), ("MY", "+60", "🇲🇾"), ("MV", "+960", "🇲🇻"), ("ML", "+223", "🇲🇱"), ("MT", "+356", "🇲🇹")]





  def get_format(self, type, url):
    r = requests.get(url)
    if type == "t":
      rp = r.text
      return rp
    elif type == "j":
      rp = r.json()
      return rp
    elif type == "a":
      return r


  @commands.command(name="dare", aliases=["dr"], help="I dare you to use this command.")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def _dr(self, ctx):
    dlol = self.get_format(type="j", url="https://api.truthordarebot.xyz/api/dare")
    icn = ctx.message.author.avatar.url if ctx.message.author.avatar is not None else ctx.bot.user.avatar.url
    embed = discord.Embed(color=config.hex, description=f"{dlol['question']}")
    embed.set_author(name=f"{ctx.message.author}", icon_url=icn)
    await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="cmds",help="shows commands count in the bot")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def cmd(self, ctx):
    await ctx.send(f"I consists a total of {len(set(ctx.bot.walk_commands()))} commands.! :P")

  @commands.command(name="servers",help="shows server count of the bot")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def server(self, ctx):
    await ctx.send(f"I'm serving to a total of {len(self.bot.guilds)} guild as of now.! :33")
  
  @commands.command(name="src",help="sends the bot source code")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def botsrc(self, ctx):
    await ctx.send(f"**Awww, need my source code.?**\nhttps://tenor.com/view/never-gonna-let-you-down-gif-25887491")

  @commands.command(name="dev",help="shows dev info")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def developer(self, ctx):
    await ctx.reply(f"https://github.com/volksgeistt")


  @commands.command(name="simp",help="Shows how much of a simp someone is")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def simp_(self, ctx, user: discord.Member=None):
      if user==None:
          user = ctx.author
      if user.id in config.owner_ids:
          embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: you can't use this command on my developers! :DD")
          await ctx.reply(embed=embed, mention_author=False)
      else:     
          simp_percentage = random.randrange(101)
          embed = discord.Embed(color=config.hex, description=f"{config.ques_emoji} {user.mention}: they are `{simp_percentage}%` simp 🫦")
          await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="stupid",help="Shows how stupid someone is")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def stupid_(self, ctx, user: discord.Member=None):
      if user==None:
          user = ctx.author
      if user.id in config.owner_ids:
          embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: you can't use this command on my developers! :DD")
          await ctx.reply(embed=embed, mention_author=False)
      else:     
          stupid_percentage = random.randrange(101)
          embed = discord.Embed(color=config.hex, description=f"{config.ques_emoji} {user.mention}: they are `{stupid_percentage}%` stupid 🤪")
          await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="ship",help="Ship two users together")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def ship_(self, ctx, user1: discord.Member=None, user2: discord.Member=None):
      if user1==None:
          user1 = ctx.author
      if user2==None:
          user2 = ctx.author
      
      ship_percentage = random.randrange(101)
      
      if ship_percentage < 30:
          message = "Yikes... not a great match 💔"
      elif ship_percentage < 60:
          message = "There might be something there... 💓"
      elif ship_percentage < 80:
          message = "Pretty good match! 💖"
      else:
          message = "Perfect match made in heaven! 💘"
          
      embed = discord.Embed(color=config.hex, description=f"{config.ques_emoji} **Shipping {user1.mention} with {user2.mention}**\n> **Love Rating:** `{ship_percentage}%`")
      embed.set_footer(text=message,icon_url=self.bot.user.avatar)
      await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="dice",help="Roll a dice with custom sides")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def dice_(self, ctx, sides: int=6):
      if sides < 1:
          embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: please provide a valid number of sides!")
          await ctx.reply(embed=embed, mention_author=False)
          return
          
      result = random.randint(1, sides)
      embed = discord.Embed(color=config.hex, description=f"{config.ques_emoji} {ctx.author.mention}: you rolled a `{result}` on a {sides}-sided dice! 🎲")
      await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="choose",help="Let the bot choose between multiple options")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def choose_(self, ctx, *, options):
      choices = [option.strip() for option in options.split(",")]
      if len(choices) < 2:
          embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: please provide at least 2 options separated by commas!")
          await ctx.reply(embed=embed, mention_author=False)
          return
          
      choice = random.choice(choices)
      embed = discord.Embed(color=config.hex, description=f"{config.ques_emoji} {ctx.author.mention}: I choose **{choice}**!")
      await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="reverse",help="Reverse the given text")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def reverse_(self, ctx, *, text: str):
      reversed_text = text[::-1]
      embed = discord.Embed(color=config.hex, description=f"{config.ques_emoji} {ctx.author.mention}: {reversed_text}")
      await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="insult",help="Generate a funny insult (just for fun!)")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def insult_(self, ctx, user: discord.Member=None):
      if user==None:
          user = ctx.author
          
      async with aiohttp.ClientSession() as session:
          async with session.get("https://evilinsult.com/generate_insult.php?lang=en&type=json") as response:
              if response.status == 200:
                  data = await response.json()
                  insult = data["insult"]
                  await ctx.reply(f"hey {user.mention}...\n{insult}\nn||This is just for fun! No offense intended :33 ||", mention_author=False)
              else:
                  embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: Failed to generate an insult. Try again later!")
                  await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="randomhex",help="Get a random hex color code")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def randomhex_(self, ctx):
      hex_code = ''.join(random.choices('0123456789ABCDEF', k=6))
      embed = discord.Embed(
          color=int(hex_code, 16),
          description=f"{config.ques_emoji} {ctx.author.mention}: Random hex color: `#{hex_code}`\nPreview color shown in embed color! 🎨"
      )
      await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="cat",help="Get a random cat image")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def cat_(self, ctx):
      async with aiohttp.ClientSession() as session:
          async with session.get("https://api.thecatapi.com/v1/images/search") as response:
              if response.status == 200:
                  data = await response.json()
                  cat_url = data[0]["url"]
                  embed = discord.Embed(color=config.hex)
                  embed.set_image(url=cat_url)
                  embed.description = f"{config.ques_emoji} {ctx.author.mention}: Here's your random cat! 🐱"
                  await ctx.reply(embed=embed, mention_author=False)
              else:
                  embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: Failed to fetch a cat image. Try again later!")
                  await ctx.reply(embed=embed, mention_author=False)

    

  @commands.command(name="truth", aliases=["tru"], help="Gives you a random truth")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def _tr(self, ctx):
    dlol = self.get_format(type="j", url="https://api.truthordarebot.xyz/api/truth")
    icn = ctx.message.author.avatar.url if ctx.message.author.avatar is not None else ctx.bot.user.avatar.url
    embed = discord.Embed(color=config.hex, description=f"{dlol['question']}")
    embed.set_author(name=f"{ctx.message.author}", icon_url=icn)
    await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="nhie", aliases=["nhiee", "neverhaveiever"], help="Gives you a random never have I ever situation")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def _nhie(self, ctx):
    dlol = self.get_format(type="j", url="https://api.truthordarebot.xyz/api/nhie")
    icn = ctx.message.author.avatar.url if ctx.message.author.avatar is not None else ctx.bot.user.avatar.url
    embed = discord.Embed(color=config.hex, description=f"{dlol['question']}")
    embed.set_author(name=f"{ctx.message.author}", icon_url=icn)
    await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="wyr", aliases=["wyrr", "wouldyourather"], help="Gives you a would you rather situation")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def _wyr(self, ctx):
    dlol = self.get_format(type="j", url="https://api.truthordarebot.xyz/api/wyr")
    icn = ctx.message.author.avatar.url if ctx.message.author.avatar is not None else ctx.bot.user.avatar.url
    embed = discord.Embed(color=config.hex, description=f"{dlol['question']}")
    embed.set_author(name=f"{ctx.message.author}", icon_url=icn)
    await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="paranoia", aliases=["paronia"], help="Gives you a random paranoia")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def _paronia(self, ctx):
    dlol = self.get_format(type="j", url="https://api.truthordarebot.xyz/api/paranoia")
    icn = ctx.message.author.avatar.url if ctx.message.author.avatar is not None else ctx.bot.user.avatar.url
    embed = discord.Embed(color=config.hex, description=f"{dlol['question']}")
    embed.set_author(name=f"{ctx.message.author}", icon_url=icn)
    await ctx.reply(embed=embed, mention_author=False)
                     

  @commands.command(name="guessthenumber", aliases=["gtn"], help="Play a guess the number game! You have one chance to guess the number 1-10")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def _gtn(self, ctx):
    listlol = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    chances = 3
    choice = random.choice(listlol)
    listlol.remove(choice)
    cc2 = random.choice(listlol)
    if choice > cc2:
      hnr = "greater"
    else:
      hnr = "lower"
    await ctx.send(f"A number between **1 and 10** has been chosen, You have 1 attempt to guess the right number! Type your guess in the chat as a valid number!\nhint: number is {hnr} than {cc2}")
    def check(m):
      return m.channel.id == ctx.channel.id and m.guild.id == ctx.guild.id and m.author.id == ctx.author.id
    try:
      ms2=await ctx.bot.wait_for("message", check=check, timeout=30)
    except asyncio.TimeoutError:
      await ctx.send("You got to give me a number... game ended due to inactivity")
    else:
      nvr = int(ms2.content)
      if nvr == choice:
        await ctx.send("You **Won!**")
      else:
        await ctx.send(f"You **Lost** right number was {choice}.")

            
  @commands.command(name="hack", help="hack someone's discord account")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def _hack(self, ctx, user: discord.Member):
    n = str(user.name)
    pwd = n+ random.choice(self.pwds)
    mail = n+random.choice(self.lolw)+random.choice(self.domains)
    ip = random.choice(self.ips)
    gs = random.choice(self.lw)
    sittte = random.choice(self.sites)
    msg = await ctx.reply(f"Hacking into {user}'s account...")
    await asyncio.sleep(5)
    await msg.delete()
    embed = discord.Embed(color=config.hex, title=f"Hacked Data:",description=f">>> **Email:** {mail}\n**Password:** {pwd}\n**Country:** {random.choice(self.code)}\n**IP:** {ip}\n**Last Google Search:** {gs}\n**Last Website Visited:** {sittte}")
    embed.set_image(url=f"https://cdn.discordapp.com/attachments/1226511108966187081/1229015687943553035/Hacked-Site-small.jpg?ex=662e250e&is=661bb00e&hm=bcffe0d7545caa1f44812167f9aba26f1b4625b640996009b920dc7dd16393e0&")
    await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="bitches",help="shows how many bitches you have")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def bitches_(self, ctx, user: discord.Member=None):
      if user==None:
          embed=discord.Embed(color=config.hex, description= f"{config.ques_emoji} {ctx.author.mention}: you have a total of `{random.randrange(51)}` bitches!!")
          await ctx.reply(embed=embed, mention_author=False)
      else:
          embed=discord.Embed(color=config.hex, description= f"{config.ques_emoji} {user.mention}: they have a total of `{random.randrange(51)}` bitches!!")
          await ctx.reply(embed=embed, mention_author=False)

  @commands.command(name="iq",help="shows how much iq you have")
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def iq_(self, ctx, user: discord.Member=None):
      if user==None:
          embed=discord.Embed(color=config.hex, description= f"{config.ques_emoji} {ctx.author.mention}: you have `{random.randrange(150)}` iq :brain:")
          await ctx.reply(embed=embed, mention_author=False)
      else:
          embed=discord.Embed(color=config.hex, description= f"{config.ques_emoji} {user.mention}: they have `{random.randrange(150)}` iq :brain:")
          await ctx.reply(embed=embed, mention_author=False)

        
  @commands.command(name="gayrate", help="Shows the 'gayrate' of a user.", aliases=["gay"])
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def gayrate_(self, ctx, user: discord.Member=None):
      if user.id in config.owner_ids:
        embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: you can't use this command on my developers! :DD")
        await ctx.reply(embed=embed, mention_author=False)
      else:     
        gay_percentage = random.randrange(101)
        embed = discord.Embed(color=config.hex, description=f"{config.ques_emoji} {user.mention}: they are `{gay_percentage}%` gay 🏳️‍🌈")
        await ctx.reply(embed=embed, mention_author=False)
         
            
# Anime Cmds

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def slap(self, ctx, user: discord.Member=None):
      gif_url = get_gif("slap")
      await self.send_action(ctx, "slaps", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def bite(self, ctx, user: discord.Member=None):
      gif_url = get_gif("bite")
      await self.send_action(ctx, "bites", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def highfive(self, ctx, user: discord.Member=None):
      gif_url = get_gif("highfive")
      await self.send_action(ctx, "highfives", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def hug(self, ctx, user: discord.Member=None):
      gif_url = get_gif("hug")
      await self.send_action(ctx, "hugs", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def kiss(self, ctx, user: discord.Member=None):
      gif_url = get_gif("kiss")
      await self.send_action(ctx, "kisses", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def punch(self, ctx, user: discord.Member=None):
      gif_url = get_gif("punch")
      await self.send_action(ctx, "punches", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def shoot(self, ctx, user: discord.Member=None):
      gif_url = get_gif("shoot")
      await self.send_action(ctx, "shoots", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def smile(self, ctx, user: discord.Member=None):
      gif_url = get_gif("smile")
      await self.send_action(ctx, "smiles at", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def stare(self, ctx, user: discord.Member=None):
      gif_url = get_gif("stare")
      await self.send_action(ctx, "stares at", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def wave(self, ctx, user: discord.Member=None):
      gif_url = get_gif("wave")
      await self.send_action(ctx, "waves at", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def tickle(self, ctx, user: discord.Member=None):
      gif_url = get_gif("tickle")
      await self.send_action(ctx, "tickles", user, gif_url)

  @commands.command()
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def wink(self, ctx, user: discord.Member=None):
      gif_url = get_gif("wink")
      await self.send_action(ctx, "winks at", user, gif_url)

  async def send_action(self, ctx, action_text, user, gif_url):
      if gif_url:
          if user:
              description = f"**{ctx.author.mention} {action_text} {user.mention}!**"
          else:
              description = f"**{ctx.author.mention} {action_text}!**"

          embed = discord.Embed(description=description, color=config.hex)
          embed.set_image(url=gif_url)
          await ctx.send(embed=embed)
      else:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: error fetching gif image",color=config.hex))

  @commands.command(name='wanted')
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def wanted_(self, ctx, user: discord.Member = None):
    if user == None:
      user = ctx.author
    wanted = Image.open("assets/wanted2.jpg")
    asset = user.display_avatar.with_size(128)
    data = BytesIO(await asset.read())
    pfp = Image.open(data)
    pfp = pfp.resize((123,123))
    wanted.paste(pfp, (33,80))
    wanted.save("assets/profile.jpg")
    await ctx.send(file = discord.File("assets/profile.jpg"))

  

  @commands.command(name='rip')
  @commands.cooldown(1,3, commands.BucketType.user)
  @commands.guild_only()
  async def rip_(self, ctx, user: discord.Member = None):
    if user == None:
      user = ctx.author
    rip = Image.open("assets/rip.png")
    asset = user.display_avatar.with_size(128)
    data = BytesIO(await asset.read())
    pfp = Image.open(data)
    pfp = pfp.resize((177,177))
    rip.paste(pfp, (120,250))
    rip.save("assets/rippeduser.png")
    await ctx.send(file = discord.File("assets/rippeduser.png"))

  #@commands.command(name="aki", help="Play a guessing game with Akinator!")
  #@commands.cooldown(1, 5, BucketType.user)
  #@commands.guild_only()
  #async def test(self, ctx):
        #aki = akinator.Akinator()
       # self.aki_sessions[ctx.author.id] = aki  # Track the session by user ID
     #   embed = discord.Embed(color=self.color, title="Think of a character!", description="I'll try to guess who it is!")
      # await ctx.reply(embed=embed, mention_author=False)

  #      try:
       #     question = aki.start_game(language="en")  # Start the Akinator game in English

         #   while aki.progression <= 80:
            #    embed = discord.Embed(
             #       color=self.color,
               #     title="Akinator Game",
               #     description=f"{question}\n\nType `yes`, `no`, `idk`, `probably`, or `probably not` to answer."
           #     )
             #   await ctx.send(embed=embed)

             #   def check(m):
                #    return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no", "idk", "probably", "probably not"]

              #  try:
                #    answer = await self.bot.wait_for("message", check=check, timeout=30)
               # except asyncio.TimeoutError:
                 #   await ctx.send("Game ended due to inactivity.")
                #    del self.aki_sessions[ctx.author.id]
                 #   return

              #  question = aki.answer(answer.content.lower())

           # aki.win()
         #   embed = discord.Embed(
              #  color=self.color,
               # title="Is this your character?",
               # description=f"**{aki.first_guess['name']}**\n{aki.first_guess['description']}\n\nWas I correct? (`yes`/`no`)"
          #  )
           # embed.set_image(url=aki.first_guess['absolute_picture_path'])
          #  await ctx.send(embed=embed)

          #  def check_final(m):
            #    return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

          #  try:
             #   final_answer = await self.bot.wait_for("message", check=check_final, timeout=30)
           # except asyncio.TimeoutError:
            #    await ctx.send("Game ended due to inactivity.")
            #    del self.aki_sessions[ctx.author.id]
             #   return

          #  if final_answer.content.lower() == "yes":
          #      await ctx.send("Yay! I guessed it right!")
          #  else:
           #     await ctx.send("Oh no! I'll try better next time.")

     #   except akinator.AkiNoQuestions:
          #  await ctx.send("Oops! Something went wrong with the game.")

      #  finally:
          #  if ctx.author.id in self.aki_sessions:
            #    del self.aki_sessions[ctx.author.id]

    
async def setup(bot):
  await bot.add_cog(Fun(bot))
    




  