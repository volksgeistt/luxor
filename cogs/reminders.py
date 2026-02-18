import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import re
import json
import os
from config import config

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_file = "db/reminders.json"
        self.reminders = self.load_reminders()
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()
        self.save_reminders()

    def load_reminders(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    for reminder in data:
                        reminder['time'] = datetime.datetime.fromisoformat(reminder['time'])
                    return data
            except Exception as e:
                print(f"Error loading reminders: {e}")
                return []
        return []

    def save_reminders(self):
        """Save reminders to JSON file"""
        try:
            data = []
            for reminder in self.reminders:
                reminder_copy = reminder.copy()
                reminder_copy['time'] = reminder_copy['time'].isoformat()
                data.append(reminder_copy)
                
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving reminders: {e}")

    def parse_time(self, time_str):
        total_seconds = 0
        time_units = {
            'w': 604800,
            'd': 86400,
            'h': 3600,
            'm': 60,
            's': 1
        }
        
        pattern = r'(\d+)([wdhms])'
        matches = re.findall(pattern, time_str.lower())
        
        if not matches:
            return None
            
        for value, unit in matches:
            total_seconds += int(value) * time_units[unit]
            
        return total_seconds

    def get_next_id(self):
        """Get next available reminder ID"""
        if not self.reminders:
            return 1
        return max(r['remind_id'] for r in self.reminders) + 1

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def remind(self, ctx, time: str, *, reminder: str):
        seconds = self.parse_time(time)
        
        if not seconds:
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention} : invalid time format! Use combinations of w(weeks), d(days), h(hours), m(minutes), s(seconds)\nExample: 1h30m",
                color=config.hex
            ))

        if seconds > 2592000: 
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention} : reminders cannot be set for more than 30 days",
                color=config.hex
            ))

        # Check if DMs are open
        try:
            await ctx.author.send()
        except discord.Forbidden:
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention} : I cannot send you DMs! Please enable DMs from server members to receive reminders.",
                color=config.hex
            ))
        except:
            pass

        reminder_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        
        reminder_data = {
            'user_id': ctx.author.id,
            'channel_id': ctx.channel.id, 
            'guild_id': ctx.guild.id,     
            'message': reminder,
            'time': reminder_time,
            'remind_id': self.get_next_id()
        }
        
        self.reminders.append(reminder_data)
        self.save_reminders()
        
        time_str = []
        if seconds >= 86400:
            days = seconds // 86400
            time_str.append(f"{days} day{'s' if days != 1 else ''}")
            seconds %= 86400
        if seconds >= 3600:
            hours = seconds // 3600
            time_str.append(f"{hours} hour{'s' if hours != 1 else ''}")
            seconds %= 3600
        if seconds >= 60:
            minutes = seconds // 60
            time_str.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            seconds %= 60
        if seconds > 0:
            time_str.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        formatted_time = ", ".join(time_str)
        
        await ctx.send(embed=discord.Embed(
            description=f"{config.tick} {ctx.author.mention} : I will remind you about `{reminder}` in {formatted_time}.",
            color=config.hex
        ))

    @remind.command(name="list")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def remind_list(self, ctx):
        """List all your active reminders"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]
        
        if not user_reminders:
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention} : you don't have any active reminders",
                color=config.hex
            ))
        
        embed = discord.Embed(
            title="Active Reminders",
            color=config.hex
        )
        
        for reminder in user_reminders:
            time_left = reminder['time'] - datetime.datetime.utcnow()
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            
            time_str = []
            if time_left.days > 0:
                time_str.append(f"{time_left.days}d")
            if hours > 0:
                time_str.append(f"{hours}h")
            if minutes > 0:
                time_str.append(f"{minutes}m")
                
            formatted_time = " ".join(time_str)
            
            guild = self.bot.get_guild(reminder['guild_id'])
            guild_name = guild.name if guild else "Unknown Server"
            
            embed.add_field(
                name=f"ID: {reminder['remind_id']}",
                value=f"Message: {reminder['message']}\nTime left: {formatted_time}\nSet in: {guild_name}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @remind.command(name="remove")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def remind_remove(self, ctx, remind_id: int):
        reminder = next((r for r in self.reminders 
                        if r['user_id'] == ctx.author.id and r['remind_id'] == remind_id), None)
        
        if not reminder:
            return await ctx.send(embed=discord.Embed(
                description=f"{config.error_emoji} {ctx.author.mention} : couldn't find a reminder with that ID.",
                color=config.hex
            ))
        
        self.reminders.remove(reminder)
        self.save_reminders()
        
        await ctx.send(embed=discord.Embed(
            description=f"{config.tick} {ctx.author.mention} : successfully removed the reminder.",
            color=config.hex
        ))

    @tasks.loop(seconds=15)
    async def check_reminders(self):
        current_time = datetime.datetime.utcnow()
        reminders_copy = self.reminders.copy()
        need_save = False
        
        for reminder in reminders_copy:
            if current_time >= reminder['time']:
                user = self.bot.get_user(reminder['user_id'])
                
                if user:
                    try:
                        guild = self.bot.get_guild(reminder['guild_id'])
                        guild_name = guild.name if guild else "a server"
                        
                        embed = discord.Embed(
                            description=f"**{reminder['message']}**\n*This reminder was set in: {guild_name}*",
                            color=config.hex,
                            timestamp=current_time
                        )
                        embed.set_author(name=f"Reminder",icon_url=self.bot.user.avatar)
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        channel = self.bot.get_channel(reminder['channel_id'])
                        if channel:
                            await channel.send(embed=discord.Embed(
                                description=f"🔔 {user.mention} : I couldn't send your reminder in DM, so here it is: {reminder['message']}\n\n*Note: Please enable DMs to receive future reminders privately.*",
                                color=config.hex
                            ))
                
                self.reminders.remove(reminder)
                need_save = True
        
        if need_save:
            self.save_reminders()

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminder(bot))