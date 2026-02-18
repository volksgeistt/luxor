import discord
from discord.ext import commands
import json
from typing import Optional
from datetime import datetime, timedelta
from config import config

class EventPaginator(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot
        self.current_page = 1
        self.max_pages = 5
        
        self.pages = {
            1: ("Member Events", "• Member Join\n• Member Leave\n• Member Ban\n• Member Unban\n\nLogs details like user IDs, timestamps, and avatars"),
            2: ("Channel Events", "• Channel Create\n• Channel Delete\n• Channel Update\n\nTracks changes in name, category, and position"),
            3: ("Role Events", "• Role Create\n• Role Delete\n• Role Update\n\nMonitors changes in permissions, color, and settings"),
            4: ("Message Events", "• Message Delete\n• Message Edit\n\nCaptures message content and author information"),
            5: ("Voice Events", "• Voice Channel Join\n• Voice Channel Leave\n• Voice Channel Move\n\nTracks member voice state changes")
        }

    @discord.ui.button(label="◀", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 1:
            self.current_page -= 1
        else:
            self.current_page = self.max_pages
        await self.update_page(interaction)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_pages:
            self.current_page += 1
        else:
            self.current_page = 1
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        title, content = self.pages[self.current_page]
        embed = discord.Embed(
            title=f"Logging Events - {title}",
            description=content,
            color=config.hex
        )
        embed.set_footer(text=f"Page {self.current_page}/{self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=self)

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reply = "> "
        self.color = config.hex

    async def load_logs(self):
        try:
            with open('logsch.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def save_logs(self, logs):
        with open('logsch.json', 'w') as f:
            json.dump(logs, f, indent=4)

    def get_timestamp(self):
        return f"Today at {datetime.now().strftime('%I:%M %p')}"

    def create_embed(self, title, description, color=None):
        embed = discord.Embed(
            color=color or self.color,
            description=description
        )
        embed.set_author(name=title, icon_url=self.bot.user.avatar)
        embed.set_footer(text=self.get_timestamp(),icon_url=self.bot.user.avatar)
        return embed

    @commands.group(name="log", aliases=["logging"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def log(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Logging",description=f">>> `logging`, `logging enable`, `logging config`, `logging remove`\n{config.ques_emoji} Example: `logging enable <#channel>`",color=config.hex))


    @log.command(name="set", aliases=["enable"],help="setup logging channel in the guild.")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def set_log(self, ctx, channel: discord.TextChannel):
        logs = await self.load_logs()
        logs[str(ctx.guild.id)] = str(channel.id)
        
        await channel.send(embed=discord.Embed(description=f"> This channel has been set as the logs channel.",color=config.hex))
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: logging channel set to {channel.mention}",color=config.hex))
        await self.save_logs(logs)

    @log.command(name="show", aliases=["config"],help="show logging setup channel in the guild.")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def show_log(self, ctx):
        logs = await self.load_logs()
        try:
            channel_id = logs[str(ctx.guild.id)]
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: current logging channel is set to <#{channel_id}>",color=config.hex))
        except KeyError:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: currently, there is no logging channel set.",color=config.hex))

    @log.command(name="remove",aliases=["delete"],help="clear logging channel data for the guild.")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def remove_log(self, ctx):
        logs = await self.load_logs()
        if str(ctx.guild.id) in logs:
            del logs[str(ctx.guild.id)]
            await ctx.send("Logs channel removed")
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: disabled logging for this guild.",color=config.hex))
            await self.save_logs(logs)
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: currently, there is no logging channel set.",color=config.hex))

    @log.command(name="events", help="Show all events logged by the bot")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def events(self, ctx):
        view = EventPaginator(self.bot)
        title, content = view.pages[1]
        embed = discord.Embed(
            title=f"Logging Events - {title}",
            description=content,
            color=self.color
        )
        embed.set_footer(text=f"Page 1/{view.max_pages}")
        await ctx.send(embed=embed, view=view)


# ------------------- logging_events ------------------- #
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        logs = await self.load_logs()
        if str(before.guild.id) not in logs:
            return
        if before.nick != after.nick:
            desc = f"{self.reply} {after} | {after.id}\n{self.reply} Old Nickname: {before.nick}\n{self.reply} New Nickname: {after.nick}"
            embed = self.create_embed("Nickname Changed", desc, config.hex)
            embed.set_thumbnail(url=after.display_avatar.url)

            channel = self.bot.get_channel(int(logs[str(before.guild.id)]))
            if channel:
                await channel.send(embed=embed)

        if before.roles != after.roles:
            added = set(after.roles) - set(before.roles)
            removed = set(before.roles) - set(after.roles)
            
            desc = f"{self.reply} {after} | {after.id}\n"
            if added:
                desc += f"{self.reply} Added Roles: {', '.join(role.mention for role in added)}\n"
            if removed:
                desc += f"{self.reply} Removed Roles: {', '.join(role.mention for role in removed)}"
            
            embed = self.create_embed("Roles Updated", desc, config.hex)
            embed.set_thumbnail(url=after.display_avatar.url)

            channel = self.bot.get_channel(int(logs[str(before.guild.id)]))
            if channel:
                await channel.send(embed=embed)

        if before.avatar != after.avatar:
            desc = f"{self.reply} {after} | {after.id}\n{self.reply} Old Avatar: [Link]({before.display_avatar.url})\n{self.reply} New Avatar: [Link]({after.display_avatar.url})"
            embed = self.create_embed("Avatar Changed", desc, config.hex)
            embed.set_thumbnail(url=after.display_avatar.url)

            channel = self.bot.get_channel(int(logs[str(before.guild.id)]))
            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        logs = await self.load_logs()
        if str(before.id) not in logs:
            return

        changes = []
        if before.name != after.name:
            changes.append(f"{self.reply} Server Name: {before.name} → {after.name}")
        if before.icon != after.icon:
            changes.append(f"{self.reply} Server Icon: Changed")
        if before.banner != after.banner:
            changes.append(f"{self.reply} Server Banner: Changed")
        if before.premium_tier != after.premium_tier:
            changes.append(f"{self.reply} Server Boost Level: {before.premium_tier} → {after.premium_tier}")
        if before.premium_subscription_count != after.premium_subscription_count:
            changes.append(f"{self.reply} Server Boosts: {before.premium_subscription_count} → {after.premium_subscription_count}")
        if before.system_channel != after.system_channel:
            changes.append(f"{self.reply} System Channel: {before.system_channel.mention if before.system_channel else 'None'} → {after.system_channel.mention if after.system_channel else 'None'}")
        if before.afk_channel != after.afk_channel:
            changes.append(f"{self.reply} AFK Channel: {before.afk_channel.mention if before.afk_channel else 'None'} → {after.afk_channel.mention if after.afk_channel else 'None'}")
        if before.verification_level != after.verification_level:
            changes.append(f"{self.reply} Verification Level: {before.verification_level} → {after.verification_level}")
        if before.default_notifications != after.default_notifications:
            changes.append(f"{self.reply} Default Notifications: {before.default_notifications} → {after.default_notifications}")
        if before.description != after.description:
            changes.append(f"{self.reply} Description: {before.description or 'None'} → {after.description or 'None'}")
        if before.vanity_url_code != after.vanity_url_code:
            changes.append(f"{self.reply} Vanity URL: {before.vanity_url_code or 'None'} → {after.vanity_url_code or 'None'}")
        if before.preferred_locale != after.preferred_locale:
            changes.append(f"{self.reply} Preferred Locale: {before.preferred_locale} → {after.preferred_locale}")
        if before.rules_channel != after.rules_channel:
            changes.append(f"{self.reply} Rules Channel: {before.rules_channel.mention if before.rules_channel else 'None'} → {after.rules_channel.mention if after.rules_channel else 'None'}")

        if changes:
            desc = "\n".join(changes)
            embed = self.create_embed("Server Updated", desc, config.hex)
            if after.icon:
                embed.set_thumbnail(url=after.icon.url)

            channel = self.bot.get_channel(int(logs[str(before.id)]))
            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        logs = await self.load_logs()
        if str(invite.guild.id) not in logs:
            return

        desc = (f"{self.reply} Created By: {invite.inviter} | {invite.inviter.id}\n"
               f"{self.reply} Channel: {invite.channel.mention}\n"
               f"{self.reply} Invite Code: {invite.code}\n"
               f"{self.reply} Max Uses: {invite.max_uses or 'Unlimited'}\n"
               f"{self.reply} Expires: {invite.max_age and f'<t:{int((datetime.utcnow() + timedelta(seconds=invite.max_age)).timestamp())}:R>' or 'Never'}")
        
        embed = self.create_embed("Invite Created", desc, config.hex)
        embed.set_thumbnail(url=invite.inviter.display_avatar.url)

        channel = self.bot.get_channel(int(logs[str(invite.guild.id)]))
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        logs = await self.load_logs()
        if str(invite.guild.id) not in logs:
            return

        desc = f"{self.reply} Invite Code: {invite.code}\n{self.reply} Channel: {invite.channel.mention if invite.channel else 'Unknown'}"
        embed = self.create_embed("Invite Deleted", desc, config.hex)
        if invite.inviter:
            embed.set_thumbnail(url=invite.inviter.display_avatar.url)

        channel = self.bot.get_channel(int(logs[str(invite.guild.id)]))
        if channel:
            await channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        logs = await self.load_logs()
        if str(member.guild.id) not in logs:
            return
        desc = f"{self.reply} {member} | {member.id}\n{self.reply} Created: <t:{int(member.created_at.timestamp())}:D>\n{self.reply} Avatar: [Link]({member.display_avatar.url})"
        embed = self.create_embed("Member Joined", desc, config.hex)
        embed.set_thumbnail(url=member.display_avatar.url)

        channel = self.bot.get_channel(int(logs[str(member.guild.id)]))
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        logs = await self.load_logs()
        if str(member.guild.id) not in logs:
            return

        desc = f"{self.reply} {member} | {member.id}\n{self.reply} Joined: <t:{int(member.joined_at.timestamp())}:D>"
        embed = self.create_embed("Member Left", desc, config.hex)
        embed.set_thumbnail(url=member.display_avatar.url)

        channel = self.bot.get_channel(int(logs[str(member.guild.id)]))
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        logs = await self.load_logs()
        if str(channel.guild.id) not in logs:
            return

        desc = f"{self.reply} Name: #{channel.name}\n{self.reply} ID: {channel.id}\n{self.reply} Type: {channel.type}\n{self.reply} Category: {channel.category.name if channel.category else 'None'}"
        embed = self.create_embed("Channel Created", desc, config.hex)

        log_channel = self.bot.get_channel(int(logs[str(channel.guild.id)]))
        if log_channel:
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        logs = await self.load_logs()
        if str(channel.guild.id) not in logs:
            return

        desc = f"{self.reply} Name: #{channel.name}\n{self.reply} ID: {channel.id}\n{self.reply} Type: {channel.type}\n{self.reply} Category: {channel.category.name if channel.category else 'None'}"
        embed = self.create_embed("Channel Deleted", desc, config.hex)

        log_channel = self.bot.get_channel(int(logs[str(channel.guild.id)]))
        if log_channel:
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        logs = await self.load_logs()
        if str(before.guild.id) not in logs:
            return
        changes = []
        if before.name != after.name:
            changes.extend([
                f"{self.reply} Before Name: {before.name}",
                f"{self.reply} After Name: {after.name}"
            ])

        if before.category != after.category:
            changes.extend([
                f"{self.reply} Before Category: {before.category.name if before.category else 'None'}",
                f"{self.reply} After Category: {after.category.name if after.category else 'None'}"
            ])

        if before.position != after.position:
            changes.extend([
                f"{self.reply} Before Position: {before.position}",
                f"{self.reply} After Position: {after.position}"
            ])

        if isinstance(before, discord.TextChannel):
            if before.topic != after.topic:
                changes.extend([
                    f"{self.reply} Before Topic: {before.topic or 'None'}",
                    f"{self.reply} After Topic: {after.topic or 'None'}"
                ])
            
            if before.is_nsfw() != after.is_nsfw():
                changes.extend([
                    f"{self.reply} Before NSFW: {before.is_nsfw()}",
                    f"{self.reply} After NSFW: {after.is_nsfw()}"
                ])
            
            if before.slowmode_delay != after.slowmode_delay:
                changes.extend([
                    f"{self.reply} Before Slowmode: {before.slowmode_delay}s",
                    f"{self.reply} After Slowmode: {after.slowmode_delay}s"
                ])

            if before.is_news() != after.is_news():
                changes.extend([
                    f"{self.reply} Before News Channel: {before.is_news()}",
                    f"{self.reply} After News Channel: {after.is_news()}"
                ])

        elif isinstance(before, discord.VoiceChannel):
            if before.bitrate != after.bitrate:
                changes.extend([
                    f"{self.reply} Before Bitrate: {before.bitrate//1000}kbps",
                    f"{self.reply} After Bitrate: {after.bitrate//1000}kbps"
                ])
            
            if before.user_limit != after.user_limit:
                changes.extend([
                    f"{self.reply} Before User Limit: {before.user_limit or 'Unlimited'}",
                    f"{self.reply} After User Limit: {after.user_limit or 'Unlimited'}"
                ])

            if before.rtc_region != after.rtc_region:
                changes.extend([
                    f"{self.reply} Before Region: {before.rtc_region or 'Automatic'}",
                    f"{self.reply} After Region: {after.rtc_region or 'Automatic'}"
                ])

        # Forum channel specific changes
        elif isinstance(before, discord.ForumChannel):
            if before.topic != after.topic:
                changes.extend([
                    f"{self.reply} Before Topic: {before.topic or 'None'}",
                    f"{self.reply} After Topic: {after.topic or 'None'}"
                ])
            
            if before.slowmode_delay != after.slowmode_delay:
                changes.extend([
                    f"{self.reply} Before Slowmode: {before.slowmode_delay}s",
                    f"{self.reply} After Slowmode: {after.slowmode_delay}s"
                ])

            if before.default_auto_archive_duration != after.default_auto_archive_duration:
                changes.extend([
                    f"{self.reply} Before Auto Archive: {before.default_auto_archive_duration} minutes",
                    f"{self.reply} After Auto Archive: {after.default_auto_archive_duration} minutes"
                ])

        before_overwrites = dict(before.overwrites)
        after_overwrites = dict(after.overwrites)
        
        for target in set(before_overwrites.keys()) | set(after_overwrites.keys()):
            before_perms = before_overwrites.get(target)
            after_perms = after_overwrites.get(target)
            
            if before_perms != after_perms:
                target_name = target.name if hasattr(target, 'name') else str(target)
                changes.extend([
                    f"{self.reply} Permission Changes for {target_name}:",
                    f"{self.reply} Before: {before_perms}",
                    f"{self.reply} After: {after_perms}"
                ])
        if changes:
            desc = f"{self.reply} Channel: {after.mention}\n" + "\n".join(changes)
            embed = self.create_embed("Channel Updated", desc)
            log_channel = self.bot.get_channel(int(logs[str(before.guild.id)]))
            if log_channel:
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        logs = await self.load_logs()
        if str(role.guild.id) not in logs:
            return

        desc = (f"{self.reply} Name: {role.name}\n"
               f"{self.reply} ID: {role.id}\n"
               f"{self.reply} Color: {role.color}\n"
               f"{self.reply} Position: {role.position}\n"
               f"{self.reply} Mentionable: {role.mentionable}\n"
               f"{self.reply} Hoisted: {role.hoist}")
        embed = self.create_embed("Role Created", desc, config.hex)

        channel = self.bot.get_channel(int(logs[str(role.guild.id)]))
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        logs = await self.load_logs()
        if str(role.guild.id) not in logs:
            return

        desc = (f"{self.reply} Name: {role.name}\n"
               f"{self.reply} ID: {role.id}\n"
               f"{self.reply} Color: {role.color}\n"
               f"{self.reply} Position: {role.position}")
        embed = self.create_embed("Role Deleted", desc, config.hex)

        channel = self.bot.get_channel(int(logs[str(role.guild.id)]))
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        logs = await self.load_logs()
        if str(before.guild.id) not in logs:
            return
        changes = []
        if before.name != after.name:
            changes.extend([
                f"{self.reply} Before Name: {before.name}",
                f"{self.reply} After Name: {after.name}"
            ])

        if before.color != after.color:
            changes.extend([
                f"{self.reply} Before Color: {before.color}",
                f"{self.reply} After Color: {after.color}"
            ])

        if before.hoist != after.hoist:
            changes.extend([
                f"{self.reply} Before Hoisted: {before.hoist}",
                f"{self.reply} After Hoisted: {after.hoist}"
            ])

        if before.mentionable != after.mentionable:
            changes.extend([
                f"{self.reply} Before Mentionable: {before.mentionable}",
                f"{self.reply} After Mentionable: {after.mentionable}"
            ])

        if before.position != after.position:
            changes.extend([
                f"{self.reply} Before Position: {before.position}",
                f"{self.reply} After Position: {after.position}"
            ])

        if before.permissions != after.permissions:
            before_perms = dict(before.permissions)
            after_perms = dict(after.permissions)
            
            added_perms = []
            removed_perms = []
            changed_perms = []

            for perm, value in after_perms.items():
                if perm in before_perms:
                    if before_perms[perm] != value:
                        changed_perms.append(f"{perm}: {before_perms[perm]} → {value}")
                else:
                    added_perms.append(perm)

            for perm in before_perms:
                if perm not in after_perms:
                    removed_perms.append(perm)

            if added_perms:
                changes.append(f"{self.reply} Added Permissions: {', '.join(added_perms)}")
            if removed_perms:
                changes.append(f"{self.reply} Removed Permissions: {', '.join(removed_perms)}")
            if changed_perms:
                changes.append(f"{self.reply} Changed Permissions: {', '.join(changed_perms)}")
        if hasattr(before, 'icon') and before.icon != after.icon:
            changes.extend([
                f"{self.reply} Role Icon Updated: {before.icon} → {after.icon}"
            ])
        if hasattr(before, 'unicode_emoji') and before.unicode_emoji != after.unicode_emoji:
            changes.extend([
                f"{self.reply} Unicode Emoji: {before.unicode_emoji or 'None'} → {after.unicode_emoji or 'None'}"
            ])
        if changes:
            desc = f"{self.reply} Role: {after.mention}\n" + "\n".join(changes)
            embed = self.create_embed("Role Updated", desc)
            if before.color != after.color:
                embed.color = after.color
            channel = self.bot.get_channel(int(logs[str(before.guild.id)]))
            if channel:
                await channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
            
        logs = await self.load_logs()
        if str(message.guild.id) not in logs:
            return

        desc = (f"{self.reply} Author: {message.author.mention}\n"
               f"{self.reply} Channel: {message.channel.mention}\n"
               f"{self.reply} Content:\n```{message.content or 'No content'}```")
        embed = self.create_embed("Message Deleted", desc, config.hex)

        channel = self.bot.get_channel(int(logs[str(message.guild.id)]))
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
            
        logs = await self.load_logs()
        if str(before.guild.id) not in logs:
            return

        desc = (f"{self.reply} Author: {before.author.mention}\n"
               f"{self.reply} Channel: {before.channel.mention}\n"
               f"{self.reply} Before:\n```{before.content}```\n"
               f"{self.reply} After:\n```{after.content}```")
        embed = self.create_embed("Message Edited", desc)

        channel = self.bot.get_channel(int(logs[str(before.guild.id)]))
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        logs = await self.load_logs()
        if str(member.guild.id) not in logs:
            return

        channel = self.bot.get_channel(int(logs[str(member.guild.id)]))
        if not channel:
            return

        if before.channel is None and after.channel:
            desc = f"{self.reply} {member.mention} joined {after.channel.mention}"
            embed = self.create_embed("Voice Channel Joined", desc, config.hex)
            embed.set_footer(text=f"Member ID: {member.id}",icon_url=self.bot.user.avatar)
            await channel.send(embed=embed)

        elif after.channel is None and before.channel:
            desc = f"{self.reply} {member.mention} left {before.channel.mention}"
            embed = self.create_embed("Voice Channel Left", desc, config.hex)
            embed.set_footer(text=f"Member ID: {member.id}",icon_url=self.bot.user.avatar)
            await channel.send(embed=embed)

        elif before.channel != after.channel:
            desc = f"{self.reply} {member.mention} moved from {before.channel.mention} to {after.channel.mention}"
            embed = self.create_embed("Voice Channel Moved", desc, config.hex)
            embed.set_footer(text=f"Member ID: {member.id}",icon_url=self.bot.user.avatar)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, member):
        logs = await self.load_logs()
        if str(guild.id) not in logs:
            return

        channel = self.bot.get_channel(int(logs[str(guild.id)]))
        if not channel:
            return

        try:
            audit_entry = [entry async for entry in guild.audit_logs(
                action=discord.AuditLogAction.unban,
                limit=1,
                after=datetime.utcnow() - timedelta(seconds=3)
            )][0]
            
            if audit_entry.target.id != member.id:
                return

            desc = f"{self.reply} User: {member}\n{self.reply} Unbanned by: {audit_entry.user}"
            embed = self.create_embed("User Unbanned", desc, config.hex)
            embed.add_field(
                name="User Information",
                value=f"**Created At:** <t:{int(member.created_at.timestamp())}:F> (<t:{int(member.created_at.timestamp())}:R>)\n```User ID: {member.id}\nModerator ID: {audit_entry.user.id}```"
            )
            await channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        logs = await self.load_logs()
        if str(guild.id) not in logs:
            return

        channel = self.bot.get_channel(int(logs[str(guild.id)]))
        if not channel:
            return

        try:
            audit_entry = [entry async for entry in guild.audit_logs(
                action=discord.AuditLogAction.ban,
                limit=1,
                after=datetime.utcnow() - timedelta(seconds=3)
            )][0]
            
            if audit_entry.target.id != member.id:
                return

            desc = f"{self.reply} User: {member}\n{self.reply} Banned by: {audit_entry.user}"
            embed = self.create_embed("User Banned", desc, config.hex)
            embed.add_field(
                name="User Information",
                value=f"**Created At:** <t:{int(member.created_at.timestamp())}:F> (<t:{int(member.created_at.timestamp())}:R>)\n```User ID: {member.id}\nModerator ID: {audit_entry.user.id}```"
            )
            await channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if len(messages) == 0:
            return
            
        logs = await self.load_logs()
        if str(messages[0].guild.id) not in logs:
            return

        desc = f"{self.reply} Channel: {messages[0].channel.mention}\n{self.reply} Messages Deleted: {len(messages)}"
        embed = self.create_embed("Bulk Messages Deleted", desc, config.hex)

        channel = self.bot.get_channel(int(logs[str(messages[0].guild.id)]))
        if channel:
            await channel.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Logging(bot))