import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime
import logging
from typing import List, Dict, Any
from config import config

ALLOWED_USER_IDS = config.owner_ids
SUPPORT_SERVER_WL = [1295611048266563605]
GLOBAL_BAN_FILE = "global_bans.json"
BATCH_SIZE = 5
COOLDOWN = 5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfirmView(discord.ui.View):
    def __init__(self, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

class PaginationView(discord.ui.View):
    def __init__(self, embeds: List[discord.Embed]):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])
        else:
            await interaction.response.defer()

class GlobalBan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.global_bans = self.load_global_bans()

    def load_global_bans(self) -> Dict[str, Any]:
        if os.path.exists(GLOBAL_BAN_FILE):
            with open(GLOBAL_BAN_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_global_bans(self):
        with open(GLOBAL_BAN_FILE, 'w') as f:
            json.dump(self.global_bans, f, indent=4)

    async def batch_ban(self, guilds: List[discord.Guild], target: discord.User, reason: str) -> int:
        successful_bans = 0
        for i in range(0, len(guilds), BATCH_SIZE):
            batch = guilds[i:i+BATCH_SIZE]
            tasks = [self.ban_user(guild, target, reason) for guild in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_bans += sum(1 for result in results if result)
            await asyncio.sleep(COOLDOWN)
        return successful_bans

    async def ban_user(self, guild: discord.Guild, target: discord.User, reason: str) -> bool:
        try:
            await guild.ban(target, reason=reason)
            logger.info(f"Banned {target} ({target.id}) from {guild.name} ({guild.id})")
            return True
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to ban {target} ({target.id}) in {guild.name} ({guild.id}): {str(e)}")
            return False

    @commands.group(name="globalban", invoke_without_command=True, aliases=["gb"])
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def glban(self, ctx):
      embed = discord.Embed(
          title="Global-Ban Subcommands:",
          description=
          f">>> `globalban add`, `globalban remove`, `globalban config`, `globalban sync`\n{config.ques_emoji} Example: `globalban add <user>`",
          color=config.hex)
      await ctx.reply(embed=embed)


    @glban.command(name="add", help="Globally bans a user from all servers the bot is in.")
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def add_(self, ctx: commands.Context, target: discord.User, *, reason: str = "No reason provided"):
        if ctx.author.id not in ALLOWED_USER_IDS:
            await ctx.send("You do not have permission to use this command.")
            return

        confirmation = await self.confirm_ban(ctx, target)
        if not confirmation:
            await ctx.send("Global ban cancelled.")
            return

        ban_animation = ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛']
        progress_message = await ctx.send("Initiating global ban...")

        eligible_guilds = [guild for guild in self.bot.guilds if guild.id not in SUPPORT_SERVER_WL]
        total_guilds = len(eligible_guilds)

        successful_bans = await self.batch_ban(eligible_guilds, target, f"Global ban by {ctx.author}: {reason}")

        for i in range(total_guilds):
            animation_frame = ban_animation[i % len(ban_animation)]
            await progress_message.edit(content=f"{animation_frame} Banning in progress... ({i+1}/{total_guilds})")
            await asyncio.sleep(0.5)

        self.global_bans[str(target.id)] = {
            "reason": reason,
            "banned_by": ctx.author.id,
            "ban_time": discord.utils.utcnow().isoformat(),
            "successful_bans": successful_bans
        }
        self.save_global_bans()

        ban_embed = discord.Embed(
            color=discord.Color.red(),
            title=":hammer: Global Ban Completed :hammer:",
            description=f"**{target}** has been globally banned from {successful_bans} servers."
        )
        ban_embed.set_thumbnail(url=target.display_avatar.url)
        ban_embed.add_field(name="Banned User", value=f"{target} ({target.id})", inline=True)
        ban_embed.add_field(name="Banned By", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        ban_embed.add_field(name="Reason", value=reason, inline=False)
        ban_embed.set_footer(text="Action performed at")
        ban_embed.timestamp = discord.utils.utcnow()

        await progress_message.delete()
        await ctx.send(embed=ban_embed)
        logger.info(f"Global ban completed for {target} ({target.id}) by {ctx.author} ({ctx.author.id})")

    @glban.command(name="remove", help="Removes a user from the global ban list.")
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def _remove__(self, ctx: commands.Context, user_id: int):
        if ctx.author.id not in ALLOWED_USER_IDS:
            await ctx.send("You do not have permission to use this command.")
            return

        if str(user_id) in self.global_bans:
            del self.global_bans[str(user_id)]
            self.save_global_bans()
            await ctx.send(f"User with ID {user_id} has been removed from the global ban list.")
            logger.info(f"User {user_id} removed from global ban list by {ctx.author} ({ctx.author.id})")
        else:
            await ctx.send(f"User with ID {user_id} is not in the global ban list.")

    @glban.command(name="config", help="Displays the list of globally banned users.")
    @commands.has_permissions(ban_members=True)
    async def config__(self, ctx: commands.Context):
        if ctx.author.id not in ALLOWED_USER_IDS:
            await ctx.send("You do not have permission to use this command.")
            return

        if not self.global_bans:
            await ctx.send("There are no globally banned users.")
            return

        embeds = []
        users_per_page = 5
        user_list = list(self.global_bans.items())

        for i in range(0, len(user_list), users_per_page):
            embed = discord.Embed(
                title="Global Ban List",
                color=discord.Color.blurple(),
                description=f"Page {len(embeds) + 1}/{-(-len(user_list) // users_per_page)}"
            )

            for user_id, ban_info in user_list[i:i+users_per_page]:
                ban_time = datetime.fromisoformat(ban_info['ban_time'])
                embed.add_field(
                    name=f"User ID: {user_id}",
                    value=f"Reason: {ban_info['reason']}\n"
                          f"Banned by: <@{ban_info['banned_by']}>\n"
                          f"Ban time: <t:{int(ban_time.timestamp())}:F>\n"
                          f"Banned from: {ban_info.get('successful_bans', 'Unknown')} servers",
                    inline=False
                )

            embeds.append(embed)

        view = PaginationView(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @glban.command(name="sync", help="Synchronizes bans across all servers.")
    @commands.is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def __sync__(self, ctx: commands.Context):
        if ctx.author.id not in ALLOWED_USER_IDS:
            await ctx.send("You do not have permission to use this command.")
            return

        progress_message = await ctx.send("Initiating ban synchronization...")

        for user_id, ban_info in self.global_bans.items():
            target = await self.bot.fetch_user(int(user_id))
            if not target:
                continue

            reason = f"Global ban sync: {ban_info['reason']}"
            eligible_guilds = [guild for guild in self.bot.guilds if guild.id not in SUPPORT_SERVER_WL]
            
            await self.batch_ban(eligible_guilds, target, reason)

            # Unban from support servers if banned
            for guild_id in SUPPORT_SERVER_WL:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    try:
                        await guild.unban(target, reason="Global ban sync: Support server whitelist")
                        logger.info(f"Unbanned {target} ({target.id}) from support server {guild.name} ({guild.id})")
                    except discord.NotFound:
                        pass 
                    except (discord.Forbidden, discord.HTTPException) as e:
                        logger.error(f"Failed to unban {target} ({target.id}) from support server {guild.name} ({guild.id}): {str(e)}")

        await progress_message.edit(content="Ban synchronization completed.")
        logger.info("Ban synchronization completed")

    async def confirm_ban(self, ctx: commands.Context, target: discord.User) -> bool:
        view = ConfirmView()
        confirm_embed = discord.Embed(
            title="Confirm Global Ban",
            description=f"Are you sure you want to ban {target} ({target.id}) globally from all servers?",
            color=discord.Color.blurple()
        )
        confirm_message = await ctx.send(embed=confirm_embed, view=view)
        
        await view.wait()
        await confirm_message.delete()
        
        return view.value

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if str(member.id) in self.global_bans:
            if member.guild.id in SUPPORT_SERVER_WL:
                logger.info(f"Allowing {member} ({member.id}) to join support server {member.guild.name} ({member.guild.id})")
                return

            ban_info = self.global_bans[str(member.id)]
            try:
                await member.guild.ban(member, reason=f"Global ban: {ban_info['reason']}")
                logger.info(f"Auto-banned {member} ({member.id}) from {member.guild.name} ({member.guild.id})")
            except (discord.Forbidden, discord.HTTPException) as e:
                logger.error(f"Failed to auto-ban {member} ({member.id}) in {member.guild.name} ({member.guild.id}): {str(e)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(GlobalBan(bot))