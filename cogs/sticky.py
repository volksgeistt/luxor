import discord
from discord.ext import commands
import json
import asyncio
from collections import defaultdict
import time
from config import config

class StickyMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_messages = {}
        self.last_sticky_message = {}
        self.message_queue = defaultdict(list)
        self.processing_lock = defaultdict(asyncio.Lock)
        self.last_update = defaultdict(float)
        self.UPDATE_INTERVAL = 1.0  # Reduced from 5.0 to 1.0 for faster updates
        self.load_sticky_messages()
        self.bot.loop.create_task(self.process_message_queue())

    def load_sticky_messages(self):
        try:
            with open('db/sticky.json', 'r') as f:
                data = json.load(f)
                self.sticky_messages = data.get('messages', {})
                self.last_sticky_message = data.get('last_messages', {})
        except FileNotFoundError:
            self.sticky_messages = {}
            self.last_sticky_message = {}

    def save_sticky_messages(self):
        data = {
            'messages': self.sticky_messages,
            'last_messages': self.last_sticky_message
        }
        with open('db/sticky.json', 'w') as f:
            json.dump(data, f, indent=4)

    async def process_message_queue(self):
        while True:
            try:
                for channel_key, queue in list(self.message_queue.items()):
                    if not queue:
                        continue
                    guild_id, channel_id = channel_key
                    current_time = time.time()
                    if current_time - self.last_update[channel_key] < self.UPDATE_INTERVAL:
                        continue
                    
                    async with self.processing_lock[channel_key]:
                        if not queue:
                            continue
                        channel = self.bot.get_channel(channel_id)
                        if not channel:
                            continue

                        for sticky_id, message_content in self.sticky_messages.get(str(guild_id), {}).items():
                            if message_content['channel_id'] == channel_id:
                                last_msg_key = f"{guild_id}-{channel_id}-{sticky_id}"
                                
                                if last_msg_key in self.last_sticky_message:
                                    try:
                                        old_msg = await channel.fetch_message(self.last_sticky_message[last_msg_key])
                                        await old_msg.delete()
                                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                                        pass

                                try:
                                    sticky_msg = await channel.send(message_content['message'])
                                    self.last_sticky_message[last_msg_key] = sticky_msg.id
                                    self.sticky_messages[str(guild_id)][sticky_id]['last_message_id'] = sticky_msg.id
                                    self.save_sticky_messages()
                                except discord.HTTPException as e:
                                    print(f"Error sending sticky message: {e}")
                                    continue

                        self.message_queue[channel_key].clear()
                        self.last_update[channel_key] = current_time
            except Exception as e:
                print(f"Error in process_message_queue: {e}")
            await asyncio.sleep(0.5)  # Reduced sleep time for faster processing

    @commands.Cog.listener()
    async def on_ready(self):
        print("Sticky Messages Cog: Restoring sticky messages...")
        for guild_id, guild_data in self.sticky_messages.items():
            for sticky_id, message_data in guild_data.items():
                channel_id = message_data['channel_id']
                channel = self.bot.get_channel(channel_id)
                if channel:
                    channel_key = (guild_id, channel_id)
                    self.message_queue[channel_key].append((sticky_id, message_data['message']))
                    print(f"Queued sticky message {sticky_id} for channel {channel_id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.sticky_messages:
            return

        # Check if there's any sticky message for this channel
        has_sticky = False
        for sticky_data in self.sticky_messages[guild_id].values():
            if sticky_data['channel_id'] == message.channel.id:
                has_sticky = True
                break

        if has_sticky:
            channel_key = (guild_id, message.channel.id)
            # Add to queue only if not already being processed
            async with self.processing_lock[channel_key]:
                if not self.message_queue[channel_key]:
                    self.message_queue[channel_key].append(("trigger", ""))
                    self.last_update[channel_key] = 0  # Reset the last update time to trigger immediate processing

    # [Rest of the commands remain the same...]
    @commands.group(name='sticky', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def sticky(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title="Sticky Messages", description=f"`sticky`, `sticky create`, `sticky delete`, `sticky show`, `sticky reset`\n{config.ques_emoji} Example: `sticky create 001 #text Hello`", color=config.hex))

    @sticky.command(name='create', help="create a sticky message in the guild")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def create_sticky(self, ctx, sticky_id: str, channel: discord.TextChannel, *, message: str):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.sticky_messages:
            self.sticky_messages[guild_id] = {}
        
        self.sticky_messages[guild_id][sticky_id] = {
            'channel_id': channel.id,
            'message': message,
            'last_message_id': None
        }
        
        self.save_sticky_messages()
        
        channel_key = (guild_id, channel.id)
        self.message_queue[channel_key].append((sticky_id, message))
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: sticky message with id `{sticky_id}` created in {channel.mention}", color=config.hex))

    @sticky.command(name='remove', aliases=["delete"], help="removes a specific sticky message with the provided id")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def remove_sticky(self, ctx, sticky_id: str):
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.sticky_messages and sticky_id in self.sticky_messages[guild_id]:
            channel_id = self.sticky_messages[guild_id][sticky_id]['channel_id']
            last_msg_key = f"{guild_id}-{channel_id}-{sticky_id}"
            
            if last_msg_key in self.last_sticky_message:
                channel = self.bot.get_channel(channel_id)
                try:
                    msg = await channel.fetch_message(self.last_sticky_message[last_msg_key])
                    await msg.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass
                del self.last_sticky_message[last_msg_key]
            
            del self.sticky_messages[guild_id][sticky_id]
            if not self.sticky_messages[guild_id]:
                del self.sticky_messages[guild_id]
            
            self.save_sticky_messages()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: sticky message with id `{sticky_id}` has been removed.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: sticky message with id `{sticky_id}` not found", color=config.hex))

    @sticky.command(name='show', help="shows all the sticky messages setup in the guild")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def show_sticky(self, ctx):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.sticky_messages or not self.sticky_messages[guild_id]:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no sticky messages set up in this server.", color=config.hex))
            return
        
        embed = discord.Embed(color=config.hex)
        embed.set_author(name=f"Sticky Messages", icon_url=self.bot.user.avatar)
        for sticky_id, data in self.sticky_messages[guild_id].items():
            channel = self.bot.get_channel(data['channel_id'])
            channel_name = channel.mention if channel else "Unknown Channel"
            embed.add_field(
                name=f"ID: {sticky_id}",
                value=f"Channel: {channel_name}\nMessage:\n```{data['message'][:1000]}```",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @sticky.command(name='reset', help="clear all the sticky messages setup in the guild")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def reset_sticky(self, ctx):
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.sticky_messages:
            for sticky_id, data in self.sticky_messages[guild_id].items():
                channel_id = data['channel_id']
                last_msg_key = f"{guild_id}-{channel_id}-{sticky_id}"
                
                if last_msg_key in self.last_sticky_message:
                    channel = self.bot.get_channel(channel_id)
                    try:
                        msg = await channel.fetch_message(self.last_sticky_message[last_msg_key])
                        await msg.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
                    del self.last_sticky_message[last_msg_key]
            
            del self.sticky_messages[guild_id]
            self.save_sticky_messages()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: all sticky messages have been removed.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: uhh!? no sticky messages to reset.", color=config.hex))

async def setup(bot):
    await bot.add_cog(StickyMessages(bot))