import discord
import aiohttp
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands import check
from config import mongo
import config, random
from datetime import datetime, timedelta
import colorama, time
from colorama import Fore


def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed

def registered_user():
    async def SpreadBot(ctx):
        data  = await mongo.db.economy.find_one({"_id": str(ctx.author.id)})
        if data:
            return True
        else:
            await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))
            return False
    return commands.check(SpreadBot)

class Economy(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.db = mongo.db.economy

  @commands.command(name="register", help="register your account for economy", aliases=['start'])
  @commands.cooldown(1, 60, commands.BucketType.user)
  @commands.guild_only()
  async def eco_register(self, ctx):
    check = await self.db.find_one({"_id": str(ctx.author.id)})
    
    if check:
      return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have already registered your account"))
    
    data = {"_id": str(ctx.author.id), 
            "wallet": 1000,
            "level": 0,
            "daily_cooldown": 0,
            "daily_streak": 0,
            "banner": None,
            "badges": []
            }

    await self.db.insert_one(data)
    await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully registered, added **1000** coins in your wallet"))
  
  @commands.command(name="balance", help="shows your balance", aliases=['bal'])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def balance(self, ctx):
    data  = await self.db.find_one({"_id": str(ctx.author.id)})
    if not data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))

    wallet = data["wallet"]
    await ctx.send(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}, your wallet balance is **{wallet}** coin(s)"))

  @commands.command(name="beg", help="beg some coins")
  @commands.cooldown(1, 300, commands.BucketType.user)
  @commands.guild_only()
  async def beg(self, ctx):
    data  = await self.db.find_one({"_id": str(ctx.author.id)})
    if not data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))
    
    amt = random.randint(1, 10)*100

    await self.db.update_one({"_id": str(ctx.author.id)}, {"$inc": {"wallet": amt}})

    await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}, you got **{amt}** coins from begging"))
  
  
  @commands.command(name="coinflip", help="flip a coin for a chance to win coins", aliases=['flip', 'cf'])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def coinflip(self, ctx, amount: int=1, face:str="heads"):
    data  = await self.db.find_one({"_id": str(ctx.author.id)})
    if not data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))

    wallet = data["wallet"]

    if amount <= 0 or amount > 100000:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please enter a valid amount between 0 and 100,000"))
    
    if amount > wallet:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you don't have enough coins in your wallet"))
    
    face = face.lower()

    if face not in ['heads', 'tails', 'h', 't']:
       return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: invalid choice, available choices are heads/h and tails/t"))
  
    msg = await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: you flips the coin and chooses {face}, amount: {amount}"))

    flip = random.choice(["heads", "tails"])
    await asyncio.sleep(3)
    face = "heads" if face in ['heads', 'h'] else "tails"

    if face == flip:
        result = "win"
    else:
       result = "lose"

    if result == "win":
        await self.db.update_one({"_id": str(ctx.author.id)}, {"$inc": {"wallet": amount}})
        await msg.edit(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: and it lands on {flip}, you won **{amount}** coins!"))
    else:
        await self.db.update_one({"_id": str(ctx.author.id)}, {"$inc": {"wallet": -amount}})
        await msg.edit(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: and it lands on {flip}, you lost **{amount}** coins!"))
  
  @commands.command(name="daily", help="claim your daily coin reward")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def daily(self, ctx):
    user_id = str(ctx.author.id)
    
    data  = await self.db.find_one({"_id": str(ctx.author.id)})
    if not data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))

    
    streak = data['daily_streak']
    current_time = time.time()
    last = data['daily_cooldown']
    
    reset = None

    if current_time - last >= 86400:
        if streak == 30:
            coins = 500000
            reset = True
        elif streak >= 20:
            coins = random.randint(200, 300)*100
        elif streak >= 14:
            coins = random.randint(100, 200)*100
        elif streak >= 7:
            coins = random.randint(10, 100)*100
        else:
            coins = random.randint(1, 10)*100

        if reset == True:
            await self.db.update_one({"_id": user_id}, {"$set": {"daily_cooldown": current_time, "daily_streak": 0}, "$inc": {"wallet": coins}})
            await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: congratulations! you've claimed your daily reward of **{coins}** coins for **{streak}** days streak"))
            return
        
        await self.db.update_one({"_id": user_id}, {"$set": {"daily_cooldown": current_time}, "$inc": {"wallet": coins, "daily_streak": 1}})
        await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: congratulations! you've claimed your daily reward of **{coins}** coins for **{streak}** daily streak"))
    else:
        remaining_time_seconds = 86400 - (current_time - last)
        remaining_hours = remaining_time_seconds // 3600
        remaining_minutes = (remaining_time_seconds % 3600) // 60
        remaining_seconds = remaining_time_seconds % 60
        remaining_time_str = f"`{int(remaining_hours)}`h `{int(remaining_minutes)}`m `{int(remaining_seconds)}`s"
        await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have already claimed your daily reward, next claim available in {remaining_time_str}."))
  

  @commands.command(name="work", help="work for some coins")
  @commands.cooldown(1, 600, commands.BucketType.user)
  @commands.guild_only()
  async def work(self, ctx):
      data  = await self.db.find_one({"_id": str(ctx.author.id)})
      if not data:
          return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))
      
      wallet = data["wallet"]
      
      coin = random.randint(1, 10)*100

      await self.db.update_one({"_id": str(ctx.author.id)}, {"$inc": {"wallet": coin}})
      await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: congratulations! you put in the work and earned yourself **{coin}** shiny coins!"))


  @commands.command(name="crime", help="do crime for some coins")
  @commands.cooldown(1, 600, commands.BucketType.user)
  @commands.guild_only()
  async def crime(self, ctx):
      data  = await self.db.find_one({"_id": str(ctx.author.id)})
      if not data:
          return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))
      
      wallet = data["wallet"]
      
      if random.choice(['succ', 'fail']) == 'succ':
        coin = random.randint(1, 10)*100
        await self.db.update_one({"_id": str(ctx.author.id)}, {"$inc": {"wallet": coin}})
        await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: you successfully pulled off the heist and snagged **{coin}** coins"))
      else:
        coin = random.randint(1, 5)*100
        await self.db.update_one({"_id": str(ctx.author.id)}, {"$inc": {"wallet": -coin}})
        await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: oh no! you got caught red-handed and lost **{coin}** coins"))

  @commands.command(name="give", help="give someone some coins")
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.guild_only()
  async def give(self, ctx, user: discord.User, coins: int):
    sender_data = await self.db.find_one({"_id": str(ctx.author.id)})
    if not sender_data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you have not registered yet, use `register` command to register your account"))
    
    if user.id == ctx.author.id:
       return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you cant give coins to yourself"))
    
    if coins <= 0:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please enter a valid amount greater than 0"))

    sender_wallet = sender_data["wallet"]

    if coins > sender_wallet:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you don't have enough coins in your wallet"))

    recipient_data = await self.db.find_one({'_id': str(user.id)})
    if not recipient_data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: the recipient has not registered yet"))

    await self.db.update_one({"_id": str(ctx.author.id)}, {"$inc": {"wallet": -coins}})
    await self.db.update_one({"_id": str(user.id)}, {"$inc": {"wallet": coins}})

    await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: you have generously given {user.mention} **{coins}** coins!"))
  
  @commands.command(name="leaderboard", help="display the leaderboard based on wallet balance", aliases=['lb'])
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.guild_only()
  async def leaderboard(self, ctx):
    leaderboard = await self.db.find().sort("wallet", -1).limit(10).to_list(10)

    leaderboard_embed = discord.Embed(color=config.hex)
    for index, data in enumerate(leaderboard, start=1):
        user = ctx.guild.get_member(int(data["_id"]))
        if user:
            leaderboard_embed.add_field(name=f"#{index} {user.name}", value=f"`{data['wallet']}` coin(s)", inline=False)
    leaderboard_embed.set_author(name="Global Coins Leaderboard", icon_url=self.bot.user.avatar)
    await ctx.send(embed=leaderboard_embed)

  @commands.command(name="ecogive", help="Grant unlimited coins to any user (developer only)")
  @commands.guild_only()
  @commands.is_owner()
  async def ecogive(self, ctx, user: discord.User, coins: int):
        # Check if the coins amount is valid
        if coins <= 0:
            return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please enter a valid amount greater than 0"))

        # Check if the recipient is registered
        recipient_data = await self.db.find_one({'_id': str(user.id)})
        if not recipient_data:
            return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: the recipient has not registered yet"))

        # Update the recipient's wallet with the specified amount
        await self.db.update_one({"_id": str(user.id)}, {"$inc": {"wallet": coins}})

        # Notify the developer and the recipient
        await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: you have successfully granted {user.mention} **{coins}** coins!"))

  @commands.command(name="ecotake", help="Remove coins from a user (developer only)")
  @commands.guild_only()
  @commands.is_owner()
  async def ecotake(self, ctx, user: discord.User, coins: int):
    # Check if the coins amount is valid
    if coins <= 0:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please enter a valid amount greater than 0"))

    # Check if the recipient is registered
    recipient_data = await self.db.find_one({'_id': str(user.id)})
    if not recipient_data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: the recipient has not registered yet"))

    current_wallet = recipient_data["wallet"]

    # If the amount to remove is greater than their balance, set it to their total balance
    if coins > current_wallet:
        coins = current_wallet

    # Update the recipient's wallet by deducting the specified amount
    await self.db.update_one({"_id": str(user.id)}, {"$inc": {"wallet": -coins}})

    # Notify the developer and the recipient
    await ctx.reply(embed=create_embed(f"{config.coin_emoji} {ctx.author.mention}: you have successfully removed **{coins}** coins from {user.mention}'s wallet!"))        
        
async def setup(bot):
  await bot.add_cog(Economy(bot))
    
  