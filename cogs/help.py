import discord
from discord.ext import commands
from config import config

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class HelpSelect(discord.ui.Select):
        def __init__(self, embed, ctx, bot):
            options = [
                discord.SelectOption(label="Moderation", description="Shows moderation commands"),
                discord.SelectOption(label="Utility", description="Shows utility commands"),
                discord.SelectOption(label="Antinuke", description="Shows antinuke setup commands"),
                discord.SelectOption(label="Antibot", description="Shows antibot setup commands"),
                discord.SelectOption(label="Voicemaster", description="Shows voicemaster setup commands"),
                discord.SelectOption(label="Music", description="Shows music player commands"),
                discord.SelectOption(label="Webhooks", description="Shows webhooks manager commands"),
                discord.SelectOption(label="Verification", description="Shows verification setup commands"),
                discord.SelectOption(label="Logging", description="Shows logging setup commands"),
                discord.SelectOption(label="Greet", description="Shows greet setup commands"),
                discord.SelectOption(label="Giveaway", description="Shows giveaway commands"),
                discord.SelectOption(label="Sticky", description="Shows sticky setup commands"),
                discord.SelectOption(label="Media", description="Shows media setup commands"),
                discord.SelectOption(label="Image", description="Shows image manipulation commands"),
                discord.SelectOption(label="Voice", description="Shows voice commands"),
                discord.SelectOption(label="Ticket", description="Shows ticket setup commands"),
                discord.SelectOption(label="Economy", description="Shows economy commands"),
                discord.SelectOption(label="Forcenick", description="Shows forcenick setup commands"),
                discord.SelectOption(label="Fun", description="Shows fun commands"),
                discord.SelectOption(label="Ping on Join", description="Shows ping on join setup commands"),
                discord.SelectOption(label="Autorole", description="Shows autorole setup commands"),
                discord.SelectOption(label="Join DM", description="Shows join-dm setup commands"),
                discord.SelectOption(label="Goodbye", description="Shows goodbye notifier setup commands"),
                discord.SelectOption(label="Autopost", description="Shows pfp and autopost setup commands"),
                discord.SelectOption(label="Autoresponse", description="Shows autoresponse setup commands"),
                #discord.SelectOption(label="Developers", description="Shows developers only commands")
            ]
            super().__init__(placeholder="choose a menu or function", max_values=1, min_values=1, options=options)
            self.embed = embed
            self.ctx = ctx
            self.bot = bot

        async def callback(self, interaction: discord.Interaction):
            if self.ctx.author.id != interaction.user.id:
                return await interaction.response.send_message("This select menu is not for you!", ephemeral=True)

            bot = self.bot
            embed = self.embed or discord.Embed()
            embed.color = discord.Color.blurple()
            embed.set_author(name=f"{self.ctx.author.name}", url=config.url, icon_url=bot.user.avatar.url)
            embed.set_footer(text=f"use ,help <command_name> for more help", icon_url=bot.user.avatar.url)
            
            if self.values[0] == "Main Menu":
                await interaction.response.send_message("Select a category from the dropdown menu to view available commands.", ephemeral=True)
            elif self.values[0] == "Antinuke":
                embed.description = f">>> `antinuke`, `antinuke setup`, `antinuke enable`, `antinuke disable`, `antinuke threatmode enable`, `antinuke threatmode disable`, `antinuke whitelist add`, `antinuke whitelist remove`, `antinuke whitelist show`, `antinuke settings`, `antinuke logs`, `antinuke punishment`"
            elif self.values[0] == "Autorole":
                embed.description = f">>> `autorole`, `autorole enable`, `autorole disable`, `autorole humans add`, `autorole humans remove`, `autorole humans reset`, `autorole humans show`, `autorole bot add`, `autorole bot remove`, `autorole bot reset`, `autorole bot show`"
            elif self.values[0] == "Ping on Join":
                embed.description = f">>> `pingonjoin`, `pingonjoin enable`, `pingonjoin disable`, `pingonjoin channel add`, `pingonjoin channel remove`, `pingonjoin message`, `pingonjoin delay`"
            elif self.values[0] == "Autopost":
                embed.description = f">>> {config.beta}\n`autopost`, `autopost male enable`, `autopost male disable`, `autopost female enable`, `autopost female disable`, `autopost anime enable`, `autopost anime disable`, `autopost banner enable`, `autopost banner disable`, `pfp male`, `pfp female`, `pfp anime`"
            elif self.values[0] == "Goodbye":
                embed.description = f">>> `goodbye`, `goodbye variable`, `goodbye test`, `goodbye enable`, `goodbye disable`, `goodbye message`, `goodbye config`"
            elif self.values[0] == "Join DM":
                embed.description = f">>> `joindm`, `joindm message`, `joindm variables`, `joindm config`, `joindm reset`, `joindm test`"
            elif self.values[0] == "Autoresponse":
                embed.description = f">>> `autoresponse`, `autoresponse add`, `autoresponse remove`, `autoresponse update`, `autoresponse config`\n`autoreact`, `autoreact add`, `autoreact remove`, `autoreact clear`, `autoreact list`"
            elif self.values[0] == "Economy":
                embed.description = f">>> {config.beta}\n`register`, `balance`, `beg`, `coinflip`, `crime`, `daily`, `work`, `give`, `leaderboard`"
            elif self.values[0] == "Verification":
                embed.description = f">>> `verification setup`, `verification attempt`, `verification role`, `verification reset`, `verification config`"
            elif self.values[0] == "Moderation":
                embed.description = f">>> `lock`, `unlock`, `hide`, `unhide`, `lockall`, `unlockall`, `hideall`, `unhideall`, `sneaky`, `unsneaky`, `tempban`, `temprole`, `guildedit`, `roleall`, `roleall humans`, `roleall bots`, `mute`, `unmute`, `kick`, `ban`, `softban`, `unban`, `unbanall`, `setnick`, `edithex`, `steal`, `addrole`, `removerole`, `purge`, `purge bots`, `purge humans`, `purge embeds`, `purge files`, `warn add`, `warn clear`, `warn list`, `autoban add`, `autoban remove`, `autoban config`, `antialt toggle`, `antialt threshold`, `antialt config`"
            elif self.values[0] == "Utility":
                embed.description = f">>> `profile`, `invite`, `support`, `vote`, `links`, `checkvanity`, `tts`, `afk`, `afkhistory`, `embedcreate`, `snipe`, `esnipe`, `clone`, `roleinfo`, `userinfo`, `serverinfo`, `servericon`, `serverbanner`, `avatar`, `ping`, `uptime`, `github`, `remind`, `remind list`, `remind remove`, `list boosters`, `list bans`, `list roles`, `list joinposition`, `list emojis`, `list bots`, `list admins`, `list mods`, `list early`, `list activedev`, `list botdev`, `inviteinfo`, `namehistory`, `lastseen`, `clearnames`, `claim`, `detailedinfo`, `username`, `username channel`, `username delete`"
            elif self.values[0] == "Fun":
                embed.description = f">>> `wanted`, `rip`, `dare`, `truth`, `nhie`, `wouldyourather`, `paranoia`, `guessthenumber`, `hack`, `bitches`, `iq`, `gayrate`, `slap`, `bite`, `highfive`, `hug`, `kiss`, `shoot`, `smile`, `stare`, `wave`, `tickle`, `wink`, `cmds`, `src`, `simp`, `stupid`, `ship`, `dice`, `choose`, `reverse`, `insult`, `randomhex`, `cat`, `dev`"
            elif self.values[0] == "Ticket":
                embed.description = f">>> `ticket panel`, `ticket category`, `ticket stats`, `ticket staffadd`, `ticket staffremove`"
            elif self.values[0] == "Media":
                embed.description = f">>> `media`, `media channel add`, `media channel remove`, `media channel show`, `media bypass`, `media bypass add`, `media bypass remove`, `media bypass show`\n`medialogger add`, `medialogger remove`"
            elif self.values[0] == "Voice":
                embed.description = f">>> `vcrole`, `vcrole setup`, `vcrole remove`, `vcrole config`\n`antivc`, `antivc add`, `antivc remove`, `antivc config`\n`voice deafen`, `voice undeafen`, `voice mute`, `voice unmute`, `voice kick`, `voice move`, `voice mte`, `voice unmte`"
            elif self.values[0] == "Forcenick":
                embed.description = f">>> `forcenick`, `forcenick add`, `forcenick remove`, `forcenick config`, `forcenick check`"
            elif self.values[0] == "Antibot":
                embed.description = f">>> `antibot`, `antibot channel add`, `antibot channel remove`, `antibot channel show`, `antibot channel reset`, `antibot bypass`, `antibot bypass add`, `antibot bypass remove`, `antibot bypass show`, `antibot bypass reset`"
            elif self.values[0] == "Usernames":
                embed.description = f">>> `username`, `username channel`, `username delete`"
            elif self.values[0] == "Voicemaster":
                embed.description = f">>> `voicemaster`, `voicemaster setup`, `voicemaster delete`"
            elif self.values[0] == "Greet":
                embed.description = f">>> `greet`, `greet setup`, `greet reset`, `greet config`, `greet test`"
            elif self.values[0] == "Sticky":
                embed.description = f">>> `sticky`, `sticky create`, `sticky delete`, `sticky show`, `sticky reset`"
            elif self.values[0] == "Image":
                embed.description = f">>> `image`, `image blur`, `image deepfry`, `image meme`, `image swirl`, `image spread`, `image grayscale`, `image invert`"
            elif self.values[0] == "Giveaway":
                embed.description = f">>> `gw`, `gw start`, `gw end`, `gw list`, `gw reroll`"
            elif self.values[0] == "Webhooks":
                embed.description = f">>> `webhook`, `webhook create`, `webhook delete`, `webhook list`, `webhook edit`, `webhook edit name`, `webhook edit avatar`"
            elif self.values[0] == "Logging":
                embed.description = f">>> `logging`, `logging enable`, `logging config`, `logging remove`, `logging events`"
            elif self.values[0] == "Music":
                embed.description = f">>> `join`, `leave`, `play`, `pause`, `skip`, `nowplaying`, `queue`, `remove`, `empty`"
            elif self.values[0] == "Developers":
                embed.description = f">>> **`guildBlacklist`**\n`guild blacklist`, `guild blacklist add`, `guild blacklist remove`, `guild blacklist view`, `guild blacklist clear`\n**`globalBan`**\n`globalban add`, `globalban remove`, `globalban config`, `globalban sync`\n**`otherCmds`**\n`reload`, `leaveg`, `broadcast`"

            await interaction.response.edit_message(content="", embed=embed)

    class HelpMenuView(discord.ui.View):
        def __init__(self, ctx, bot, *, timeout=900):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.bot = bot
            self.message = None
            self.add_item(HelpMenu.HelpSelect(embed=discord.Embed(), ctx=ctx, bot=bot))

        async def on_timeout(self):
            if self.message:
                await self.message.edit(
                    content="Help menu expired, use the `,help` command again to view commands.", 
                    embed=None, 
                    view=None
                )

    @commands.command(aliases=['h'], help="get help for the bot or a specific command")
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def help(self, ctx, *command_name):
        if not command_name:
            view = HelpMenu.HelpMenuView(ctx=ctx, bot=self.bot)
            message = await ctx.reply("Use the dropdown below to access all the commands and functions of the bot. :DD", view=view)
            view.message = message
            return

        command_name = " ".join(command_name)
        command = self.bot.get_command(command_name)
        if not command:
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention}: Command not found", 
                color=config.hex
            ))
            return

        embe = discord.Embed(color=config.hex, description=f"```\n< > : Required Arguments\n[ ] : Optional Arguments```")
        embe.set_author(name=self.bot.user, icon_url=self.bot.user.avatar.url)
        embe.add_field(name="Command", value=f"{command}", inline=False)
        
        if command.help:
            embe.add_field(name="Help", value=f"{command.help}", inline=False)
        
        aliases = command.aliases
        if aliases:
            embe.add_field(name="Aliases", value=f"`{'`, `'.join(aliases)}`", inline=False)
        
        if isinstance(command, commands.Group):
            subcommands = [subcmd.name for subcmd in command.commands]
            if subcommands:
                embe.add_field(name="Subcommands", value=f"`{'`, `'.join(subcommands)}`", inline=False)
        
        sig = command.signature
        if sig:
            embe.add_field(name="Usage", value=f"`{command.qualified_name} {sig}`", inline=False)

        await ctx.reply(embed=embe)

async def setup(bot):
    await bot.add_cog(HelpMenu(bot))
