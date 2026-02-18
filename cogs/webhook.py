import discord
import aiohttp
import string
import random
import json
import os
from discord import Webhook
from discord.ext import commands
from datetime import datetime
from config import config

def load_webhooks():
    if os.path.exists('db/webhooks.json'):
        with open('db/webhooks.json', 'r') as f:
            return json.load(f)
    return {}

def save_webhooks(data):
    with open('db/webhooks.json', 'w') as f:
        json.dump(data, f, indent=4, default=str)

async def codeGen(size=6, chars=string.ascii_uppercase + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

class WebhookPaginator(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=300)
        self.embeds = embeds
        self.current_page = 0
        
    async def update_message(self, interaction: discord.Interaction):
        embed = self.embeds[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:prev:1229446062335328306>", style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(emoji="<:next:1229446448777527327>", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_message(interaction)


class WebhookManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhooks = load_webhooks()
        self.webhook_limit = 5

    def get_guild_webhooks(self, guild_id):
        return self.webhooks.get(str(guild_id), {})

    @commands.group(aliases=['webhooks', 'w'])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def webhook(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=f"Webhook Manager",
                description=f"`webhook`, `webhook create`, `webhook delete`, `webhook list`, `webhook edit`, `webhook edit name`, `webhook edit avatar`\n{config.ques_emoji} Example: `webhook create <name> [channel] [avatarURL]`",
                color=config.hex
            )
            await ctx.send(embed=embed)

    @webhook.command(aliases=['add', 'make'])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def create(self, ctx, name: str, channel: discord.TextChannel = None, avatar: str = None):
        guild_webhooks = self.get_guild_webhooks(ctx.guild.id)
        if len(guild_webhooks) >= self.webhook_limit:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this server has reached the maximum limit of `{self.webhook_limit}` webhook creation using the bot.", color=config.hex))
            return

        async with ctx.typing():
            if channel is None:
                channel = ctx.channel
                

            avatar_bytes = None
            if avatar and avatar.startswith('https://'):
                async with aiohttp.ClientSession() as session:
                    async with session.get(avatar) as response:
                        if response.status == 200:
                            avatar_bytes = await response.read()

            try:
                webhook = await channel.create_webhook(
                    name=name,
                    avatar=avatar_bytes,
                    reason=f"action executed by ~ {ctx.author}"
                )
            except discord.Forbidden:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: I don't have permission to create webhooks in that channel.", color=config.hex))
            except discord.HTTPException as e:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: Failed to create webhook: {str(e)}", color=config.hex))

            code = await codeGen()
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.webhooks:
                self.webhooks[guild_id] = {}
                
            self.webhooks[guild_id][code] = {
                "url": webhook.url,
                "channel": channel.mention,
                "time": datetime.now().timestamp(),
                "name": name,
                "creator": str(ctx.author)
            }
            
            save_webhooks(self.webhooks)
            
            embed = discord.Embed(
                description=f"{config.tick} {ctx.author.mention}: webhook creation successful.\n> **Code:** `{code}`\n> **Name:** {name}\n> **Channel:** {channel.mention}\n*Keep this code safe, You'll need it to manage the webhook.*",
                color=config.hex
            )
            await ctx.send(embed=embed)

    @webhook.command(aliases=['list', 'all'])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def view(self, ctx):
        guild_webhooks = self.get_guild_webhooks(ctx.guild.id)
        
        if not guild_webhooks:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : no webhooks found for this server!", color=config.hex))

        embeds = []
        for code, data in guild_webhooks.items():
            embed = discord.Embed(
                color=config.hex
            )
            
            created_at = f"<t:{int(data['time'])}:F>"
            relative_time = f"<t:{int(data['time'])}:R>"
            
            embed.add_field(name="Code", value=f"`{code}`", inline=False)
            embed.add_field(name="Name", value=data['name'], inline=True)
            embed.add_field(name="Channel", value=data['channel'], inline=True)
            embed.add_field(name="Created By", value=data['creator'], inline=True)
            embed.add_field(name="Created At", value=f"{created_at}\n({relative_time})", inline=False)
            embed.set_author(name=f"Webhook Information",icon_url=self.bot.user.avatar)
            embed.set_footer(text=f"Page {list(guild_webhooks.keys()).index(code) + 1}/{len(guild_webhooks)}",icon_url=self.bot.user.avatar)
            embeds.append(embed)

        view = WebhookPaginator(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @webhook.command(aliases=['del', 'remove'])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def delete(self, ctx, code: str):
        guild_webhooks = self.get_guild_webhooks(ctx.guild.id)
        if code in guild_webhooks:
            try:
                async with aiohttp.ClientSession() as session:
                    webhook = Webhook.from_url(guild_webhooks[code]["url"], session=session)
                    await webhook.delete(reason=f"Deleted by {ctx.author}")
                
                del self.webhooks[str(ctx.guild.id)][code]
                save_webhooks(self.webhooks)
                
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: deleted webhook with code `{code}`", color=config.hex))
            except discord.NotFound:
                await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this webhook appears to have been deleted already, removing this from database.", color=config.hex))
                del self.webhooks[str(ctx.guild.id)][code]
                save_webhooks(self.webhooks)
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: invalid webhook with code **`{code}`**", color=config.hex))

    @webhook.group(aliases=['e'])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def edit(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title=f"Webhook Edit",
                description=f"`webhook edit`, `webhook edit name`, `webhook edit avatar`\n{config.ques_emoji} Example: `webhook edit avatar <url>`",
                color=config.hex
            )
            await ctx.send(embed=embed)

    @edit.command(aliases=['n'])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def name(self, ctx, code: str, new_name: str):
        guild_webhooks = self.get_guild_webhooks(ctx.guild.id)
        if code not in guild_webhooks:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: invalid webhook with code `{code}`.", color=config.hex))

        try:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(guild_webhooks[code]["url"], session=session)
                await webhook.edit(name=new_name)
                
                self.webhooks[str(ctx.guild.id)][code]["name"] = new_name
                save_webhooks(self.webhooks)
                
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: updated webhook name to **{new_name}**.", color=config.hex))
        except discord.NotFound:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this webhook appears to have been deleted already, removing this from database.", color=config.hex))
            del self.webhooks[str(ctx.guild.id)][code]
            save_webhooks(self.webhooks)

    @edit.command(aliases=['av', 'pfp'])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def avatar(self, ctx, code: str, new_avatar: str = None):
        guild_webhooks = self.get_guild_webhooks(ctx.guild.id)
        if code not in guild_webhooks:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: invalid webhook with code `{code}`.", color=config.hex))

        avatar_bytes = None
        if ctx.message.attachments:
            async with aiohttp.ClientSession() as session:
                async with session.get(ctx.message.attachments[0].url) as response:
                    avatar_bytes = await response.read()
        elif new_avatar and new_avatar.startswith('https://'):
            async with aiohttp.ClientSession() as session:
                async with session.get(new_avatar) as response:
                    avatar_bytes = await response.read()

        if not avatar_bytes:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: please provide a valid image url or attachment", color=config.hex))

        try:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(guild_webhooks[code]["url"], session=session)
                await webhook.edit(avatar=avatar_bytes)
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: updated webhook avatar.", color=config.hex))
        except discord.NotFound:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this webhook appears to have been deleted already, removing this from database.", color=config.hex))
            del self.webhooks[str(ctx.guild.id)][code]
            save_webhooks(self.webhooks)

async def setup(bot):
    await bot.add_cog(WebhookManager(bot))