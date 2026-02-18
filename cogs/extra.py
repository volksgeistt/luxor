import discord
from discord.ext import commands
from config import config
from discord.ui import Button, View
import os
import datetime
import requests
import json
import io
from gtts import gTTS
import aiohttp

def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed

class Basement(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.bot.launch_time = datetime.datetime.utcnow()
    self.warns_file = "db/Warns.json"


  def load_warns(self):
      try:
          with open(self.warns_file, "r") as f:
              return json.load(f)
      except FileNotFoundError:
          return {}

  def save_warns(self, warns):
      with open(self.warns_file, "w") as f:
          json.dump(warns, f, indent=4)
##########################################################################################
  @commands.command(name="tts",aliases=["texttospeech"],help="converts text to speech")
  async def tts(self, ctx, *, text):
      luxor = io.BytesIO()
      textToSpeech = gTTS(str(text), lang='en')
      textToSpeech.write_to_fp(luxor)
      luxor.seek(0)
      return await ctx.send(file=discord.File(luxor, "TextToSpeech.mp3"))
    
  @commands.command(name="invite",help="sends the invite link of bot.",aliases=["inv"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def invite_(self, ctx):
      invite_button = Button(label=f"Invite Luxor", style=discord.ButtonStyle.link, url=config.url)
      view = View()  
      view.add_item(invite_button)  
      await ctx.reply(embed=create_embed(f"{config.added_emoji} {ctx.author.mention}: [invite Luxor]({config.url}) from the button below!"), view=view)

  @commands.command(name="vote",help="sends the vote link of bot.",aliases=["votee"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def vote_(self, ctx):
      vote_button = Button(label=f"Vote on DBL", style=discord.ButtonStyle.link, url=config.top_gg_vote)
      x = Button(label=f"Vote on Top.gg", style=discord.ButtonStyle.link, url=config.top_gg_vote2)
      view = View()  
      view.add_item(vote_button)
      view.add_item(x)
      await ctx.reply(embed=create_embed(f"{config.added_emoji} {ctx.author.mention}: [DBL]({config.top_gg_vote})/[Top.gg]({config.top_gg_vote2}) vote from the button below!"), view=view)
        
  @commands.command(help="shows the bot's uptime.")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def uptime(self, ctx):
      delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
      hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
      minutes, seconds = divmod(remainder, 60)
      days, hours = divmod(hours, 24)
      await ctx.send(embed=discord.Embed(description=f"{config.tick} {self.bot.user.mention}: `{days}`d, `{hours}`h, `{minutes}`m, `{seconds}`s", color=config.hex))
    
  @commands.command(name="support",help="sends the invite link of support server.",aliases=["suppo"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def support_(self, ctx):
      invite_button = Button(label=f"Join Luxor HQ", style=discord.ButtonStyle.link, url=config.support_server)
      view = View()
      view.add_item(invite_button)
      await ctx.reply(embed=create_embed(f"{config.ques_emoji} {ctx.author.mention}: join my [support server]({config.support_server}) from button below!"), view=view)

  @commands.command(name="github", help="sends the github profile of the user.", aliases=["git"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def github_(self, ctx, username:str):
    try:
      rr = requests.get(f'https://api.github.com/users/{username}')
      if rr.status_code == 200:
          data = rr.json()
          embed = discord.Embed(title=f"{data['login']} ({data['name'] or 'No Name'})",description=f">>> {data['bio'] or 'No bio provided'}",color=config.hex)
          embed.set_thumbnail(url=data['avatar_url'])
          embed.add_field(name='Followers', value=data['followers'], inline=False)
          embed.add_field(name='Following', value=data['following'])
          embed.add_field(name='Public Repositories', value=data['public_repos'])
          embed.add_field(name='Location', value=data['location'] or 'Not specified')
          embed.set_footer(text=f"Requested by {ctx.author}")
          await ctx.send(embed=embed)
      else:
          embed = discord.Embed(color=config.hex, description=f"{config.error_emoji} {ctx.author.mention} : Unable to fetch the profile through provided username")
          await ctx.send(embed=embed)
    except Exception as e:
      print(e)

  @commands.command(name="botinfo",help="sends the information of bot.",aliases=["bi","stats"])
  @commands.cooldown(1, 5, commands.BucketType.user)
  @commands.guild_only()
  async def botinfo_(self, ctx):
      inv = Button(label=f"invite {self.bot.user.name}", style=discord.ButtonStyle.link, url=config.url)
      supp = Button(label=f"join {self.bot.user.name} hq", style=discord.ButtonStyle.link, url=config.support_server)
      view = View()
      view.add_item(inv)
      view.add_item(supp)
      def count_files_and_lines(directories):
          total_lines = 0
          total_files = 0
          for directory in directories:
              total_lines += sum(len(open(os.path.join(dirpath, f)).readlines())
                                for dirpath, _, files in os.walk(directory)
                                for f in files if f.endswith('.py'))
              total_files += sum(1 for dirpath, _, files in os.walk(directory) for f in files if f.endswith('.py'))
          return total_files, total_lines
      directories_to_count = ['cogs', 'config', 'helper']
      total_files, total_lines = count_files_and_lines(directories_to_count)
    
    
      embed=discord.Embed(description=f">>> **Bot version:** 0.2.3",color=config.hex)
      embed.add_field(name=f"Servers",value=f"{len(self.bot.guilds)}",inline=True)
      embed.add_field(name=f"Commands",value=f"{len(set(ctx.bot.walk_commands()))}")
      embed.add_field(name=f"Average Latency",value=f"`{round(self.bot.latency * 1000, 2)}`ms")
      embed.add_field(name="Code Files", value=f"{total_files}", inline=True)
      embed.add_field(name="Code Lines", value=f"{total_lines}", inline=True)

      delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
      hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
      minutes, seconds = divmod(remainder, 60)
      days, hours = divmod(hours, 24)
      embed.add_field(name=f"Uptime", value=f"`{days}`d, `{hours}`h, `{minutes}`m, `{seconds}`s")
      embed.set_author(name=self.bot.user.name,icon_url=self.bot.user.avatar, url=config.url)
      embed.set_footer(text=f"Thanks For Choosing {self.bot.user.name}",icon_url=self.bot.user.avatar)
      embed.set_thumbnail(url=self.bot.user.avatar)
      await ctx.send(embed=embed,view=view)

  @commands.command(name="links",help="sends the all link of bot.",aliases=["link"])
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def links(self, ctx):
      ok = Button(label=f"vote", style=discord.ButtonStyle.link, url=config.top_gg_vote)
      x = Button(label=f"vote2", style=discord.ButtonStyle.link, url=config.top_gg_vote2)
      one = Button(label=f"invite", style=discord.ButtonStyle.link, url=config.url)
      two = Button(label=f"join support", style=discord.ButtonStyle.link, url=config.support_server)
      three = Button(label=f"tos", style=discord.ButtonStyle.link, url=config.tos)
      four = Button(label=f"privacy policy", style=discord.ButtonStyle.link, url=config.privacy_policy)
      view = View()  
      view.add_item(ok)
      view.add_item(x)
      view.add_item(one)
      view.add_item(two)  
      view.add_item(three)  
      view.add_item(four)  
      await ctx.reply(f"below are the links of **{self.bot.user.name}** bot.",view=view)

        
  @commands.command(name="inviteinfo", aliases=["if"], help="Show info about a particular invite code.")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def invite_info(self, ctx, invite_code: str):
      try:
          invite = await self.bot.fetch_invite(invite_code)
          embed = discord.Embed(description=f">>> **Inviter:** {invite.inviter.name}\n**Server:** {invite.guild.name}\n**Channel:** #{invite.channel.name}\n**Uses:** {invite.uses}\n**Max Uses:** {invite.max_uses}\n**Max Age:** {invite.max_age}\n**Temporary?:** {"Yes" if invite.temporary else "No"}",color=config.hex)
          embed.set_author(name=f"Invite Info",icon_url=self.bot.user.avatar)
          embed.set_footer(text=f"Invite Code: {invite_code}",icon_url=self.bot.user.avatar)
          await ctx.send(embed=embed)
      except discord.NotFound:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: the invite code is invalid.",color=config.hex))
      except discord.HTTPException:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: error occured while fetching the code.",color=config.hex))
        
        
  @commands.group(name="warn", invoke_without_command=True, help="Warn related commands.")
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.guild_only()
  async def warn_group(self, ctx):
      await ctx.send("")

  @warn_group.command(name="add", help="adds warn note to a user.")
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def warn_add(self, ctx, member: discord.Member, *, reason="No reason provided."):
      try:
          warns = self.load_warns()
          warns[str(member.id)] = warns.get(str(member.id), []) + [reason]
          self.save_warns(warns)
          await member.send(f"you have been warned in **{ctx.guild.name}** with reason **{reason}**")
          await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: warned {member.mention} for **{reason}**",color=config.hex))
      except Exception as e:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an unexpected error occured: ({e})",color=config.hex))

  @warn_group.command(name="remove",aliases=["clear", "delete", "del"], help="Remove a warn from a user.")
  @commands.guild_only()
  @commands.has_permissions(manage_guild=True)
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def warn_remove(self, ctx, member: discord.Member, index: int):
      try:
          warns = self.load_warns()
          user_warns = warns.get(str(member.id), [])
          if 0 < index <= len(user_warns):
              removed_warn = user_warns.pop(index - 1)
              warns[str(member.id)] = user_warns
              self.save_warns(warns)
              await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed warn ({index})[{removed_warn}] from {member.mention}",color=config.hex))
          else:
              await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: invalid index, please provide valid warn info to remove",color=config.hex))
      except Exception as e:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an unexpected error occured: ({e})",color=config.hex))

  @warn_group.command(name="list", aliases=["config"], help="List warns of a user.")
  @commands.guild_only()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(manage_guild=True)
  async def warn_list(self, ctx, member: discord.Member):
      try:
          warns = self.load_warns()
          user_warns = warns.get(str(member.id), [])
          if user_warns:
              embed = discord.Embed(color=config.hex)
              embed.set_author(name=f"{member.display_name}'s Warns",icon_url=self.bot.user.avatar)
              for i, warn in enumerate(user_warns, 1):
                  embed.add_field(name=f"warn case: {i}", value=warn, inline=False)
              await ctx.send(embed=embed)
          else:
              await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: that user has no warns on their profile",color=config.hex))
      except Exception as e:
          await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an unexpected error occured: ({e})",color=config.hex))
            
  @commands.command(name="guild-edit", help="Edit guild settings with an interactive menu.", aliases=["gedit","guildedit"])
  @commands.has_permissions(administrator=True)
  @commands.cooldown(1, 10, commands.BucketType.user)
  @commands.guild_only()
  async def guild_edit(self, ctx):
      name_button = Button(label="Edit Name", style=discord.ButtonStyle.primary, emoji="📝")
      description_button = Button(label="Edit Description", style=discord.ButtonStyle.primary, emoji="📄")
      banner_button = Button(label="Edit Banner", style=discord.ButtonStyle.primary, emoji="🖼️")
      icon_button = Button(label="Edit Icon", style=discord.ButtonStyle.primary, emoji="🎨")
      afk_settings_button = Button(label="AFK Settings", style=discord.ButtonStyle.primary, emoji="⏰")
      notification_button = Button(label="Notification Settings", style=discord.ButtonStyle.primary, emoji="🔔")
      verification_button = Button(label="Verification Level", style=discord.ButtonStyle.primary, emoji="📚")
      system_channel_button = Button(label="System Channel", style=discord.ButtonStyle.primary, emoji="📢")
      community_rules_button = Button(label="Community Channels", style=discord.ButtonStyle.primary, emoji="💬")

      view = GuildEditView(ctx.author)
      view.add_item(name_button)
      view.add_item(description_button)
      view.add_item(banner_button)
      view.add_item(icon_button)
      view.add_item(afk_settings_button)
      view.add_item(notification_button)
      view.add_item(verification_button)
      view.add_item(system_channel_button)
      view.add_item(community_rules_button)

      name_button.callback = view.name_callback
      description_button.callback = view.description_callback
      banner_button.callback = view.banner_callback
      icon_button.callback = view.icon_callback
      afk_settings_button.callback = view.afk_settings_callback
      notification_button.callback = view.notification_callback
      verification_button.callback = view.verification_callback
      system_channel_button.callback = view.system_channel_callback
      community_rules_button.callback = view.community_channels_callback

      embed = discord.Embed(
            description="> **Select what guild settings would you like to modify?**",
            color=config.hex
        )
      embed.set_footer(text="These changes can only be configured by Guild Administrators", icon_url=self.bot.user.avatar)
      embed.set_author(name="Guild Setting Editor", icon_url=self.bot.user.avatar)
      await ctx.send(embed=embed, view=view)

class GuildEditView(View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} You're not allowed to interact with these buttons.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
            return False
        return True

    async def name_callback(self, interaction):
        name_modal = NameModal()
        await interaction.response.send_modal(name_modal)

    async def description_callback(self, interaction):
        description_modal = DescriptionModal()
        await interaction.response.send_modal(description_modal)

    async def banner_callback(self, interaction):
        banner_modal = BannerModal()
        await interaction.response.send_modal(banner_modal)

    async def icon_callback(self, interaction):
        icon_modal = IconModal()
        await interaction.response.send_modal(icon_modal)

    async def afk_settings_callback(self, interaction):
        await interaction.response.send_modal(AFKSettingsModal())

    async def notification_callback(self, interaction):
        await interaction.response.send_modal(NotificationSettingsModal())

    async def verification_callback(self, interaction):
        await interaction.response.send_modal(VerificationLevelModal())

    async def system_channel_callback(self, interaction):
        await interaction.response.send_modal(SystemChannelModal())

    async def community_channels_callback(self, interaction):
        await interaction.response.send_modal(CommunityRulesModal())


class NameModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Change Guild Name")
        self.name = discord.ui.TextInput(
            label="New Guild Name",
            style=discord.TextStyle.short,
            placeholder="Enter new guild name",
            max_length=100,
            required=True
        )
        self.add_item(self.name)

    async def on_submit(self, interaction):
        try:
            await interaction.guild.edit(name=str(self.name))
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.tick} Guild name updated to: **{self.name}**", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} I don't have permission to change the guild name.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

class DescriptionModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Change Guild Description")
        self.description = discord.ui.TextInput(
            label="New Guild Description",
            style=discord.TextStyle.paragraph,
            placeholder="Enter new guild description",
            max_length=1000,
            required=True
        )
        self.add_item(self.description)

    async def on_submit(self, interaction):
        try:
            await interaction.guild.edit(description=str(self.description))
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.tick} Guild description updated successfully!", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} I don't have permission to change the guild description.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

class BannerModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Change Guild Banner")
        self.banner_url = discord.ui.TextInput(
            label="Banner Image URL",
            style=discord.TextStyle.short,
            placeholder="Paste a direct image URL",
            required=True
        )
        self.add_item(self.banner_url)

    async def on_submit(self, interaction):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(self.banner_url)) as resp:
                    if resp.status == 200:
                        banner_bytes = await resp.read()
                        await interaction.guild.edit(banner=banner_bytes)
                        await interaction.response.send_message(
                            embed=discord.Embed(
                                description=f"{config.tick} Guild banner updated successfully!", 
                                color=config.hex
                            ), 
                            ephemeral=True
                        )
                    else:
                        await interaction.response.send_message(
                            embed=discord.Embed(
                                description=f"{config.error_emoji} Could not download the banner image.", 
                                color=config.hex
                            ), 
                            ephemeral=True
                        )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} I don't have permission to change the guild banner.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

class IconModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Change Guild Icon")
        self.icon_url = discord.ui.TextInput(
            label="Icon Image URL",
            style=discord.TextStyle.short,
            placeholder="Paste a direct image URL",
            required=True
        )
        self.add_item(self.icon_url)

    async def on_submit(self, interaction):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(self.icon_url)) as resp:
                    if resp.status == 200:
                        icon_bytes = await resp.read()
                        await interaction.guild.edit(icon=icon_bytes)
                        await interaction.response.send_message(
                            embed=discord.Embed(
                                description=f"{config.tick} Guild icon updated successfully!", 
                                color=config.hex
                            ), 
                            ephemeral=True
                        )
                    else:
                        await interaction.response.send_message(
                            embed=discord.Embed(
                                description=f"{config.error_emoji} Could not download the icon image.", 
                                color=config.hex
                            ), 
                            ephemeral=True
                        )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} I don't have permission to change the guild icon.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

class AFKSettingsModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="AFK Channel Configuration")
        self.afk_channel = discord.ui.TextInput(
            label="AFK Channel ID",
            style=discord.TextStyle.short,
            placeholder="Enter channel ID for AFK users",
            required=False
        )
        self.afk_timeout = discord.ui.TextInput(
            label="AFK Timeout (seconds)",
            style=discord.TextStyle.short,
            placeholder="Time before moving to AFK channel (60-3600)",
            required=False
        )
        self.add_item(self.afk_channel)
        self.add_item(self.afk_timeout)

    async def on_submit(self, interaction):
        try:
            afk_channel = None
            if str(self.afk_channel).strip():
                afk_channel = interaction.guild.get_channel(int(str(self.afk_channel)))
                if not afk_channel:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"{config.error_emoji} Invalid AFK channel ID.", 
                            color=config.hex
                        ), 
                        ephemeral=True
                    )
                    return

            afk_timeout = None
            if str(self.afk_timeout).strip():
                try:
                    afk_timeout = int(str(self.afk_timeout))
                    if afk_timeout < 60 or afk_timeout > 3600:
                        raise ValueError("AFK timeout must be between 60 and 3600 seconds")
                except ValueError:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"{config.error_emoji} Invalid AFK timeout.", 
                            color=config.hex
                        ), 
                        ephemeral=True
                    )
                    return

            await interaction.guild.edit(
                afk_channel=afk_channel, 
                afk_timeout=afk_timeout
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.tick} AFK settings updated successfully!", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

class NotificationSettingsModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Notification Settings")
        self.default_notifications = discord.ui.TextInput(
            label="Default Notifications (all/mentions)",
            style=discord.TextStyle.short,
            placeholder="Enter 'all' or 'mentions'",
            required=False
        )
        self.add_item(self.default_notifications)

    async def on_submit(self, interaction):
        try:
            default_notifications = None
            if str(self.default_notifications).strip().lower() in ['all', 'mentions']:
                default_notifications = discord.NotificationLevel.all_messages if str(self.default_notifications).strip().lower() == 'all' else discord.NotificationLevel.only_mentions

            await interaction.guild.edit(
                default_notifications=default_notifications
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.tick} Notification settings updated successfully!", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

class VerificationLevelModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Change Verification Level")
        self.verification_level = discord.ui.TextInput(
            label="Verification Level (0-2)",
            style=discord.TextStyle.short,
            placeholder="0: None, 1: Low, 2: Medium",
            max_length=1,
            required=True
        )
        self.add_item(self.verification_level)

    async def on_submit(self, interaction):
        try:
            level = int(str(self.verification_level))
            if level not in [0, 1, 2]:
                raise ValueError("Verification level must be 0, 1, or 2")
            
            verification_levels = [
                discord.VerificationLevel.none,
                discord.VerificationLevel.low,
                discord.VerificationLevel.medium
            ]
            
            await interaction.guild.edit(verification_level=verification_levels[level])
            
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.tick} Verification level updated to: **{verification_levels[level].name}**", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} Invalid verification level. Must be 0, 1, or 2.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} I don't have permission to change the verification level.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

class SystemChannelModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="System Channel Configuration")
        self.system_channel = discord.ui.TextInput(
            label="System Channel ID",
            style=discord.TextStyle.short,
            placeholder="Enter channel ID for system messages",
            required=False
        )
        self.system_messages = discord.ui.TextInput(
            label="System Message Settings (on/off)",
            style=discord.TextStyle.short,
            placeholder="Enter 'on' or 'off'",
            required=False
        )
        self.add_item(self.system_channel)
        self.add_item(self.system_messages)

    async def on_submit(self, interaction):
        try:
            # Process system channel
            system_channel = None
            if str(self.system_channel).strip():
                system_channel = interaction.guild.get_channel(int(str(self.system_channel)))
                if not system_channel:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"{config.error_emoji} Invalid system channel ID.", 
                            color=config.hex
                        ), 
                        ephemeral=True
                    )
                    return

            system_messages_flags = discord.SystemChannelFlags()
            if str(self.system_messages).strip().lower() == 'on':
                # Enable welcome messages and boost messages
                system_messages_flags.join_notifications = True
                system_messages_flags.premium_subscriptions = True
            elif str(self.system_messages).strip().lower() == 'off':
                # Disable welcome messages and boost messages
                system_messages_flags.join_notifications = False
                system_messages_flags.premium_subscriptions = False

            await interaction.guild.edit(
                system_channel=system_channel, 
                system_channel_flags=system_messages_flags
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.tick} System channel settings updated successfully!", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} I don't have permission to change system channel settings.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )
            
class CommunityRulesModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Community & Rules Channel Setup")
        self.rules_channel = discord.ui.TextInput(
            label="Rules Channel ID",
            style=discord.TextStyle.short,
            placeholder="Enter channel ID for server rules",
            required=False
        )
        self.guidelines_channel = discord.ui.TextInput(
            label="Guidelines Channel ID",
            style=discord.TextStyle.short,
            placeholder="Enter channel ID for community guidelines",
            required=False
        )
        self.community_updates = discord.ui.TextInput(
            label="Community Updates Channel ID",
            style=discord.TextStyle.short,
            placeholder="Enter channel ID for community announcements",
            required=False
        )
        self.community_settings = discord.ui.TextInput(
            label="Community Settings (on/off)",
            style=discord.TextStyle.short,
            placeholder="'on' or 'off'",
            required=False
        )
        self.add_item(self.rules_channel)
        self.add_item(self.guidelines_channel)
        self.add_item(self.community_updates)
        self.add_item(self.community_settings)

    async def on_submit(self, interaction):
        try:
            rules_channel = None
            if str(self.rules_channel).strip():
                rules_channel = interaction.guild.get_channel(int(str(self.rules_channel)))
                if not rules_channel:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"{config.error_emoji} Invalid rules channel ID.", 
                            color=config.hex
                        ), 
                        ephemeral=True
                    )
                    return

            guidelines_channel = None
            if str(self.guidelines_channel).strip():
                guidelines_channel = interaction.guild.get_channel(int(str(self.guidelines_channel)))
                if not guidelines_channel:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"{config.error_emoji} Invalid guidelines channel ID.", 
                            color=config.hex
                        ), 
                        ephemeral=True
                    )
                    return

            community_updates_channel = None
            if str(self.community_updates).strip():
                community_updates_channel = interaction.guild.get_channel(int(str(self.community_updates)))
                if not community_updates_channel:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            description=f"{config.error_emoji} Invalid community updates channel ID.", 
                            color=config.hex
                        ), 
                        ephemeral=True
                    )
                    return

            community_features = False
            if str(self.community_settings).strip().lower() == 'on':
                community_features = True
            elif str(self.community_settings).strip().lower() == 'off':
                community_features = False

            # Attempt to update guild settings
            await interaction.guild.edit(
                rules_channel=rules_channel,
                public_updates_channel=community_updates_channel,
                community=community_features
            )

            embed = discord.Embed(
                title="🏘️ Community Configuration Updated",
                description="Community and rules channels have been configured.",
                color=config.hex
            )
            
            if rules_channel:
                embed.add_field(name="Rules Channel", value=rules_channel.mention, inline=False)
            if community_updates_channel:
                embed.add_field(name="Community Updates Channel", value=community_updates_channel.mention, inline=False)
            embed.add_field(name="Community Features", value="Enabled" if community_features else "Disabled", inline=False)

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} I don't have permission to change community settings.", 
                    color=config.hex
                ), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{config.error_emoji} An error occurred: {str(e)}", 
                    color=config.hex
                ), 
                ephemeral=True
            )

async def setup(bot):
  await bot.add_cog(Basement(bot))