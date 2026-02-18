import discord
from discord import guild
from discord.ext import commands
from config import config
from config import mongo


def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed


class PingOnJoin(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.db = mongo.db.pingonjoin

  @commands.Cog.listener()
  async def on_member_join(self, member):
    if member.bot:
      return

    guild = member.guild
    data = await self.db.find_one({"_id": str(guild.id)})

    if data is None or data["toggle"] is False:
      return

    message = member.mention + " " + data["message"] if data[
        "message"] is not None else f"welcome to **{guild.name}** @ {member.mention}"
    for channel_id in data["channels"]:
      channel = guild.get_channel(int(channel_id))
      if channel is None:
        continue
      msg = await channel.send(message)

      await msg.delete(delay=data["delay"])

  @commands.group(invoke_without_command=True,
                  aliases=["poj"],
                  name="pingonjoin",
                  help="setup ping on join for your server")
  @commands.has_permissions(manage_guild=True)
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def pingonjoin_(self, ctx, toggle: str = "none"):

    if toggle == "none" and ctx.invoked_subcommand is None:
      embed = discord.Embed(
          title="PingOnJoin Subcommands:",
          description=
          f">>> `pingonjoin`, `pingonjoin channel`, `pingonjoin message`, `pingonjoin delay`\n{config.ques_emoji} Example: `pingonjoin enable`",
          color=config.hex)
      await ctx.reply(embed=embed)
    else:
      if toggle.lower() not in ["enable", "disable"]:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: invalid argument, avaiable arguments are `enable` and `disable`"
        ))

      bool = True if toggle.lower() == "enable" else False

      guild_data = await self.db.find_one({"_id": str(ctx.guild.id)})
      if guild_data is None:
        data = {
            "_id": str(ctx.guild.id),
            "toggle": bool,
            "channels": [],
            "message": None,
            "delay": 3
        }
        await self.db.insert_one(data)
      else:
        if guild_data["toggle"] == bool:
          return await ctx.reply(embed=create_embed(
              f"{config.error_emoji} {ctx.author.mention}: this server already has **{'enabled' if bool else 'disabled'}** ping on join"
          ))
        await self.db.update_one({"_id": str(ctx.guild.id)},
                                 {"$set": {
                                     "toggle": bool
                                 }})

      await ctx.reply(embed=create_embed(
          f"{config.tick} {ctx.author.mention}: successfully **{'enabled' if bool else 'disabled'}** ping on join for this server"
      ))

  @pingonjoin_.command(name="channel", help="add a channel to ping on join")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  async def pingonjoin_channel(self, ctx, action: str,
                               channel: discord.TextChannel):
    guild_data = await self.db.find_one({"_id": str(ctx.guild.id)})
    if guild_data is None or guild_data['toggle'] == False:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: this server has not enabled ping on join yet"
      ))

    if action.lower() not in ["add", "remove"]:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid action, available actions are `add` and `remove`"
      ))

    if action.lower() == "add":
      if channel.id in guild_data["channels"]:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: this channel is already added to ping on join"
        ))

      if len(guild_data['channels']) == 5:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: you can only add up to 5 channels to ping on join"
        ))

      await self.db.update_one({"_id": str(ctx.guild.id)},
                               {"$push": {
                                   "channels": channel.id
                               }})
      await ctx.reply(embed=create_embed(
          f"{config.added_emoji} {ctx.author.mention}: successfully added {channel.mention} to ping on join"
      ))

    else:
      if channel.id not in guild_data["channels"]:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: this channel is not added to ping on join"
        ))

      await self.db.update_one({"_id": str(ctx.guild.id)},
                               {"$pull": {
                                   "channels": channel.id
                               }})
      await ctx.reply(embed=create_embed(
          f"{config.removed_emoji} {ctx.author.mention}: successfully removed {channel.mention} from ping on join"
      ))

  @pingonjoin_.command(name="message", help="set a message to ping on join")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(manage_guild=True)
  @commands.guild_only()
  async def pingonjoin_message(self, ctx, *, message: str):
    guild_data = await self.db.find_one({"_id": str(ctx.guild.id)})
    if guild_data is None or guild_data['toggle'] == False:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: this server has not enabled ping on join yet"
      ))

    await self.db.update_one({"_id": str(ctx.guild.id)},
                             {"$set": {
                                 "message": message
                             }})
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully set ping on join message to:\n{message}"
    ))

  @pingonjoin_.command(
      name="delay", help="set a delay for deleting the ping on join message")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(manage_guild=True)
  @commands.guild_only()
  async def pingonjoin_delay(self, ctx, delay: int):
    guild_data = await self.db.find_one({"_id": str(ctx.guild.id)})
    if guild_data is None or guild_data['toggle'] == False:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: this server has not enabled ping on join yet"
      ))

    if delay < 1:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid argument, delay cannot be negative or 0"
      ))

    await self.db.update_one({"_id": str(ctx.guild.id)},
                             {"$set": {
                                 "delay": delay
                             }})
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully set ping on join delay to **{delay}** second(s)"
    ))


async def setup(bot):
  await bot.add_cog(PingOnJoin(bot))
