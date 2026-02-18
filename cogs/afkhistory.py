
import discord
from discord.ext import commands
from datetime import datetime
import json
import os

class AFKHistoryView(discord.ui.View):
    def __init__(self, afk_history, user):
        super().__init__(timeout=120)
        self.afk_history = afk_history
        self.user = user
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        embed = self.get_current_embed()
        self.update_button_states()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_current_embed(self):
        entry = self.afk_history[self.current_page]
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="AFK Message", value=entry['reason'], inline=False)
        embed.add_field(name="Timestamp", value=f"<t:{int(datetime.fromisoformat(entry['start_time']).timestamp())}:F>", inline=False)
        embed.add_field(name="Guild", value=entry['guild_name'], inline=False)
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.afk_history)}",icon_url=self.user.avatar)
        embed.set_author(name=f"AFK History @ {self.user.name}",icon_url=self.user.avatar)
        return embed

    def update_button_states(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.afk_history) - 1

class AFKHistoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_history_file = 'db/afkHistory.json'
        self.afk_history = self.load_afk_history()

    def load_afk_history(self):
        if os.path.exists(self.afk_history_file):
            with open(self.afk_history_file, 'r') as f:
                return json.load(f)
        return {}

    def save_afk_history(self):
        with open(self.afk_history_file, 'w') as f:
            json.dump(self.afk_history, f, indent=4)

    def add_afk_entry(self, user_id, reason, start_time, guild_name):
        if user_id not in self.afk_history:
            self.afk_history[user_id] = []
        
        new_entry = {
            'reason': reason,
            'start_time': start_time,
            'guild_name': guild_name
        }
        
        self.afk_history[user_id].insert(0, new_entry)
        
        self.afk_history[user_id] = self.afk_history[user_id][:10]
        
        self.save_afk_history()

    @commands.command(name="afkhistory", help="View your AFK history")
    @commands.cooldown(1, 15, commands.BucketType.user)
    @commands.guild_only()
    async def afk_history(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.afk_history or not self.afk_history[user_id]:
            await ctx.send("You don't have any AFK history.")
            return

        view = AFKHistoryView(self.afk_history[user_id], ctx.author)
        embed = view.get_current_embed()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(AFKHistoryCog(bot))