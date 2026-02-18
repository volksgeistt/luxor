import discord
from discord.ext import commands
import discord.ui as ui
import json
import os
from datetime import datetime
from config import config
import asyncio
from collections import defaultdict

tick = "<:tickuwuwuwu:1238458935648845875>"
error_emoji = "<:error_emojiiwuwuwuwu:1238459546922647602>"

class Config:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'db/voicemaster.json'
        self.ensure_db()

    def ensure_db(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({
                    'guilds': {},
                    'voice_channels': {}
                }, f)

    def load_db(self):
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def save_db(self, data):
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_guild_config(self, guild_id):
        db = self.load_db()
        return db['guilds'].get(str(guild_id))

    def set_guild_config(self, guild_id, config):
        db = self.load_db()
        db['guilds'][str(guild_id)] = config
        self.save_db(db)

    def remove_guild_config(self, guild_id):
        db = self.load_db()
        if str(guild_id) in db['guilds']:
            del db['guilds'][str(guild_id)]
        self.save_db(db)

    def add_voice_channel(self, guild_id, channel_id, owner_id):
        db = self.load_db()
        if 'voice_channels' not in db:
            db['voice_channels'] = {}
        
        db['voice_channels'][str(channel_id)] = {
            'guild_id': str(guild_id),
            'owner_id': str(owner_id),
            'members': [str(owner_id)],
            'created_at': datetime.now().isoformat()
        }
        self.save_db(db)

    def update_voice_channel_members(self, channel_id, member_ids):
        db = self.load_db()
        if str(channel_id) in db.get('voice_channels', {}):
            db['voice_channels'][str(channel_id)]['members'] = [str(mid) for mid in member_ids]
            self.save_db(db)

    def update_voice_channel_owner(self, channel_id, new_owner_id):
        db = self.load_db()
        if str(channel_id) in db.get('voice_channels', {}):
            db['voice_channels'][str(channel_id)]['owner_id'] = str(new_owner_id)
            self.save_db(db)

    def get_voice_channel_info(self, channel_id):
        db = self.load_db()
        return db.get('voice_channels', {}).get(str(channel_id))

    def remove_voice_channel(self, channel_id):
        db = self.load_db()
        if str(channel_id) in db.get('voice_channels', {}):
            del db['voice_channels'][str(channel_id)]
            self.save_db(db)

class UserLimitModal(ui.Modal):
    def __init__(self, bot, config):
        super().__init__(title="Set User Limit")
        self.bot = bot
        self.config = config
        
        self.limit = ui.TextInput(
            label="User Limit",
            placeholder="Enter max number of users (0-99)",
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.limit)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit.value)
            if limit < 0 or limit > 99:
                raise ValueError("Limit must be between 0 and 99")
            
            await interaction.user.voice.channel.edit(user_limit=limit)
            
            embed = discord.Embed(
                color=config.hex, 
                description=f"{tick} {interaction.user.mention}: Channel user limit set to **{limit}**"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError as ve:
            embed = discord.Embed(
                color=config.hex, 
                description=f"{error_emoji} {interaction.user.mention}: {str(ve)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                color=config.hex, 
                description=f"{error_emoji} {interaction.user.mention}: An error occurred: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class VCRenameModal(ui.Modal):
    def __init__(self, bot, config):
        super().__init__(title="Rename Your Channel")
        self.bot = bot
        self.config = config
        
        self.name = ui.TextInput(
            label="Voice Channel Name",
            placeholder="Give your channel a new name",
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            new_name = self.name.value
            await interaction.user.voice.channel.edit(name=new_name)
            
            embed = discord.Embed(
                color=config.hex, 
                description=f"{tick} {interaction.user.mention}: Voice channel renamed to **{new_name}**"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                color=config.hex, 
                description=f"{error_emoji} {interaction.user.mention}: An error occurred: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class VCManagementButtons(ui.View):
    def __init__(self, bot, config):
        super().__init__(timeout=None)
        self.bot = bot
        self.config = config

    @classmethod
    def create_view(cls, bot, config):
        view = cls(bot, config)
        view.add_item(view.lock_channel)
        view.add_item(view.unlock_channel)
        view.add_item(view.rename_channel)
        view.add_item(view.set_user_limit)
        view.add_item(view.kick_user)
        view.add_item(view.ban_user)
        view.add_item(view.invite_user)
        view.add_item(view.hide_channel)
        view.add_item(view.unhide_channel)
        view.add_item(view.claim_channel)
        view.add_item(view.transfer_channel)
        return view

    async def channel_permission_check(self, interaction):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        
        if not channel:
            await interaction.response.send_message(
                "You must be in a voice channel.", 
                ephemeral=True
            )
            return None

        channel_info = self.config.get_voice_channel_info(channel.id)
        
        if not channel_info:
            await interaction.response.send_message(
                "This is not a VoiceMaster channel.", 
                ephemeral=True
            )
            return None

        return channel, channel_info

    async def owner_check(self, interaction, channel_info):
        if str(interaction.user.id) != channel_info['owner_id']:
            await interaction.response.send_message(
                "Only the channel owner can perform this action.", 
                ephemeral=True
            )
            return False
        return True

    @ui.button(emoji=config.vm_lock, style=discord.ButtonStyle.gray, custom_id="lock_channel")
    async def lock_channel(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        # Owner check
        if not await self.owner_check(interaction, channel_info):
            return

        await channel.set_permissions(interaction.guild.default_role, connect=False)
        
        embed = discord.Embed(
            color=config.hex, 
            description=f"{tick} {interaction.user.mention}: Channel locked"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(emoji=config.vm_unlock, style=discord.ButtonStyle.gray, custom_id="unlock_channel")
    async def unlock_channel(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        if not await self.owner_check(interaction, channel_info):
            return

        await channel.set_permissions(interaction.guild.default_role, connect=True)
        
        embed = discord.Embed(
            color=config.hex, 
            description=f"{tick} {interaction.user.mention}: Channel unlocked"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(emoji=config.vm_rename, style=discord.ButtonStyle.gray, custom_id="rename_channel")
    async def rename_channel(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        if not await self.owner_check(interaction, channel_info):
            return

        rename_modal = VCRenameModal(self.bot, self.config)
        await interaction.response.send_modal(rename_modal)

    @ui.button(emoji=config.vm_limit, style=discord.ButtonStyle.gray, custom_id="set_user_limit")
    async def set_user_limit(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        if not await self.owner_check(interaction, channel_info):
            return

        limit_modal = UserLimitModal(self.bot, self.config)
        await interaction.response.send_modal(limit_modal)

    @ui.button(emoji=config.vm_kick, style=discord.ButtonStyle.gray, custom_id="kick_user")
    async def kick_user(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        if not await self.owner_check(interaction, channel_info):
            return

        channel_members = [
            member for member in channel.members 
            if member != interaction.user
        ]

        if not channel_members:
            await interaction.response.send_message(
                "There are no other users in the channel to kick.", 
                ephemeral=True
            )
            return

        select = ui.Select(
            placeholder="Select a user to kick",
            options=[
                discord.SelectOption(
                    label=member.display_name, 
                    value=str(member.id)
                ) for member in channel_members
            ]
        )

        async def kick_callback(select_interaction: discord.Interaction):
            user_id = select.values[0]
            member = interaction.guild.get_member(int(user_id))
            
            try:
                await member.move_to(None)
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{tick} {interaction.user.mention}: Kicked {member.mention} from the channel"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{error_emoji} {interaction.user.mention}: Failed to kick: {str(e)}"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = kick_callback
        view = ui.View()
        view.add_item(select)
        await interaction.response.send_message(view=view, ephemeral=True)

    @ui.button(emoji=config.vm_ban, style=discord.ButtonStyle.gray, custom_id="ban_user")
    async def ban_user(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        if not await self.owner_check(interaction, channel_info):
            return

        channel_members = [
            member for member in channel.members 
            if member != interaction.user
        ]

        if not channel_members:
            await interaction.response.send_message(
                "There are no other users in the channel to ban.", 
                ephemeral=True
            )
            return

        select = ui.Select(
            placeholder="Select a user to ban from this channel",
            options=[
                discord.SelectOption(
                    label=member.display_name, 
                    value=str(member.id)
                ) for member in channel_members
            ]
        )

        async def ban_callback(select_interaction: discord.Interaction):
            user_id = select.values[0]
            member = interaction.guild.get_member(int(user_id))
            
            try:
                await channel.set_permissions(member, connect=False)
                await member.move_to(None)
                
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{tick} {interaction.user.mention}: Banned {member.mention} from the channel"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{error_emoji} {interaction.user.mention}: Failed to ban: {str(e)}"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = ban_callback
        view = ui.View()
        view.add_item(select)
        await interaction.response.send_message(view=view, ephemeral=True)

    @ui.button(emoji=config.vm_inv, style=discord.ButtonStyle.gray, custom_id="invite_user")
    async def invite_user(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        if not await self.owner_check(interaction, channel_info):
            return

        select = ui.Select(
            placeholder="Select a user to invite to your channel",
            options=[
                discord.SelectOption(
                    label=member.display_name, 
                    value=str(member.id)
                ) for member in interaction.guild.members 
                if member not in channel.members and member.voice is None
            ]
        )

        async def invite_callback(select_interaction: discord.Interaction):
            user_id = select.values[0]
            member = interaction.guild.get_member(int(user_id))
            try:
                await channel.set_permissions(member, connect=True)
                invite_embed = discord.Embed(
                    color=config.hex,
                    description=f"📨 {interaction.user.mention} invited you to their voice channel: {channel.name}"
                )
                await member.send(embed=invite_embed)
                
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{tick} {interaction.user.mention}: Invited {member.mention} to the channel"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{error_emoji} {interaction.user.mention}: Failed to invite: {str(e)}"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = invite_callback
        view = ui.View()
        view.add_item(select)
        await interaction.response.send_message(view=view, ephemeral=True)

    @ui.button(emoji=config.vm_hide, style=discord.ButtonStyle.gray, custom_id="hide_channel")
    async def hide_channel(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data
        
        if not await self.owner_check(interaction, channel_info):
            return

        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        
        embed = discord.Embed(
            color=config.hex, 
            description=f"{tick} {interaction.user.mention}: Channel hidden"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(emoji=config.vm_unhide, style=discord.ButtonStyle.gray, custom_id="unhide_channel")
    async def unhide_channel(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data
        
        if not await self.owner_check(interaction, channel_info):
            return

        await channel.set_permissions(interaction.guild.default_role, view_channel=True)
        
        embed = discord.Embed(
            color=config.hex, 
            description=f"{tick} {interaction.user.mention}: Channel unhidden"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(emoji=config.vm_claim, style=discord.ButtonStyle.gray, custom_id="claim_channel")
    async def claim_channel(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data
        original_owner = interaction.guild.get_member(int(channel_info['owner_id']))
        
        if original_owner and original_owner in channel.members:
            await interaction.response.send_message(
                f"Cannot claim channel while original owner is present.", 
                ephemeral=True
            )
            return

        self.config.update_voice_channel_owner(channel.id, interaction.user.id)
        embed = discord.Embed(
            color=config.hex, 
            description=f"{tick} {interaction.user.mention}: Claimed the voice channel"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(emoji=config.vm_transfer, style=discord.ButtonStyle.gray, custom_id="transfer_channel")
    async def transfer_channel(self, interaction: discord.Interaction, button: ui.Button):
        channel_data = await self.channel_permission_check(interaction)
        if not channel_data:
            return

        channel, channel_info = channel_data

        if not await self.owner_check(interaction, channel_info):
            return

        channel_members = [
        member for member in channel.members 
        if member != interaction.user
    ]

        if not channel_members:
            await interaction.response.send_message(
                f"There are no other users in the channel to transfer ownership to.",
                ephemeral=True
            )
            return

        select = ui.Select(
            placeholder="Select a user to transfer channel ownership",
            options=[
                discord.SelectOption(
                    label=member.display_name, 
                    value=str(member.id)
                ) for member in channel_members
            ]
        )

        async def transfer_callback(select_interaction: discord.Interaction):
            user_id = select.values[0]
            new_owner = interaction.guild.get_member(int(user_id))
            try:
                self.config.update_voice_channel_owner(channel.id, new_owner.id)
            
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{tick} {interaction.user.mention}: Transferred channel ownership to {new_owner.mention}"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                embed = discord.Embed(
                    color=config.hex, 
                    description=f"{error_emoji} {interaction.user.mention}: Failed to transfer ownership: {str(e)}"
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = transfer_callback
        view = ui.View()
        view.add_item(select)
        await interaction.response.send_message(view=view, ephemeral=True)



class VoiceMaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config(bot)
        # Track channel creation cooldowns
        self.channel_creation_cooldowns = defaultdict(lambda: asyncio.Lock())
        # Track recent channel deletions to prevent duplicate deletions
        self.recently_deleted_channels = set()

    @commands.Cog.listener()
    async def on_ready(self):
        view = VCManagementButtons.create_view(self.bot, self.config)
        db = self.config.load_db()
        guilds = db.get('guilds', {})

        for guild_id, guild_config in guilds.items():
            try:
                guild = self.bot.get_guild(int(guild_id))
                if not guild:
                    continue
                interface_channel = guild.get_channel(guild_config.get('interface_channel_id'))
                if not interface_channel:
                    continue
                try:
                    async for message in interface_channel.history(limit=10):
                        if message.author == self.bot.user and message.embeds:
                            await message.edit(view=view)
                            break
                except Exception as e:
                    print(f"Error finding interface message in {guild.name}: {e}")
            
            except Exception as e:
                print(f"Error setting up VoiceMaster for guild {guild_id}: {e}")
        print(f"VoiceMaster setup complete. Logged in as {self.bot.user}")

    @commands.command(name="voicemaster",aliases=["vm","jointocreate","j2c","jtc"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def voicemaster(self, ctx, option=None):
        if option in ["setup", "set", "create"]:
            await self.setup_voicemaster(ctx)
        elif option in ["delete", "remove", "unset", "del"]:
            await self.unset_voicemaster(ctx)
        else:
            await ctx.send(embed=discord.Embed(title=f"VoiceMaster",description=f"`voicemaster setup`, `voicemaster delete`\nExample: `voicemaster setup`",color=discord.Color.blurple()))

    async def setup_voicemaster(self, ctx):
        if self.config.get_guild_config(ctx.guild.id):
            await ctx.send(embed=discord.Embed(description=f"{error_emoji} {ctx.author.mention}: voice master is already set up for this server.", color=discord.Color.blurple()))
            return

        category = await ctx.guild.create_category("VoiceMaster")
        interface_channel = await category.create_text_channel("interface",
        overwrites={category.guild.default_role: discord.PermissionOverwrite(send_messages=False)})
        join_channel = await category.create_voice_channel("create")

        config = {
            'category_id': category.id,
            'interface_channel_id': interface_channel.id,
            'join_channel_id': join_channel.id,
            'setup_timestamp': datetime.now().isoformat()
        }
        self.config.set_guild_config(ctx.guild.id, config)

        embed = discord.Embed(
            description="**Use the buttons below to manage your private voice channel.** <:stolen_emoji:1298284135894351893>",
            color=discord.Color.blurple()
        )
        embed.add_field(name=f"<:lockx:1318222979334934589> Lock", value="Prevent others from joining", inline=True)
        embed.add_field(name=f"<:unlockx:1318223331043967006> Unlock", value="Allow others to join", inline=True)
        embed.add_field(name=f"<:renamex:1318222966776926220> Rename", value="Change channel name", inline=True)
        embed.add_field(name=f"<:userlimitx:1318222982409093211> Set Limit", value="Limit max users", inline=True)
        embed.add_field(name=f"<:kickx:1318222976201527367> Kick", value="Remove a user", inline=True)
        embed.add_field(name=f"<:banx:1318222961546891365> Ban", value="Prevent user rejoining", inline=True)
        embed.add_field(name=f"<:invx:1318222973097742376> Invite", value="Invite users to your channel", inline=True)
        embed.add_field(name=f"<:hidex:1318222969868124160> Hide", value="Make channel invisible", inline=True)
        embed.add_field(name=f"<:unhide:1318223328229724220> Unhide", value="Make channel visible", inline=True)
        embed.add_field(name=f"<:claimx:1318222964390498396> Claim", value="Take ownership of empty channel", inline=True)
        embed.add_field(name=f"<:transferx:1318222985609482261> Transfer", value="Transfer channel ownership", inline=True)
        
        embed.set_footer(text=f"{self.bot.user.name} - VoiceMaster Interface",icon_url=self.bot.user.avatar)
        embed.set_author(name="VoiceMaster Controls",icon_url=self.bot.user.avatar)
        message = await interface_channel.send(embed=embed, view=VCManagementButtons(self.bot, self.config))
        await message.pin()
        await ctx.send(embed=discord.Embed(description=f"{tick} {ctx.author.mention}: voice master setup completed for this guild.",color=discord.Color.blurple()))

    async def unset_voicemaster(self, ctx):
        config = self.config.get_guild_config(ctx.guild.id)
        if not config:
            await ctx.send(embed=discord.Embed(description=f"{error_emoji} {ctx.author.mention}: voice master is not setup for this guild.",color=discord.Color.blurple()))
            return

        try:
            category = ctx.guild.get_channel(config['category_id'])
            if category:
                for channel in category.channels:
                    await channel.delete()
                await category.delete()
        except Exception as e:
            print(f"Error deleting channels: {e}")
        self.config.remove_guild_config(ctx.guild.id)
        await ctx.send(embed=discord.Embed(description=f"{tick} {ctx.author.mention}: deleted the voice master setup for this guild.",color=discord.Color.blurple()))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        config = self.config.get_guild_config(member.guild.id)
        if not config:
            return

        join_channel_id = config['join_channel_id']

        # Rapid join handling for channel creation
        if after.channel and after.channel.id == join_channel_id:
            async with self.channel_creation_cooldowns[member.guild.id]:
                try:
                    # Prevent multiple rapid channel creations
                    category = after.channel.category
                    new_channel = await category.create_voice_channel(f"{member.name}")
                    self.config.add_voice_channel(member.guild.id, new_channel.id, member.id)
                    await member.move_to(new_channel)
                except discord.HTTPException as e:
                    print(f"Channel creation error: {e}")
                    # Optionally, send an error message to the user or log
                    try:
                        await member.send(f"Could not create your voice channel. Please try again.")
                    except:
                        pass

        # Handle channel member tracking and cleanup
        if before.channel:
            try:
                channel_info = self.config.get_voice_channel_info(before.channel.id)
                if channel_info:
                    # Update members in the channel
                    current_members = [str(m.id) for m in before.channel.members]
                    self.config.update_voice_channel_members(before.channel.id, current_members)

                    # Cleanup empty channels with additional safeguards
                    if (before.channel.category and 
                        before.channel.category.id == config['category_id'] and 
                        before.channel.id != join_channel_id and 
                        len(before.channel.members) == 0):
                        
                        # Prevent duplicate deletions
                        if before.channel.id not in self.recently_deleted_channels:
                            await self.safe_delete_channel(before.channel)
            except Exception as e:
                print(f"Error processing voice state update: {e}")

    async def safe_delete_channel(self, channel):
        # Add channel to recently deleted to prevent multiple deletion attempts
        self.recently_deleted_channels.add(channel.id)
        
        try:
            # Remove from database
            self.config.remove_voice_channel(channel.id)
            
            # Delete channel with timeout
            await asyncio.wait_for(channel.delete(), timeout=5.0)
        except asyncio.TimeoutError:
            print(f"Timeout deleting channel {channel.id}")
        except discord.HTTPException as e:
            print(f"Error deleting channel {channel.id}: {e}")
        finally:
            # Remove from recently deleted after a short delay
            await asyncio.sleep(10)
            self.recently_deleted_channels.discard(channel.id)


async def setup(bot):
    await bot.add_cog(VoiceMaster(bot))
    voicemaster_cog = bot.get_cog('VoiceMaster')
    if voicemaster_cog:
        view = VCManagementButtons.create_view(bot, voicemaster_cog.config)
        bot.add_view(view)
