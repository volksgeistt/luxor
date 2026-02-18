import discord
from discord.ext import commands, tasks
import json
import asyncio
import random
import datetime
import re
from config import config

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ACTIVE_GIVEAWAY_FILE = 'db/active_giveaways.json'
        self.GIVEAWAY_HISTORY_FILE = 'db/giveaway_history.json'
        self.giveaway_locks = {}
        self.check_giveaways.start()

    async def load_giveaways(self, file_path):
        try:
            async with asyncio.Lock():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except FileNotFoundError:
            return {}

    async def save_giveaways(self, giveaways, file_path):
        async with asyncio.Lock():
            with open(file_path, 'w') as f:
                json.dump(giveaways, f)

    async def archive_giveaway(self, giveaway_id, giveaway_data):
        history = await self.load_giveaways(self.GIVEAWAY_HISTORY_FILE)
        history[giveaway_id] = giveaway_data
        await self.save_giveaways(history, self.GIVEAWAY_HISTORY_FILE)

        active_giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
        if giveaway_id in active_giveaways:
            del active_giveaways[giveaway_id]
            await self.save_giveaways(active_giveaways, self.ACTIVE_GIVEAWAY_FILE)

    @staticmethod
    def parse_time(time_str):
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        pattern = re.compile(r'(\d+)([smhd])')
        return sum(int(value) * time_dict[unit] for value, unit in pattern.findall(time_str))

    @commands.group(aliases=["giveaway", "g"])
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gw(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(
                title="Giveaway Subcommands:",
                description=f">>> `gw start`, `gw end`, `gw list`, `gw reroll`\n{config.ques_emoji} Example: `gw start 1d 1 Nitro`",
                color=config.hex))

    @gw.command(name='start', help="starts a giveaway")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def start_giveaway(self, ctx, duration: str, winners: int, *, prize: str):
        giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
        guild_giveaways = [gw for gw in giveaways.values() if gw['guild_id'] == ctx.guild.id]
        
        if len(guild_giveaways) >= 3:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: each guild can only have up to 3 active giveaways.", color=config.hex))
            return

        try:
            duration_seconds = self.parse_time(duration)
            end_time = discord.utils.utcnow() + datetime.timedelta(seconds=duration_seconds)
        except ValueError:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: invalid duration! use time duration as (d/h/m/s)", color=config.hex))
            return

        if winners < 1:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: winners count must be at least 1!", color=config.hex))
            return

        giveaway_data = {
            'prize': prize,
            'host': ctx.author.id,
            'guild_id': ctx.guild.id,
            'channel_id': ctx.channel.id,
            'message_id': None,
            'end_time': end_time.isoformat(),
            'participants': [],
            'winners_count': winners,
            'ended': False,
            'winners': []
        }
        
        embed = discord.Embed(description=f"**Winner(s):** {str(winners)}\n**Hosted by:** {ctx.author.mention}\n**Ends:** <t:{int(end_time.timestamp())}:R>", color=config.hex)
        embed.set_author(name=prize, icon_url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.avatar)
        embed.set_footer(icon_url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.avatar, text=f"{self.bot.user.name} - Giveaway Module")
        
        message = await ctx.send("**🎉 GIVEAWAY 🎉**", embed=embed)
        await message.add_reaction("🎉")

        giveaway_data['message_id'] = message.id
        giveaway_id = str(message.id)
        giveaways[giveaway_id] = giveaway_data
        await self.save_giveaways(giveaways, self.ACTIVE_GIVEAWAY_FILE)

    @gw.command(name='list', help="list all active giveaways in the guild")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def list_giveaways(self, ctx):
        giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
        guild_giveaways = [gw for gw in giveaways.values() if gw['guild_id'] == ctx.guild.id]
        
        if not guild_giveaways:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: no active giveaways in this guild.", color=config.hex))
            return
        
        embed = discord.Embed(title="🎉 Active Giveaways 🎉", color=config.hex)
        for giveaway in guild_giveaways:
            channel = self.bot.get_channel(giveaway['channel_id'])
            end_time = datetime.datetime.fromisoformat(giveaway['end_time'])
            
            embed.add_field(
                name=f"Giveaway in #{channel.name if channel else 'Unknown'}",
                value=f"**Prize:** {giveaway['prize']}\n**Winners:** {giveaway['winners_count']}\n**Ends:** <t:{int(end_time.timestamp())}:R>\n**Message ID:** {giveaway['message_id']}",
                inline=False
            )
        
        embed.set_footer(text=f"{self.bot.user.name}", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.avatar)
        await ctx.send(embed=embed)

    @gw.command(name='end', help="end an active giveaway")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def end_giveaway_command(self, ctx, message_id: int):
        giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
        giveaway_id = str(message_id)
        
        if giveaway_id not in giveaways:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: no active giveaway found with that message ID.", color=config.hex))
            return
            
        if giveaways[giveaway_id]['guild_id'] != ctx.guild.id:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: that giveaway is not from this guild.", color=config.hex))
            return

        await self.end_giveaway(giveaway_id)
        await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: giveaway ended successfully.", color=config.hex))

    async def end_giveaway(self, giveaway_id):
        async with asyncio.Lock():
            if giveaway_id in self.giveaway_locks:
                return
            self.giveaway_locks[giveaway_id] = True

        try:
            giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
            if giveaway_id not in giveaways:
                return
                
            giveaway = giveaways[giveaway_id]
            if giveaway['ended']:
                return

            channel = self.bot.get_channel(giveaway['channel_id'])
            if not channel:
                await self.archive_giveaway(giveaway_id, giveaway)
                return

            # Remove duplicates and get unique participants
            participants = list(set(giveaway['participants']))
            total_participants = len(participants)

            if total_participants == 0:
                await channel.send(embed=discord.Embed(description=f"No valid participants in the giveaway for **{giveaway['prize']}**.", color=config.hex))
            else:
                winners_count = min(giveaway['winners_count'], total_participants)
                winners = random.sample(participants, winners_count)
                giveaway['winners'] = winners

                try:
                    message = await channel.fetch_message(int(giveaway_id))
                    embed = message.embeds[0]
                    
                    winners_mention = ", ".join(f"<@{winner}>" for winner in winners)
                    embed.description = f"**Winner{'s' if winners_count > 1 else ''}:** {winners_mention}\n**Total Participant(s):** {total_participants}\n**Ended:** <t:{int(discord.utils.utcnow().timestamp())}:R>"
                    embed.color = config.hex
                    
                    await message.edit(content="🎉 **GIVEAWAY ENDED** 🎉", embed=embed)
                    await channel.send(f"🎉 Congratulations {winners_mention}! You won **{giveaway['prize']}**!")
                    
                except discord.NotFound:
                    await channel.send("The giveaway message was not found. It may have been deleted.")

            giveaway['ended'] = True
            await self.archive_giveaway(giveaway_id, giveaway)

        finally:
            if giveaway_id in self.giveaway_locks:
                del self.giveaway_locks[giveaway_id]

    @gw.command(name='reroll', help="reroll a new winner from an ended giveaway")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def reroll_giveaway(self, ctx, message_id: int):
        history = await self.load_giveaways(self.GIVEAWAY_HISTORY_FILE)
        giveaway_id = str(message_id)
        
        if giveaway_id not in history:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: no ended giveaway found with that message ID.", color=config.hex))
            return

        giveaway = history[giveaway_id]
        if giveaway['guild_id'] != ctx.guild.id:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: that giveaway is not from this guild.", color=config.hex))
            return

        participants = list(set(giveaway['participants']))
        if not participants:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: no participants to reroll.", color=config.hex))
            return

        new_winner = random.choice(participants)
        while new_winner in giveaway['winners']:
            if len(participants) <= len(giveaway['winners']):
                await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: all participants have already won!", color=config.hex))
                return
            new_winner = random.choice(participants)

        giveaway['winners'].append(new_winner)
        await self.save_giveaways(history, self.GIVEAWAY_HISTORY_FILE)
        await ctx.send(f"🎉 The new winner is <@{new_winner}>! Congratulations!")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or str(reaction.emoji) != "🎉":
            return
        
        giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
        giveaway_id = str(reaction.message.id)
        
        if giveaway_id in giveaways and not giveaways[giveaway_id]['ended']:
            if user.id not in giveaways[giveaway_id]['participants']:
                giveaways[giveaway_id]['participants'].append(user.id)
                await self.save_giveaways(giveaways, self.ACTIVE_GIVEAWAY_FILE)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot or str(reaction.emoji) != "🎉":
            return
        
        giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
        giveaway_id = str(reaction.message.id)
        
        if giveaway_id in giveaways and not giveaways[giveaway_id]['ended']:
            if user.id in giveaways[giveaway_id]['participants']:
                giveaways[giveaway_id]['participants'].remove(user.id)
                await self.save_giveaways(giveaways, self.ACTIVE_GIVEAWAY_FILE)

    @tasks.loop(seconds=15)
    async def check_giveaways(self):
        giveaways = await self.load_giveaways(self.ACTIVE_GIVEAWAY_FILE)
        current_time = discord.utils.utcnow()
        
        for giveaway_id, giveaway in list(giveaways.items()):
            if not giveaway['ended']:
                end_time = datetime.datetime.fromisoformat(giveaway['end_time'])
                if current_time >= end_time:
                    await self.end_giveaway(giveaway_id)

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Giveaway(bot))