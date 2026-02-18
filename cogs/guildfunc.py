import discord
from discord.ext import commands
import datetime
from config import config

class ComprehensiveLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1295632987769274419
        self.log_webhook = discord.SyncWebhook.from_url("https://discord.com/api/webhooks/1317131245175443489/Hlqzf7gL0cqbL8MUEPd0LImKn68TOVEJMhbTOgacTO9DPKujXwite6XxBxNfSYqM7S4v")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="📥 JOINED A NEW GUILD", color=config.hex)
        embed.add_field(name="Name", value=guild.name, inline=False)
        embed.add_field(name="ID", value=str(guild.id), inline=False)
        embed.add_field(name="Owner", value=f"{guild.owner.name} {guild.owner.id}", inline=False)
        embed.add_field(name="Member Count", value=f"{guild.member_count} Members", inline=False)
        embed.add_field(name="Creation Date", value=guild.created_at.strftime("%d %b %Y"), inline=False)
        
        inviter = "Unknown"
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=1):
                inviter = f"{entry.user.name} ({entry.user.id})"
                break
        except discord.errors.Forbidden:
            inviter = "Couldn't check audit logs (no permissions)"
        embed.add_field(name="Invited by", value=inviter, inline=False)
        
        try:
            first_channel = next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).create_instant_invite), None)
            if first_channel:
                invite = await first_channel.create_invite(max_age=0, max_uses=0)
                invite_url = invite.url
            else:
                invite_url = "Couldn't create invite (no suitable channel)"
        except discord.errors.Forbidden:
            invite_url = "Couldn't create invite (no permissions)"
        
        embed.add_field(name="Guild Invite", value=invite_url, inline=False)
        embed.add_field(name="Server Count", value=f"{len(self.bot.guilds)} Servers", inline=False)
        embed.set_footer(text=datetime.datetime.now().strftime("%m/%d/%Y %I:%M %p"))
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(title="📤 LEFT A GUILD", color=config.hex)
        embed.add_field(name="Name", value=guild.name, inline=False)
        embed.add_field(name="ID", value=str(guild.id), inline=False)
        embed.add_field(name="Member Count", value=f"{guild.member_count} Members", inline=False)
        embed.add_field(name="Creation Date", value=guild.created_at.strftime("%d %b %Y"), inline=False)
        embed.add_field(name="Server Count", value=f"{len(self.bot.guilds)} Servers", inline=False)
        embed.set_footer(text=datetime.datetime.now().strftime("%m/%d/%Y %I:%M %p"))
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_command_completion(self, context: discord.ext.commands.Context) -> None:
        full_command_identifier = context.command.qualified_name
        command_parts = full_command_identifier.split("\n")
        executed_command_name = str(command_parts[0])
        if not context.message.content.startswith(","):
            command_display = f"`,{context.message.content}`"
        else:
            command_display = f"`{context.message.content}`"

        try:
            if context.guild is not None:
                command_embed = discord.Embed(color=config.hex)
                command_embed.set_author(
                    name=f"Executor : {context.author}",
                    icon_url=str(context.author.avatar)
                )
                command_embed.set_thumbnail(url=str(context.author.avatar))
                
                command_embed.add_field(
                    name="Command Details:",
                    value=f"> **Name:** {executed_command_name}\n"
                          f"> **Content:** {command_display}",
                    inline=False
                )
                
                command_embed.add_field(
                    name="Execution Context:",
                    value=f"> **User:** {context.author} | ID: [{context.author.id}](https://discord.com/users/{context.author.id})\n"
                          f"> **Server:** {context.guild.name} | ID: [{context.guild.id}](https://discord.com/users/{context.author.id})\n"
                          f"> **Channel:** #{context.channel.name} | ID: [{context.channel.id}](https://discord.com/channel/{context.channel.id})",
                    inline=False
                )
                
                command_embed.set_footer(
                    text=f" {self.bot.user.name}",
                    icon_url=str(self.bot.user.display_avatar.url)
                )
                
                self.log_webhook.send(embed=command_embed)
            
            else:
                dm_embed = discord.Embed(color=config.hex)
                dm_embed.set_author(
                    name=f"Executor : {context.author}",
                    icon_url=str(context.author.avatar)
                )
                dm_embed.set_thumbnail(url=str(context.author.avatar))
                
                dm_embed.add_field(
                    name="Command Details:",
                    value=f"> **Name:** {executed_command_name}",
                    inline=False
                )
                
                dm_embed.add_field(
                    name="Execution Context:",
                    value=f"> **User:** {context.author} | ID: [{context.author.id}](https://discord.com/users/{context.author.id})",
                    inline=False
                )
                
                dm_embed.set_footer(
                    text=f"{self.bot.user.name}",
                    icon_url=str(self.bot.user.display_avatar.url)
                )
                self.log_webhook.send(embed=dm_embed)
        except Exception as error:
            print(f"Logging error: {error}")

    async def send_log(self, embed):
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print("[ LOG ] : GUILD JOIN / REMOVE LOG CHANNEL NOT FOUND.")

async def setup(bot):
    await bot.add_cog(ComprehensiveLogging(bot))