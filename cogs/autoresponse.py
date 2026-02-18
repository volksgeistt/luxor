import discord
from discord.ext import commands
import json
from config import config

class autoresponse(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.Cog.listener() 
  async def on_message(self, message: discord.Message) -> None:
        if message.author == self.client.user:
                return
        try:
            if message is not None:
                with open("db/autoresponse.json", "r") as f:
                    autoresponse = json.load(f)
                if str(message.guild.id) in autoresponse:
                    ans = autoresponse[str(message.guild.id)][message.content.lower()]
                    return await message.channel.send(ans)
        except:
            pass

  @commands.group(aliases=["ar","response","trigger"],description='show the help menu of autoresponse')
  @commands.has_permissions(manage_guild=True)
  async def autoresponse(self, ctx):
      if ctx.invoked_subcommand is None:
          await ctx.send(embed=discord.Embed(title="Autoresponse Subcommnads:", description=f">>> `autoresponse`, `autoresponse add`, `autoresponse remove`, `autoresponse update`, `autoresponse config`\n{config.ques_emoji} Example: `autoresponse add <ar_name> <response>`",color=config.hex))



  @autoresponse.command(aliases=["add",'a'],help='create autoresponse in the server')  
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def create(self, ctx, name , *, message):
        with open("db/autoresponse.json", "r") as f:
            autoresponse = json.load(f)
        numbers = []
        if str(ctx.guild.id) in autoresponse:
            for autoresponsecount in autoresponse[str(ctx.guild.id)]:
              numbers.append(autoresponsecount)
            if len(numbers) >= 10:
                return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.cross} {ctx.author.mention}: you can only have 10 autoresponders in a server."))
        if str(ctx.guild.id) in autoresponse:
            if name in autoresponse[str(ctx.guild.id)]:
                return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention}: the autoresponse `{name}` is already existing in the server."))
        if str(ctx.guild.id) in autoresponse:
            autoresponse[str(ctx.guild.id)][name] = message
            with open("db/autoresponse.json", "w") as f:
              json.dump(autoresponse, f, indent=4)
            return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.tick} {ctx.author.mention}: created an autoresponse `{name}`."))
        data = {
            name : message,
        }
        autoresponse[str(ctx.guild.id)] = data

        with open("db/autoresponse.json", "w") as f:
            json.dump(autoresponse, f, indent=4)
            return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.tick} {ctx.author.mention}: created an autoresponse `{name}`."))

  @autoresponse.command(aliases=["remove",'del','r','clear'],help='delete autoresponse in the server')
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()   
  @commands.has_permissions(manage_guild=True)
  async def delete(self, ctx, name):
        with open("db/autoresponse.json", "r") as f:
            autoresponse = json.load(f)

        if str(ctx.guild.id) in autoresponse:
            if name in autoresponse[str(ctx.guild.id)]:
                del autoresponse[str(ctx.guild.id)][name]
                with open("db/autoresponse.json", "w") as f:
                    json.dump(autoresponse, f, indent=4)
                return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.tick} {ctx.author.mention}: cleared autoresponse `{name}` for this server."))
            else:
                return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.cross} {ctx.author.mention}: no autoresponse found with name `{name}` for this server."))
        else:
            return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.cross} {ctx.author.mention}: autoresponse is not configured for this server."))
          
  @autoresponse.command(help='edit the old created autoresponse of server', aliases=["update"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def edit(self, ctx, name , *, message):
        with open("db/autoresponse.json", "r") as f:
            autoresponse = json.load(f)
        if str(ctx.guild.id) in autoresponse:
            if name in autoresponse[str(ctx.guild.id)]:
                autoresponse[str(ctx.guild.id)][name] = message
                with open("db/autoresponse.json", "w") as f:
                    json.dump(autoresponse, f, indent=4)
                return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.tick} {ctx.author.mention}: updated the autoresponse `{name}`"))
        else:
            return await ctx.send(embed=discord.Embed(color=config.hex, description=f"{config.cross} {ctx.author.mention}: autoresponse is not configured for this server."))
          
  @autoresponse.command(aliases=["show", "config"],help='shows all autoresponses of server')
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def list(self, ctx):
        with open("db/autoresponse.json", "r") as f:
            autoresponse = json.load(f)
        autoresponsenames = []
        if str(ctx.guild.id) in autoresponse:
            for autoresponsecount in autoresponse[str(ctx.guild.id)]:  
              autoresponsenames.append(autoresponsecount)
            embed = discord.Embed(color=config.hex)
            st, count = "", 1
            for autoresponse in autoresponsenames:
                    st += f"`{'0' + str(count) if count < 20 else count}` **{autoresponse}**\n"
                    test = count
                    count += 1
            embed.title = f"Autoresponders - {test}"
        embed.description = st
        await ctx.send(embed=embed)

async def setup(bot):
  await bot.add_cog(autoresponse(bot))