import discord
from discord.ext import commands
import math
from config import config

class DetailedCommandInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def get_command_embed(self, command):
        """Helper function to create an embed for a single command"""
        embed = discord.Embed(color=config.hex, description="```\n< > : Required Arguments\n[ ] : Optional Arguments```")
        embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar.url)
        
        embed.add_field(name="Command", value=f"{command}", inline=False)
        
        if command.help:
            embed.add_field(name="Help", value=f"{command.help}", inline=False)
        
        if command.aliases:
            embed.add_field(name="Aliases", value=f"`{'`, `'.join(command.aliases)}`", inline=False)
        
        if isinstance(command, commands.Group):
            subcommands = [subcmd.name for subcmd in command.commands]
            if subcommands:
                embed.add_field(name="Subcommands", value=f"`{'`, `'.join(subcommands)}`", inline=False)
        
        if command.signature:
            embed.add_field(name="Usage", value=f"`{command.qualified_name} {command.signature}`", inline=False)
            
        return embed

    class PaginationView(discord.ui.View):
        def __init__(self, commands_list, get_embed_func):
            super().__init__(timeout=60)
            self.commands = commands_list
            self.current_page = 0
            self.get_embed = get_embed_func
            self.total_pages = len(commands_list)
            
            self.update_buttons()
        
        def update_buttons(self):
            self.previous_button.disabled = self.current_page == 0
            self.next_button.disabled = self.current_page == self.total_pages - 1
            self.page_counter.label = f"Page {self.current_page + 1}/{self.total_pages}"
        
        @discord.ui.button(label="◀", style=discord.ButtonStyle.grey)
        async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = max(0, self.current_page - 1)
            self.update_buttons()
            
            embed = self.get_embed(self.commands[self.current_page])
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.grey, disabled=True)
        async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
            pass
        
        @discord.ui.button(label="▶", style=discord.ButtonStyle.grey)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = min(self.total_pages - 1, self.current_page + 1)
            self.update_buttons()
            
            embed = self.get_embed(self.commands[self.current_page])
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")
            
            await interaction.response.edit_message(embed=embed, view=self)

    @commands.command(name="detailedinfo", aliases=["dinfo"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def detailed_info(self, ctx):
        all_commands = sorted([cmd for cmd in self.bot.commands if not cmd.hidden], key=lambda x: x.name)
        
        if not all_commands:
            await ctx.send("No commands found!")
            return
            
        first_embed = self.get_command_embed(all_commands[0])
        first_embed.set_footer(text=f"Page 1/{len(all_commands)}")
        
        view = self.PaginationView(all_commands, self.get_command_embed)
        await ctx.send(embed=first_embed, view=view)

async def setup(bot):
    await bot.add_cog(DetailedCommandInfo(bot))