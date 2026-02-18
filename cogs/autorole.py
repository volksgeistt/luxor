import discord
from discord.ext import commands
from config import config
from config import mongo

def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed

class Autorole(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.db = mongo.db.autorole
    

  @commands.Cog.listener()
  async def on_member_join(self, member):
    guild = member.guild
    data = await self.db.find_one({"_id": str(guild.id)})
    if data is None:
      return
    if not member.bot:
      roles = data['humans']
      if len(roles) == 0:
        return
      for role in roles:
        role_ = guild.get_role(role)
        if role_:
          try:
             await member.add_roles(role_, reason="@ Luxor : human autorole")
          except:
           pass
            
    elif member.bot:
      roles = data['bots']

      if len(roles) == 0:
        return

      for role in roles:
        role_ = guild.get_role(role)
        if role_:
          try:
             await member.add_roles(role_, reason="@ Luxor : bot autorole")
          except:
            pass
          
  @commands.group(name="autorole", aliases=['autor'], help="setup autorole for your server", invoke_without_command=True)
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def autorole(self, ctx, toggle="none"):
    if toggle == "none" and ctx.invoked_subcommand is None:
      return await ctx.reply(embed=discord.Embed(description=f">>> `autorole`, `autorole enable`, `autorole disable`, `autorole humans`, `autorole bots`\n{config.ques_emoji} Example: `autorole <humans/bots> <add/remove/show/reset> <role>`", color=config.hex, title="Autorole Subcommands"))

    if toggle.lower() not in ['enable', 'disable']:
      return await ctx.reply(embed=create_embed(
        f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `enable` and `disable`"
    ))

    if toggle.lower() == 'enable':
      data = await self.db.find_one({"_id": str(ctx.guild.id)})
      
      if data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: autorole is already enabled"))
        
      await self.db.insert_one({"_id": str(ctx.guild.id), "humans": [], "bots": []})
      return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully enabled autorole, use `autorole humans/bots`"))
    elif toggle.lower() == 'disable':
      data = await self.db.find_one({"_id": str(ctx.guild.id)})
      
      if not data:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: autorole is not enabled is this server"))
        
      await self.db.delete_one({"_id": str(ctx.guild.id)})
      return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully disabled autorole for this server"))

  @autorole.command(name="humans", aliases=['human'], help="add or remove role for human autorole")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def autorole_human(self, ctx, arg, role: discord.Role=None):
    data = await self.db.find_one({"_id": str(ctx.guild.id)})
    if not data:
      return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: autorole is not enabled in this server"))

    if arg.lower() not in ['add', 'remove', 'show', 'reset']:
      return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `add`, `remove`, `show`, `reset`"))

    if arg.lower() == 'add':
      if role == None:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please provide a role to add it to human autorole"))
      if role.id in data['humans']:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: role is already added in human autorole"))

      if len(data['humans']) == 3:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you cant have more than 3 roles in human autorole"))
        
      data['humans'].append(role.id)
      await self.db.update_one({"_id": str(ctx.guild.id)}, {"$set": data})
      return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully added {role.mention} in human autorole"))

    elif arg.lower() == 'remove':
      if role == None:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please provide a role to remove it from autorole"))
      if role.id not in data['humans']:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: role is not in human autorole"))
        
      data['humans'].remove(role.id)
      await self.db.update_one({"_id": str(ctx.guild.id)}, {"$set": data})
      return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully removed {role.mention} from human autorole"))

    elif arg.lower() == 'show':
      if not data['humans']:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: no role in human autorole found for this server"))

      roles = [f"`{i+1}` <@&{role}> `[{role}]`" for i, role in enumerate(data['humans'])]
      embed = discord.Embed(description="\n".join(roles), color=config.hex).set_author(name="Human Autoroles", icon_url=ctx.guild.icon)
      await ctx.reply(embed=embed)

    elif arg.lower() == 'reset':
      if not data['humans']:
        return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: no role in human autorole found for this server"))
      data['humans'] = []
      await self.db.update_one({"_id": str(ctx.guild.id)}, {"$set": data})
      return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully reset human autorole"))
    
  @autorole.command(name="bots", help="add or remove role for bot autorole")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def autorole_bots(self, ctx, arg, role: discord.Role=None):
      data = await self.db.find_one({"_id": str(ctx.guild.id)})
      if not data:
          return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: autorole is not enabled in this server"))

      if arg.lower() not in ['add', 'remove', 'show', 'reset']:
          return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `add`, `remove`, `show`, `reset`"))

      if arg.lower() == 'add':
          if role == None:
            return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please provide a role to add it to bot autorole"))
          if role.id in data['bots']:
              return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: role is already added in bot autorole"))

          if len(data['bots']) == 3:
              return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: you cant have more than 3 roles in bot autorole"))

          data['bots'].append(role.id)
          await self.db.update_one({"_id": str(ctx.guild.id)}, {"$set": data})
          return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully added {role.mention} in bot autorole"))

      elif arg.lower() == 'remove':
          if role == None:
            return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: please provide a role to remove it from bot autorole"))
          
          if role.id not in data['bots']:
              return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: role is not in bot autorole"))

          data['bots'].remove(role.id)
          await self.db.update_one({"_id": str(ctx.guild.id)}, {"$set": data})
          return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully removed {role.mention} from bot autorole"))

      elif arg.lower() == 'show':
          if not data['bots']:
              return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: no role in bot autorole found for this server"))

          roles = [f"`{i+1}` <@&{role}> `[{role}]`" for i, role in enumerate(data['bots'])]
          embed = discord.Embed(description="\n".join(roles), color=config.hex).set_author(name="Bot Autoroles", icon_url=ctx.guild.icon)
          await ctx.reply(embed=embed)

      elif arg.lower() == 'reset':
          if not data['bots']:
              return await ctx.reply(embed=create_embed(f"{config.error_emoji} {ctx.author.mention}: no role in bot autorole found for this server"))
          data['bots'] = []
          await self.db.update_one({"_id": str(ctx.guild.id)}, {"$set": data})
          return await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully reset bot autorole"))


async def setup(bot):
  await bot.add_cog(Autorole(bot))