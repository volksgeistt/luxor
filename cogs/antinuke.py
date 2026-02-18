import discord
import aiohttp
import asyncio
from discord.ext import commands, tasks
from config import mongo
import config
from datetime import datetime, timedelta
import colorama
from colorama import Fore


def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed


class Antinuke(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.db = mongo.db.antinuke
    self.headers = {"Authorization": f"Bot {self.bot.http.token}"}
    self.session = aiohttp.ClientSession(headers=self.headers)
    self.cache = {}
    self.antinuke_cache.start()

  @tasks.loop(hours=12)
  async def antinuke_cache(self):
    data = self.db.find({})
    new_cache = {}
    for d in await data.to_list(length=None):
      print(f"{Fore.YELLOW}[ Antinuke Cache ] : added {d['_id']}" + Fore.RESET)
      new_cache[d["_id"]] = d
    self.cache = new_cache

  async def get_data(self, guild_id):
    guild_id = str(guild_id)
    if guild_id in self.cache:
      return self.cache[guild_id]
    else:
      data = await self.db.find_one({"_id": str(guild_id)})
      if data:
        self.cache[guild_id] = data
        return data
      else:
        return None

  async def cache_data(self, guild_id):
    guild_id = str(guild_id)
    data = await self.db.find_one({"_id": str(guild_id)})
    if data:
      self.cache[guild_id] = data
      return data
    else:
      return None

  @commands.group(name="antinuke",
                  aliases=["an"],
                  invoke_without_command=True,
                  help="enable or disable antinuke")
  async def antinuke_grp(self, ctx, toggle: str = "none"):
    if ctx.author.id != ctx.guild.owner.id and ctx.author.id not in config.owner_ids:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: only the guild owner can use this command"
      ))

    if toggle == "none" and ctx.invoked_subcommand is None:
      return await ctx.reply(embed=discord.Embed(
          title="Antinuke Subcommands:",
          color=config.hex,
          description=
          f">>> `antinuke`, `antinuke setup`, `antinuke enable`, `antinuke disable`, `antinuke whitelist add`, `antinuke whitelist remove`, `antinuke whitelist show`, `antinuke settings`, `antinuke logs`, `antinuke punishment`\n{config.ques_emoji} Example: `antinuke setup`"
      ))

    if toggle.lower() not in ['enable', 'disable']:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid argument, available arguments are `enable` and `disable`"
      ))
  
    data = await self.db.find_one({"_id": str(ctx.guild.id)})

    if data is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: server not found in database, use `antinuke setup` to setup antinuke"
      ))

    if toggle.lower() == "enable":
      view = self.enable_functions_view(ctx, self.db, self.cache)
      await ctx.reply(embed=create_embed(
          f"{config.ques_emoji} {ctx.author.mention}: select the antinuke functions to enable"
      ),
                      view=view)
    else:
      view = self.disable_functions_view(ctx, self.db, self.cache)
      await ctx.reply(embed=create_embed(
          f"{config.ques_emoji} {ctx.author.mention}: select the antinuke functions to disable"
      ),
                      view=view)

  @antinuke_grp.command(name="setup", help="setup antinuke of your server")
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def antinuke_setup(self, ctx):
    if ctx.author.id != ctx.guild.owner.id and ctx.author.id not in config.owner_ids:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: only the guild owner can use this command"
      ))

    data = await self.db.find_one({"_id": str(ctx.guild.id)})

    if data is not None:
      return await ctx.reply(embed=create_embed(
          f"{config.cross} {ctx.author.mention}: antinuke is already setuped in this server"
      ))

    msg = await ctx.reply(embed=create_embed(
        f"{config.config_emoji} {ctx.author.mention}: setting up antinuke in this server"
    ))

    await asyncio.sleep(1)

    if not ctx.guild.me.guild_permissions.administrator:
      return await msg.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: antinuke setup failed, i don't have administrator permission"
      ))

    await asyncio.sleep(1)

    log_channel = discord.utils.get(ctx.guild.channels,
                                    name="Luxor-antinuke-logs")
    if log_channel is None:
      try:
        log_channel = await ctx.guild.create_text_channel("Luxor-antinuke-logs")
        overwrite = log_channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await log_channel.set_permissions(ctx.guild.default_role,
                                          overwrite=overwrite)
      except:
        return await msg.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: antinuke setup failed, unable to setup the log channel"
        ))

    await asyncio.sleep(1)

    data_ = {
        "_id": str(ctx.guild.id),
        "whitelist": [],
        "log_channel": log_channel.id,
        "punishment": "ban",
        "functions": {
            "anti_bot": False,
            "anti_ban": False,
            "anti_kick": False,
            "anti_channel_create": False,
            "anti_channel_delete": False,
            "anti_channel_update": False,
            "anti_role_create": False,
            "anti_role_delete": False,
            "anti_role_update": False,
            "anti_server_update": False,
            "anti_member_update": False,
        }
    }

    await self.db.insert_one(data_)

    await msg.reply(embed=create_embed(
        f">>> {config.tick} {ctx.author.mention}: antinuke setup complete\n{config.ques_emoji} use `antinuke enable` to enable antinuke functions"
    ))
    await self.cache_data(ctx.guild.id)

  class enable_functions_view(discord.ui.View):

    def __init__(self, ctx, db, cache):
        super().__init__(timeout=120)
        self.auth = ctx.author
        self.db = db
        self.cache = cache

    @discord.ui.select(placeholder="Select functions to enable",
                       min_values=1,
                       custom_id="enbview",
                       max_values=11,
                       options=[
                           discord.SelectOption(label="Anti ban"),
                           discord.SelectOption(label="Anti kick"),
                           discord.SelectOption(label="Anti bot"),
                           discord.SelectOption(label="Anti server update"),
                           discord.SelectOption(label="Anti member update"),
                           discord.SelectOption(label="Anti channel create"),
                           discord.SelectOption(label="Anti channel delete"),
                           discord.SelectOption(label="Anti channel update"),
                           discord.SelectOption(label="Anti role create"),
                           discord.SelectOption(label="Anti role delete"),
                           discord.SelectOption(label="Anti role update")
                       ])
    async def select_callback(self, interaction, select):
        await self.process_functions(interaction, interaction.data["values"])

    @discord.ui.button(label="Enable All", style=discord.ButtonStyle.green, custom_id="enable_all")
    async def enable_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        all_functions = [
            "Anti ban", "Anti kick", "Anti bot", "Anti server update", "Anti member update",
            "Anti channel create", "Anti channel delete", "Anti channel update",
            "Anti role create", "Anti role delete", "Anti role update"
        ]
        await self.process_functions(interaction, all_functions)

    async def process_functions(self, interaction, values):
        funcs = []
        function_mapping = {
            "Anti ban": "anti_ban",
            "Anti kick": "anti_kick",
            "Anti bot": "anti_bot",
            "Anti channel create": "anti_channel_create",
            "Anti channel delete": "anti_channel_delete",
            "Anti channel update": "anti_channel_update",
            "Anti role create": "anti_role_create",
            "Anti role delete": "anti_role_delete",
            "Anti role update": "anti_role_update",
            "Anti server update": "anti_server_update",
            "Anti member update": "anti_member_update"
        }

        for val in values:
            function = function_mapping.get(val)
            if function:
                funcs.append(function)

        query = {"$set": {"functions." + func: True for func in funcs}}
        await self.db.update_one({"_id": str(interaction.guild.id)}, query)
        data_c = await self.db.find_one({"_id": str(interaction.guild.id)})
        self.cache[str(interaction.guild.id)] = data_c

        self.children[0].disabled = True  # Disable the select menu
        self.children[1].disabled = True  # Disable the button
        await interaction.response.edit_message(view=self)
        await interaction.message.reply(embed=create_embed(
            f">>> {config.tick} Successfully enabled the following functions:\n`{'`, `'.join(funcs)}`"
        ))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.auth.id:
            await interaction.response.send_message(
                f"{config.cross} {interaction.user.mention}: This interaction is not for you!",
                ephemeral=True)
            return False
        return True

  class disable_functions_view(discord.ui.View):

    def __init__(self, ctx, db, cache):
      super().__init__(timeout=120)
      self.auth = ctx.author
      self.db = db
      self.cache = cache

    @discord.ui.select(placeholder="Select a function to disable",
                       min_values=1,
                       custom_id="disbview",
                       max_values=11,
                       options=[
                           discord.SelectOption(label="Anti ban"),
                           discord.SelectOption(label="Anti kick"),
                           discord.SelectOption(label="Anti bot"),
                           discord.SelectOption(label="Anti server update"),
                           discord.SelectOption(label="Anti member update"),
                           discord.SelectOption(label="Anti channel create"),
                           discord.SelectOption(label="Anti channel delete"),
                           discord.SelectOption(label="Anti channel update"),
                           discord.SelectOption(label="Anti role create"),
                           discord.SelectOption(label="Anti role delete"),
                           discord.SelectOption(label="Anti role update")
                       ])
    async def select_callback(self, interaction, select):

      values = interaction.data["values"]
      funcs = []

      for val in values:
        function = ""
        if val == "Anti ban":
          function = "anti_ban"
        elif val == "Anti kick":
          function = "anti_kick"
        elif val == "Anti bot":
          function = "anti_bot"
        elif val == "Anti channel create":
          function = "anti_channel_create"
        elif val == "Anti channel delete":
          function = "anti_channel_delete"
        elif val == "Anti channel update":
          function = "anti_channel_update"
        elif val == "Anti role create":
          function = "anti_role_create"
        elif val == "Anti role delete":
          function = "anti_role_delete"
        elif val == "Anti role update":
          function = "anti_role_update"
        elif val == "Anti server update":
          function = "anti_server_update"
        elif val == "Anti member update":
          function = "anti_member_update"

        if function:
          funcs.append(function)

      # Update the database
      query = {"$set": {"functions." + func: False for func in funcs}}
      await self.db.update_one({"_id": str(interaction.guild.id)}, query)
      data_c = await self.db.find_one({"_id": str(interaction.guild.id)})
      self.cache[str(interaction.guild.id)] = data_c

      # Disable the select menu and update the message
      select.disabled = True
      await interaction.response.edit_message(view=self)
      await interaction.followup.send(embed=create_embed(
          f">>> {config.tick} successfully disabled following functions:\n`{'`, `'.join(funcs)}`"
      ))

    @discord.ui.button(label="Disable All", style=discord.ButtonStyle.danger, custom_id="disable_all")
    async def disable_all_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
      all_functions = [
          "anti_ban", "anti_kick", "anti_bot", "anti_server_update", 
          "anti_member_update", "anti_channel_create", "anti_channel_delete", 
          "anti_channel_update", "anti_role_create", "anti_role_delete", "anti_role_update"
      ]

      query = {"$set": {"functions." + func: False for func in all_functions}}
      await self.db.update_one({"_id": str(interaction.guild.id)}, query)
      data_c = await self.db.find_one({"_id": str(interaction.guild.id)})
      self.cache[str(interaction.guild.id)] = data_c

      button.disabled = True
      await interaction.response.edit_message(view=self)
      await interaction.followup.send(embed=create_embed(
          f">>> {config.tick} Successfully disabled all functions."
      ))

    async def interaction_check(self, interaction: discord.Interaction):
      if interaction.user.id != self.auth.id:
        await interaction.response.send_message(
            f"{config.cross} {interaction.user.mention}: this interaction is not for you!",
            ephemeral=True)
        return False
      return True


  @antinuke_grp.command(name="settings",
                        help="shows antinuke settings for your server",
                        aliases=["config", "setting"])
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def antinuke_sett(self, ctx):
    if ctx.author.id != ctx.guild.owner.id and ctx.author.id not in config.owner_ids:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: only the guild owner can use this command"
      ))

    data = await self.db.find_one({"_id": str(ctx.guild.id)})

    if data is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: server not found in database, use `antinuke setup` to setup antinuke"
      ))

    log = f"<#{data['log_channel']}>" if ctx.guild.get_channel(
        data['log_channel']) else 'not found..'
    embed = create_embed(
        f">>> Log channel: {log}\nPunishmemt: `{data['punishment']}`\nThreat mode: `{"enabled" if data.get("threatmode", False) else "disabled"}`")
    embed.set_author(name=f'Antinuke settings', icon_url=ctx.guild.icon)
    funcs_str = f"""

  anti bot: {str(data['functions']['anti_bot']).lower()}
  anti ban: {str(data['functions']['anti_ban']).lower()}
  anti kick: {str(data['functions']['anti_kick']).lower()}
  anti server update: {str(data['functions']['anti_server_update']).lower()}
  anti member update: {str(data['functions']['anti_member_update']).lower()}
  anti channel create: {str(data['functions']['anti_channel_create']).lower()}
  anti channel delete: {str(data['functions']['anti_channel_delete']).lower()}
  anti channel update: {str(data['functions']['anti_channel_update']).lower()}
  anti role create: {str(data['functions']['anti_role_create']).lower()}
  anti role delete: {str(data['functions']['anti_role_delete']).lower()}
  anti role update: {str(data['functions']['anti_role_update']).lower()}
    """
    
    embed.add_field(name="Functions:", value="```\n{" + funcs_str + "\n}```")
    await ctx.reply(embed=embed)

  @antinuke_grp.command(name="whitelist",
                        help="whitelist a user from antinuke",
                        aliases=["wl"])
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def antinuke_wl(self, ctx, action: str, user: discord.Member = None):
    if ctx.author.id != ctx.guild.owner.id and ctx.author.id not in config.owner_ids:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: only the guild owner can use this command"
      ))

    data = await self.db.find_one({"_id": str(ctx.guild.id)})

    if data is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: server not found in database, use `antinuke setup` to setup antinuke"
      ))

    if action.lower() == "add":
      if user is None:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: please provide a user to whitelist"
        ))

      if user.id in data['whitelist']:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: {user.mention} is already whitelisted"
        ))

      data['whitelist'].append(user.id)
      await self.db.update_one({"_id": str(ctx.guild.id)},
                               {"$set": {
                                   "whitelist": data['whitelist']
                               }})

      await ctx.reply(embed=create_embed(
          f"{config.tick} {ctx.author.mention}: successfully added {user.mention} to antinuke whitelist"
      ))
    elif action.lower() == "remove":
      if user is None:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: please provide a user to remove from whitelist"
        ))

      if user.id not in data['whitelist']:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: {user.mention} is not whitelisted"
        ))
      data['whitelist'].remove(user.id)

      await self.db.update_one({"_id": str(ctx.guild.id)},
                               {"$set": {
                                   "whitelist": data['whitelist']
                               }})
      await ctx.reply(embed=create_embed(
          f"{config.tick} {ctx.author.mention}: successfully removed {user.mention} from antinuke whitelist"
      ))
    elif action.lower() == "show":

      if not data['whitelist']:
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: no whitelisted users found for this server"
        ))

      str_ = ""
      for i, user in enumerate(data['whitelist'], start=1):
        str_ += f"`{i}` <@{user}> `({user})`\n"

      embed = create_embed(str_)
      embed.set_author(name=f"Whitelisted users for {ctx.guild.name}",
                       icon_url=ctx.guild.icon)
      return await ctx.reply(embed=embed)
    else:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid action, use `add`, `remove` or `show`"
      ))
    await self.cache_data(ctx.guild.id)

  @antinuke_grp.command(name="punishment",
                        help="set punishment for antinuke",
                        aliases=["punish"])
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def antinuke_punish(self, ctx, punishment: str):
    if ctx.author.id != ctx.guild.owner.id and ctx.author.id not in config.owner_ids:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: only the guild owner can use this command"
      ))

    data = await self.db.find_one({"_id": str(ctx.guild.id)})

    if data is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: server not found in database, use `antinuke setup` to setup antinuke"
      ))

    if punishment.lower() == "ban":
      if data['punishment'] == "ban":
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: antinuke punishment is already set to ban"
        ))
      data['punishment'] = "ban"
      await self.db.update_one({"_id": str(ctx.guild.id)},
                               {"$set": {
                                   "punishment": data['punishment']
                               }})
      await ctx.reply(embed=create_embed(
          f"{config.tick} {ctx.author.mention}: successfully set antinuke punishment to ban"
      ))
    elif punishment.lower() == "kick":
      if data['punishment'] == "kick":
        return await ctx.reply(embed=create_embed(
            f"{config.error_emoji} {ctx.author.mention}: antinuke punishment is already set to kick"
        ))
      data['punishment'] = "kick"
      await self.db.update_one({"_id": str(ctx.guild.id)},
                               {"$set": {
                                   "punishment": data['punishment']
                               }})
      await ctx.reply(embed=create_embed(
          f"{config.tick} {ctx.author.mention}: successfully set antinuke punishment to kick"
      ))
    else:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid punishment, use `ban` or `kick`"
      ))

    await self.cache_data(ctx.guild.id)

  @antinuke_grp.command(name="logging",
                        help="set logging channel for antinuke",
                        aliases=["logs", "log", "loggings"])
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def antinuke_log(self, ctx, channel: discord.TextChannel):
    if ctx.author.id != ctx.guild.owner.id and ctx.author.id not in config.owner_ids:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: only the guild owner can use this command"
      ))

    data = await self.db.find_one({"_id": str(ctx.guild.id)})

    if data is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: server not found in database, use `antinuke setup` to setup antinuke"
      ))

    if channel.id == data['log_channel']:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: logging channel is already set to {channel.mention}"
      ))

    data['log_channel'] = channel.id
    await self.db.update_one({"_id": str(ctx.guild.id)},
                             {"$set": {
                                 "log_channel": data['log_channel']
                             }})
    await ctx.reply(embed=create_embed(
        f"{config.tick} {ctx.author.mention}: successfully set logging channel to {channel.mention}"
    ))
    await self.cache_data(ctx.guild.id)

  @antinuke_grp.command(name="threatmode",
                        help="enable/disable antinuke threat mode",
                        aliases=["threat"])
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def antinuke_threatmode(self, ctx, toggle):
    if ctx.author.id != ctx.guild.owner.id and ctx.author.id not in config.owner_ids:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: only the guild owner can use this command"
      ))

    data = await self.db.find_one({"_id": str(ctx.guild.id)})

    if data is None:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: server not found in database, use `antinuke setup` to setup antinuke"
      ))

    if toggle.lower() not in ['enable', 'disable']:
      return await ctx.reply(embed=create_embed(
          f"{config.error_emoji} {ctx.author.mention}: invalid toggle, use `enable` or `disable`"
      ))

    togg = True if toggle.lower() == 'enable' else False

    await self.db.update_one({"_id": str(ctx.guild.id)},
                             {"$set": {
                                 "threatmode": togg
                             }})
    
    await ctx.reply(embed=create_embed(f"{config.tick} {ctx.author.mention}: successfully **{'enabled' if togg else 'disabled'}** threat mode{f"\n{config.error_emoji} any action taken by whitelisted or non whitelisted member will trigger the bot" if togg else ""}"))
    await self.cache_data(ctx.guild.id)

  async def punish(self, guild, user, punishment, reason):
    try:
        if punishment == "ban":
            async with self.session.put(
                f"https://discord.com/api/v9/guilds/{guild.id}/bans/{user.id}",
                json={"reason": reason}) as r:
                if r.status in (200, 201, 204):
                    return "banned"
                else:
                    return "failed"
        elif punishment == "kick":
            async with self.session.delete(
                f"https://discord.com/api/v9/guilds/{guild.id}/members/{user.id}",
                json={"reason": reason}) as r:
                if r.status in (200, 201, 204):
                    return "kicked"
                else:
                    return "failed"
    except Exception as e:
        return "failed"

  async def send_log(self, channel, user, action, punishment):
    embed = create_embed(None)
    embed.set_author(name=f"Luxor antinuke loggings",
                     icon_url=self.bot.user.avatar)
    embed.add_field(name="User", value=f"{user} `({user.id})`")
    embed.add_field(name="Action", value=f"{action}")
    embed.add_field(name="Punishment Status", value=f"{punishment}")
    embed.set_thumbnail(url=user.avatar)
    try:
      await self.bot.get_channel(channel).send(embed=embed)
    except:
      return
    
  def check_wl(self, user, data, guild):
    if data.get("threatmode", False) is True:
      if user.id != guild.owner.id and user.id != self.bot.user.id:
        return False # no wl
      else:
        return True # wl
    else:
      if (user.id not in data['whitelist'] and user.id != self.bot.user.id and user.id != guild.owner.id):
        return False # no wl
      else:
        return True # wl
    

  @commands.Cog.listener()
  async def on_guild_channel_create(self, channel):
    guild = channel.guild

    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_channel_create", False) == False:
      return

    async for entry in guild.audit_logs(
        limit=1, action=discord.AuditLogAction.channel_create):
      if entry.target.id == channel.id:
        user = entry.user

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized channel create")
            await channel.delete(reason="@ Luxor antinuke recovery")
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="created channel",
                                punishment=punish)

  @commands.Cog.listener()
  async def on_guild_channel_delete(self, channel):
    guild = channel.guild

    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_channel_delete", False) == False:
      return

    async for entry in guild.audit_logs(
        limit=1, action=discord.AuditLogAction.channel_delete):
      if entry.target.id == channel.id:
        user = entry.user

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized channel delete")
            ch = await channel.clone(reason="@ Luxor antinuke recovery")
            await ch.edit(position=channel.position)
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="deleted channel",
                                punishment=punish)

  @commands.Cog.listener()
  async def on_guild_channel_update(self, before, after):
    guild = after.guild

    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_channel_update", False) == False:
      return

    channel = after

    async for entry in guild.audit_logs(
        limit=1, action=discord.AuditLogAction.channel_update):
      if entry.target.id == channel.id:
        user = entry.user
        guild = entry.guild

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized channel update")

            if before.name != after.name:
              await channel.edit(name=before.name,
                                 reason="@ Luxor antinuke recovery")
            if before.topic != after.topic:
              await channel.edit(topic=before.topic,
                                 reason="@ Luxor antinuke recovery")
            if before.nsfw != after.nsfw:
              await channel.edit(nsfw=before.nsfw,
                                 reason="@ Luxor antinuke recovery")
            if before.slowmode_delay != after.slowmode_delay:
              await channel.edit(slowmode_delay=before.slowmode_delay,
                                 reason="@ Luxor antinuke recovery")
            if before.category != after.category:
              await channel.edit(category=before.category,
                                 reason="@ Luxor antinuke recovery")
            if before.position != after.position:
              await channel.edit(position=before.position,
                                 reason="@ Luxor antinuke recovery")
            if before.overwrites != after.overwrites:
              await channel.edit(overwrites=before.overwrites,
                                 reason="@ Luxor antinuke recovery")

          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="deleted channel",
                                punishment=punish)

  @commands.Cog.listener()
  async def on_guild_role_create(self, role):
    guild = role.guild

    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_role_create", False) == False:
      return

    async for entry in guild.audit_logs(
        limit=1, action=discord.AuditLogAction.role_create):
      if entry.target.id == role.id:
        user = entry.user

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized role create")
            await role.delete(reason="@ Luxor antinuke recovery")
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="created role",
                                punishment=punish)

  @commands.Cog.listener()
  async def on_guild_role_delete(self, role):
    guild = role.guild

    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_role_delete", False) == False:
      return

    async for entry in guild.audit_logs(
        limit=1, action=discord.AuditLogAction.role_delete):
      if entry.target.id == role.id:
        user = entry.user

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized role delete")
            role = await guild.create_role(name=role.name,
                                    color=role.color,
                                    permissions=role.permissions,
                                    hoist=role.hoist,
                                    mentionable=role.mentionable,
                                    reason="@ Luxor antinuke recovery")
            await role.edit(position=role.position, reason="@ Luxor antinuke recovery")
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="deleted role",
                                punishment=punish)

  @commands.Cog.listener()
  async def on_guild_role_update(self, before, after):
    guild = after.guild

    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_role_update", False) == False:
      return

    async for entry in guild.audit_logs(
      limit=1, action=discord.AuditLogAction.role_update):
      if entry.target.id == after.id:
        user = entry.user
        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized role update")

            if before.name != after.name:
              await after.edit(name=before.name,  reason="@ Luxor antinuke recovery")
            if before.permissions != after.permissions:
              await after.edit(permissions=before.permissions,  reason="@ Luxor antinuke recovery")
            if before.color != after.color:
              await after.edit(color=before.color,  reason="@ Luxor antinuke recovery")
            if before.hoist != after.hoist:
              await after.edit(hoist=before.hoist,  reason="@ Luxor antinuke recovery")
            if before.position != after.position:
              print("pos")
              await after.edit(position=before.position,  reason="@ Luxor antinuke recovery")
              
            if before.mentionable != after.mentionable:
              await after.edit(mentionable=before.mentionable,  reason="@ Luxor antinuke recovery")
            if before.managed != after.managed:
              await after.edit(managed=before.managed,  reason="@ Luxor antinuke recovery")
            if before.display_icon != after.display_icon:
              await after.edit(display_icon=before.display_icon,  reason="@ Luxor antinuke recovery")
          except:
            pass

          if punish:
              await self.send_log(channel=data['log_channel'],
                              user=user,
                              action="updated role",
                              punishment=punish)

  @commands.Cog.listener()
  async def on_member_ban(self, guild, user):
    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_ban", False) == False:
      return

    async for entry in guild.audit_logs(
        limit=1, action=discord.AuditLogAction.ban):
      if entry.target.id == user.id:
        user = entry.user

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized ban")
            await guild.unban(user, reason="@ Luxor antinuke recovery")
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="banned member",
                                punishment=punish)

  @commands.Cog.listener()
  async def on_member_remove(self, member):
    guild = member.guild
    data = await self.get_data(member.guild.id)

    if data is None:
      return 

    if data['functions'].get("anti_kick", False) == False:
      return

    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
      if entry.target.id == member.id:
        user = entry.user

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                member.guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized kick")
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="kicked member",
                                punishment=punish)

  @commands.Cog.listener()
  async def on_member_update(self, before, after):
    guild = after.guild

    data = await self.get_data(guild.id)

    if data is None:
      return

    if data['functions'].get("anti_member_update", False) == False:
      return

    async for entry in guild.audit_logs(
        limit=1, action=discord.AuditLogAction.member_role_update):
      
      if entry.target.id == after.id:
        user = entry.user
        if not self.check_wl(user, data, guild):
         if user.guild_permissions.manage_roles:
          punish = None
          try:
            punish = await self.punish(
                guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized member update")

            if before.roles != after.roles:
              await after.edit(roles=before.roles, reason="@ Luxor antinuke recovery")
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="updated member",
                                punishment=punish)
            
  @commands.Cog.listener()
  async def on_member_join(self, member):
    guild = member.guild
    data = await self.get_data(member.guild.id)

    if data is None:
      return

    if data['functions'].get("anti_bot", False) == False:
      return

    if member.bot:
      async for entry in member.guild.audit_logs(
          limit=1, action=discord.AuditLogAction.bot_add):
        user = entry.user

        if not self.check_wl(user, data, guild):
          punish = None
          try:
            punish = await self.punish(
                member.guild, user, data['punishment'],
                "Luxor antinuke @ unauthorized bot add")
            await member.ban(reason="Luxor antinuke @ anti bot add")
          except:
            pass

          if punish:
            await self.send_log(channel=data['log_channel'],
                                user=user,
                                action="added bot",
                                punishment=punish)

  
  @commands.Cog.listener()
  async def on_guild_update(self, before, after):
    guild= after
    data = await self.get_data(after.id)

    if data is None:
      return
      
    if data['functions'].get("anti_server_update", False) == False:
      return
      
    async for entry in after.audit_logs(
        limit=1, action=discord.AuditLogAction.guild_update):
      user = entry.user
      if not self.check_wl(user, data, guild):
        punish = None
        try:
          punish = await self.punish(
              after, user, data['punishment'],
              "Luxor antinuke @ unauthorized guild update")
          if before.name != after.name:
            await after.edit(name=before.name, reason="@ Luxor antinuke recovery")
          if before.icon != after.icon:
            await after.edit(icon=before.icon.url, reason="@ Luxor antinuke recovery")
          if before.banner != after.banner:
            await after.edit(banner=before.banner, reason="@ Luxor antinuke recovery")
          if before.region != after.region:
            await after.edit(region=before.region, reason="@ Luxor antinuke recovery")
          if before.system_channel != after.system_channel:
            await after.edit(system_channel=before.system_channel, reason="@ Luxor antinuke recovery")
          if before.afk_channel != after.afk_channel:
            await after.edit(afk_channel=before.afk_channel, reason="@ Luxor antinuke recovery")
          if before.verification_level != after.verification_level:
            await after.edit(verification_level=before.verification_level, reason="@ Luxor antinuke recovery")
          if before.default_message_notifications != after.default_message_notifications:
            await after.edit(default_message_notifications=before.default_message_notifications, reason="@ Luxor antinuke recovery")
          
        except:
          pass

        if punish:
          await self.send_log(channel=data['log_channel'],
                              user=user,
                              action="updated guild",
                              punishment=punish)
async def setup(bot):
  await bot.add_cog(Antinuke(bot))