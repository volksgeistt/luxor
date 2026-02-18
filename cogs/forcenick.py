import discord
from discord.ext import commands
import json
import asyncio
from typing import Optional, Dict, List
from pathlib import Path
import logging
from config import config

class ForcenickPaginator(discord.ui.View):
    def __init__(self, embeds: List[discord.Embed]):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(emoji="<:prev:1229446062335328306>", style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(emoji="<:next:1229446448777527327>", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        try:
            await self.message.edit(view=self)
        except:
            pass

class ForceNickname(commands.Cog):    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_file = Path("db/forcenicks.json")
        self.db_file.parent.mkdir(exist_ok=True)
        self.force_nicknames: Dict[str, Dict[str, str]] = {}
        self.load_database()
     
        self.logger = logging.getLogger('force_nickname')
        self.logger.setLevel(logging.INFO)
        
    def load_database(self) -> None:
        try:
            if self.db_file.exists():
                with open(self.db_file, 'r') as f:
                    self.force_nicknames = json.load(f)
            else:
                self.force_nicknames = {}
                self.save_database()
        except Exception as e:
            self.logger.error(f"Failed to load database: {e}")
            self.force_nicknames = {}

    def save_database(self) -> None:
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.force_nicknames, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save database: {e}")

    def get_guild_nicknames(self, guild_id: int) -> Dict[str, str]:
        return self.force_nicknames.get(str(guild_id), {})

    async def create_embed(self, ctx: commands.Context, description: str) -> discord.Embed:
        embed = discord.Embed(
            description=description,
            color=discord.Color.blurple()
        )
        return embed

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick == after.nick:
            return
        guild_nicknames = self.get_guild_nicknames(before.guild.id)
        forced_nick = guild_nicknames.get(str(before.id))
        
        if forced_nick and after.nick != forced_nick:
            try:
                await after.edit(nick=forced_nick, reason="Reverted Nickname @ ForceNick Triggered")
            except discord.Forbidden:
                self.logger.warning(f"Failed to enforce nickname for {after.id} - Missing permissions")
            except Exception as e:
                self.logger.error(f"Error enforcing nickname: {e}")

    @commands.group(
        name="forcenick",
        aliases=["fn", "fnick", "forcednick", "fonick"],
        invoke_without_command=True
    )
    @commands.has_permissions(manage_nicknames=True)
    async def forcenick(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Forcenick Commands",
            color=discord.Color.blurple(),
            description=(
               f">>> `forcenick`, `forcenick add`, `forcenick remove`, `forcenick config`, `forcenick check`\n{config.ques_emoji} Example: `forcenick add <user> <nick>`"
            )
        )
        await ctx.send(embed=embed)

    @forcenick.command(name="add", help="setup forcenick of a user")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    async def forcenick_add(self, ctx: commands.Context, member: discord.Member, *, nickname: str):
        """Add a forced nickname to a member."""
        if not ctx.author.top_role.position > member.top_role.position and ctx.author != ctx.guild.owner:
            embed = await self.create_embed(
                ctx,
                f"{config.error_emoji} {ctx.author.mention}: you cannot force nickname a user with a higher or equal role."
            )
            return await ctx.send(embed=embed)
        if len(nickname) > 32:
            embed = await self.create_embed(
                ctx,
                f"{config.error_emoji} {ctx.author.mention}: please enter a shorter nickname."
            )
            return await ctx.send(embed=embed)

        guild_id = str(ctx.guild.id)
        member_id = str(member.id)

        if guild_id not in self.force_nicknames:
            self.force_nicknames[guild_id] = {}

        self.force_nicknames[guild_id][member_id] = nickname
        self.save_database()

        try:
            await member.edit(nick=nickname)
            embed = await self.create_embed(
                ctx,
                f"{config.tick} {ctx.author.mention}: forced nickname for {member.mention} set to **{nickname}**."
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = await self.create_embed(
                ctx,
                f"{config.error_emoji} {ctx.author.mention}: I don't have permission to change that user's nick."
            )
            await ctx.send(embed=embed)

    @forcenick.command(name="remove", help="removes forcenick of user")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    async def forcenick_remove(self, ctx: commands.Context, member: discord.Member):
        guild_id = str(ctx.guild.id)
        member_id = str(member.id)

        if guild_id in self.force_nicknames and member_id in self.force_nicknames[guild_id]:
            del self.force_nicknames[guild_id][member_id]
            if not self.force_nicknames[guild_id]: 
                del self.force_nicknames[guild_id]
            self.save_database()

            try:
                await member.edit(nick=None)
                embed = await self.create_embed(
                    ctx,
                    f"{config.tick} {ctx.author.mention}: removed forced nickname from {member.mention}."
                )
            except discord.Forbidden:
                embed = await self.create_embed(
                    ctx,
                    f"{config.error_emoji} {ctx.author.mention}: forced nickname removed, but can't update user nick in the guild due to permission limiations."
                )
        else:
            embed = await self.create_embed(
                ctx,
                f"{config.error_emoji} {ctx.author.mention}: uhh! {member.mention} has no forced nickname setup."
            )
        
        await ctx.send(embed=embed)

    @forcenick.command(name="list", aliases=["config"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    async def forcenick_list(self, ctx: commands.Context):
        guild_nicknames = self.get_guild_nicknames(ctx.guild.id)
        if not guild_nicknames:
            embed = await self.create_embed(
                ctx,
                f"{config.error_emoji} {ctx.author.mention}: no forced nicknames is set in this guild."
            )
            return await ctx.send(embed=embed)
        
        entries = []
        for member_id, nickname in guild_nicknames.items():
            member = ctx.guild.get_member(int(member_id))
            if member:
                entries.append(f"• {member.mention}: **{nickname}**")
            else:
                del self.force_nicknames[str(ctx.guild.id)][member_id]
                self.save_database()

        # Create embeds for pagination
        embeds = []
        items_per_page = 10
        pages = [entries[i:i + items_per_page] for i in range(0, len(entries), items_per_page)]
        
        for i, page in enumerate(pages, 1):
            embed = discord.Embed(
                description="\n".join(page),
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Page {i}/{len(pages)}", icon_url=self.bot.user.avatar)
            embed.set_author(name="forced-nick config", icon_url=self.bot.user.avatar)
            embeds.append(embed)

        # Send paginated message
        paginator = ForcenickPaginator(embeds)
        message = await ctx.send(embed=embeds[0], view=paginator)
        paginator.message = message

    @forcenick.command(name="check", help="checks forcenick of a user")
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def forcenick_check(self, ctx: commands.Context, member: discord.Member):
        guild_nicknames = self.get_guild_nicknames(ctx.guild.id)
        forced_nick = guild_nicknames.get(str(member.id))

        if forced_nick:
            embed = await self.create_embed(
                ctx,
                f"{config.tick} {ctx.author.mention}:  {member.mention} has a forced nickname: **{forced_nick}**"
            )
        else:
            embed = await self.create_embed(
                ctx,
                f"{config.error_emoji} {ctx.author.mention}:  {member.mention} does not have a forced nickname"
            )
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ForceNickname(bot))