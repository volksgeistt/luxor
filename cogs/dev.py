from discord.ext import commands
import discord
from config import config
import os
import asyncio
import datetime
import zipfile

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(usage="reload", hidden=True, help="reload all cogs")
    @commands.guild_only()
    @commands.is_owner()
    async def reload(self, ctx):
        W = 0
        for file in os.listdir(f"./cogs"):
            if file.endswith(".py"):
                W += 1
                await self.bot.reload_extension(f"cogs.{file[:-3]}")
        embed = discord.Embed(
            color=config.hex,
            description=
            f"{config.tick} {ctx.author.mention}: reloaded `{W}` cogs with `{len(set(ctx.bot.walk_commands()))}` cmds."
        )
        await ctx.send(embed=embed)

    @commands.command(name="leaveg", aliases=["leave-guild","leave-g"], help="leaves a guild whose id is provided.")
    @commands.is_owner()
    @commands.guild_only()
    async def leave_guild(self, ctx, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: please provide any valid guild id.", color=config.hex))
            return
        try:
            await guild.leave()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: left the guild: {guild.name} ({guild.id})", color=config.hex))
        except Exception as e:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an error occurred: {e}", color=config.hex))

    @commands.command(name="broadcast", aliases=["bc"], help="globally broadcast message to all guilds")
    @commands.is_owner()
    async def broadcast(self, ctx, *, message):
        sent = 0
        failed = 0
        embed = discord.Embed(
            description=message,
            color=config.hex,
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name="Broadcasting Message ~ Luxor", icon_url=self.bot.user.avatar)
        embed.set_footer(text=f"Sent by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        processing_msg = await ctx.send("🔃 Broadcasting message...!")
        
        for guild in self.bot.guilds:
            try:
                channel = guild.system_channel or guild.text_channels[0]
                await channel.send(embed=embed)
                sent += 1
                await asyncio.sleep(0.5)
            except:
                failed += 1
                
        await processing_msg.edit(content=f"✅ Broadcast completed! Sent to {sent} servers, failed in {failed} servers.")

    @commands.command(name="backupdb", help="Create a backup of the db/ directory")
    @commands.is_owner()
    async def backup_database(self, ctx):
        db_path = os.path.join(os.getcwd(), 'db')
        if not os.path.exists(db_path):
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} No db/ directory found.", 
                color=config.hex
            ))
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.zip"
        backup_path = os.path.join(os.getcwd(), backup_filename)

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(db_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, db_path)
                        zipf.write(file_path, arcname=os.path.join('db', arcname))

            try:
                await ctx.author.send(
                    content="Database backup created.",
                    file=discord.File(backup_path, filename=backup_filename)
                )
                await ctx.send(embed=discord.Embed(
                    description=f"{config.tick} Backup successfully created and sent to your DMs.", 
                    color=config.hex
                ))
            except discord.HTTPException as e:
                await ctx.send(embed=discord.Embed(
                    description=f"{config.error_emoji} Failed to send backup: {e}", 
                    color=config.hex
                ))

        except Exception as e:
            await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} Backup creation failed: {e}", 
                color=config.hex
            ))

        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)

async def setup(bot):
    await bot.add_cog(Dev(bot))