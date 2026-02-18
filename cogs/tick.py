import discord
from discord.ext import commands
from discord import ButtonStyle, TextStyle
import asyncio
from typing import Dict, Optional
import json
import os
from config import config
class TicketManager:
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'db/tickets.json'
        self.load_config()
        self.bot.loop.create_task(self.load_persistent_views_background())

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
            self.save_config()
        except Exception:
            self.config = {}

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass

    def get_server_config(self, guild_id: int) -> dict:
        if str(guild_id) not in self.config:
            self.config[str(guild_id)] = {
                "category_id": None,
                "active_tickets": {},
                "staff_roles": [],
                "ticket_counter": 0,
                "panel_message_id": None,
                "panel_channel_id": None
            }
            self.save_config()
        return self.config[str(guild_id)]

    async def create_ticket(self, user: discord.Member, guild: discord.Guild, reason: str) -> tuple[bool, str | discord.TextChannel]:
        try:
            server_config = self.get_server_config(guild.id)
            
            if any(ticket['user_id'] == user.id for ticket in server_config['active_tickets'].values()):
                return False, "You already have an open ticket. Please close it before opening a new one."
            
            if server_config["category_id"]:
                category = guild.get_channel(server_config["category_id"])
            else:
                category = await guild.create_category("Tickets")
                server_config["category_id"] = category.id
                self.save_config()
            
            server_config["ticket_counter"] += 1
            channel_name = f"ticket-{server_config['ticket_counter']:04d}"
            channel = await category.create_text_channel(channel_name)
            
            await channel.set_permissions(user, read_messages=True, send_messages=True)
            await channel.set_permissions(guild.default_role, read_messages=False)
            
            for role_id in server_config["staff_roles"]:
                role = guild.get_role(role_id)
                if role:
                    await channel.set_permissions(role, read_messages=True, send_messages=True)
            
            server_config["active_tickets"][str(channel.id)] = {"user_id": user.id, "reason": reason}
            self.save_config()
            
            return True, channel
        except Exception:
            return False, "An error occurred while creating the ticket. Please try again later."

    async def close_ticket(self, channel_id: int, guild_id: int) -> bool:
        try:
            server_config = self.get_server_config(guild_id)
            if str(channel_id) in server_config["active_tickets"]:
                del server_config["active_tickets"][str(channel_id)]
                self.save_config()
                return True
            return False
        except Exception:
            return False

    async def load_persistent_views_background(self):
        await self.bot.wait_until_ready()
        for guild_id, config in self.config.items():
            if config["panel_message_id"] and config["panel_channel_id"]:
                channel = self.bot.get_channel(config["panel_channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(config["panel_message_id"])
                        self.bot.add_view(TicketView(self), message_id=config["panel_message_id"])
                    except discord.NotFound:
                        pass
                    except Exception:
                        pass

class TicketView(discord.ui.View):
    def __init__(self, ticket_manager: TicketManager):
        super().__init__(timeout=None)
        self.ticket_manager = ticket_manager
    
    @discord.ui.button(label="Create ticket", style=ButtonStyle.grey, emoji="📨", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            modal = TicketModal(self.ticket_manager)
            await interaction.response.send_modal(modal)
        except Exception:
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self, ticket_manager: TicketManager):
        super().__init__(timeout=None)
        self.ticket_manager = ticket_manager

    @discord.ui.button(label="Close Ticket", style=ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            success = await self.ticket_manager.close_ticket(interaction.channel.id, interaction.guild.id)
            if success:
                await interaction.channel.delete()
            else:
                await interaction.followup.send("Failed to close the ticket. Please try again.", ephemeral=True)
        except Exception:
            await interaction.followup.send("An error occurred while closing the ticket. Please try again later.", ephemeral=True)

class TicketModal(discord.ui.Modal):
    def __init__(self, ticket_manager: TicketManager):
        super().__init__(title="Create a Ticket")
        self.ticket_manager = ticket_manager
        self.reason = discord.ui.TextInput(label="Reason", style=TextStyle.paragraph, required=True, max_length=1000)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            success, result = await self.ticket_manager.create_ticket(interaction.user, interaction.guild, self.reason.value)
            if success:
                embed = discord.Embed(title="Ticket Created", description=f"Your ticket has been created: {result.mention}", color=discord.Color.green())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                ticket_embed = discord.Embed(title="New Ticket", description=f"Author : {interaction.user.mention}", color=discord.Color.blurple())
                ticket_embed.add_field(name="Reason", value=self.reason.value)
                await result.send(embed=ticket_embed, view=CloseTicketView(self.ticket_manager))
            else:
                embed = discord.Embed(title="Ticket Creation Failed", description=result, color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception:
            await interaction.response.send_message("An error occurred while creating the ticket. Please try again later.", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_manager = TicketManager(bot)

    @commands.group(name='ticket', aliases=['tickets'], invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def alr(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Ticket Subcommands", description=f"`ticket panel`, `ticket category`, `ticket stats`, `ticket staffadd`, `ticket staffremove`\n{config.ques_emoji} Example: `ticket panel <channel>`", color=config.hex))


    @alr.command(help="setup ticket panel")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)    
    async def panel(self, ctx, channel: discord.TextChannel = None):
        try:
            if channel is None:
                await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: please provide a channel id, where you want to send the ticket panel."))
                return
            server_config = self.ticket_manager.get_server_config(ctx.guild.id)
            
            if server_config["panel_message_id"] and server_config["panel_channel_id"]:
                try:
                    old_channel = self.bot.get_channel(server_config["panel_channel_id"])
                    if old_channel:
                        old_message = await old_channel.fetch_message(server_config["panel_message_id"])
                        await old_message.delete()
                except discord.NotFound:
                    pass
            
            embed = discord.Embed(
                description="Click the button below to create a ticket.\n",
                color=discord.Color.blurple()
            ) 
            embed.set_author(name="Ticket System", icon_url=self.bot.user.avatar)
            embed.set_footer(text=f"Powered by - {self.bot.user.name}",icon_url=self.bot.user.avatar)
            
            message = await channel.send(embed=embed, view=TicketView(self.ticket_manager))
            server_config["panel_message_id"] = message.id
            server_config["panel_channel_id"] = channel.id
            self.ticket_manager.save_config()
            
            if channel != ctx.channel:
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: created a ticket panel in {channel.mention}",color=config.hex))
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: I don't have permission to send messages in that channel.",color=config.hex))
        except Exception as e:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: An error occurred while creating the ticket panel: {str(e)}",color=config.hex))

    @alr.command(help="shows active tickets")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def stats(self, ctx):
        try:
            server_config = self.ticket_manager.get_server_config(ctx.guild.id)
            total_tickets = len(server_config["active_tickets"])
            embed = discord.Embed(color=discord.Color.blurple(),description=str(total_tickets))
            embed.set_author(name="Active Tickets", icon_url=self.bot.user.avatar)
            embed.set_footer(text=f"Powered by - {self.bot.user.name}",icon_url=self.bot.user.avatar)
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: An error occurred while fetching data.",color=config.hex))

    @alr.command(help="setup ticket panel creation catgeory")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def category(self, ctx, category: discord.CategoryChannel):
        try:
            server_config = self.ticket_manager.get_server_config(ctx.guild.id)
            server_config["category_id"] = category.id
            self.ticket_manager.save_config()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: ticket creation category has been set to **{category.name}**",color=config.hex))
        except Exception:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: sorry, an error occured while updating the ticket creation category.",color=config.hex))

    @alr.command(help="adds a staff role for ticket managements")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def staffadd(self, ctx, role: discord.Role):
        try:
            server_config = self.ticket_manager.get_server_config(ctx.guild.id)
            if role.id not in server_config["staff_roles"]:
                server_config["staff_roles"].append(role.id)
                self.ticket_manager.save_config()
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added {role.name} to staff role for ticket management.",color=config.hex))
            else:
                await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: noob! {role.name} is already set as ticket staff role.",color=config.hex))
        except Exception:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: An error occurred while adding the staff role. Please try again later.",color=config.hex))

    @alr.command(help="removes a staff role from ticket management")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def staffremove(self, ctx, role: discord.Role):
        try:
            server_config = self.ticket_manager.get_server_config(ctx.guild.id)
            if role.id in server_config["staff_roles"]:
                server_config["staff_roles"].remove(role.id)
                self.ticket_manager.save_config()
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed {role.name} removed from staff roles for ticket management.",color=config.hex))
            else:
                await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: noob! {role.name} is not a staff role.",color=config.hex))
        except Exception:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: An error occurred while removing the staff role. Please try again later.",color=config.hex))

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))