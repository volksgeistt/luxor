import discord
from discord.ext import commands
from typing import List
import asyncio
from config import config

class RoleAllCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ongoing_operations = set()

    class RoleConfirmation(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.confirmed = None

        @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.confirmed = True
            self.stop()
            await interaction.response.send_message(content="**Adding roles**", view=None)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.confirmed = False
            self.stop()
            await interaction.response.send_message(content="**Operation cancelled.**", view=None)

    async def process_role_assignment(self, members: List[discord.Member], role: discord.Role) -> tuple[int, int]:
        success_count = 0
        failed_count = 0

        for i in range(0, len(members), 10):
            chunk = members[i:i + 10]
            tasks = []
            
            for member in chunk:
                if role not in member.roles:
                    tasks.append(member.add_roles(role))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                    else:
                        success_count += 1
            
            await asyncio.sleep(0.5)

        return success_count, failed_count

    @commands.group(help="adds a role to all members in the guild",invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def roleall(self, ctx: commands.Context, role: discord.Role):
        """Add a role to all members"""
        if ctx.guild.id in self.ongoing_operations:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: another role operation is in progress.",color=config.hex))
            return

        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: bot doesn't have `manage_roles` permissions.",color=config.hex))
            return

        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: role is higher than the bot highest role.",color=config.hex))
            return

        members = ctx.guild.members
        view = self.RoleConfirmation()
        await ctx.send(embed=discord.Embed(description=f"Do you want to add {role.mention} to members?",color=config.hex), view=view)
        await view.wait()

        if view.confirmed:
            self.ongoing_operations.add(ctx.guild.id)
            try:
                success, failed = await self.process_role_assignment(members, role)
                embed = discord.Embed(
                    description=f"{config.tick} : Added {role.mention} to {str(success)} members.",
                    color=config.hex
                )
                await ctx.send(embed=embed)
            finally:
                self.ongoing_operations.remove(ctx.guild.id)

    @roleall.command(name="humans",help="adds a role to all humans in the guild")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def roleall_humans(self, ctx: commands.Context, role: discord.Role):
        if ctx.guild.id in self.ongoing_operations:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: another role operation is in progress.",color=config.hex))
            return

        members = [m for m in ctx.guild.members if not m.bot]
        view = self.RoleConfirmation()
        await ctx.send(embed=discord.Embed(description=f"Do you want to add {role.mention} to members?",color=config.hex), view=view)
        await view.wait()

        if view.confirmed:
            self.ongoing_operations.add(ctx.guild.id)
            try:
                success, failed = await self.process_role_assignment(members, role)
                embed = discord.Embed(
                    description=f"{config.tick} : Added {role.mention} to {str(success)} members.",
                    color=config.hex
                )
                await ctx.send(embed=embed)
            finally:
                self.ongoing_operations.remove(ctx.guild.id)

    @roleall.command(name="bots",help="adds a role to all bots in the guild")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def roleall_bots(self, ctx: commands.Context, role: discord.Role):
        """Add a role to all bots"""
        if ctx.guild.id in self.ongoing_operations:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: another role operation is in progress.",color=config.hex))
            return

        members = [m for m in ctx.guild.members if m.bot]
        view = self.RoleConfirmation()
        await ctx.send(embed=discord.Embed(description=f"Do you want to add {role.mention} to members?",color=config.hex), view=view)
        await view.wait()

        if view.confirmed:
            self.ongoing_operations.add(ctx.guild.id)
            try:
                success, failed = await self.process_role_assignment(members, role)
                embed = discord.Embed(
                    description=f"{config.tick} : Added {role.mention} to {str(success)} members.",
                )
                await ctx.send(embed=embed)
            finally:
                self.ongoing_operations.remove(ctx.guild.id)

async def setup(bot):
    await bot.add_cog(RoleAllCog(bot))