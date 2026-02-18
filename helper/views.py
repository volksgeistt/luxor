import discord
from config import config

def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed

class ConfirmPrompt(discord.ui.View):
  def __init__(self, ctx):
    super().__init__()
    self.value = None
    self.user_id = ctx.author.id
    
  @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
  async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
    if self.user_id == interaction.user.id:
        self.value = True
        self.stop()
    else:
        await interaction.response.send_message(embed=create_embed("You cannot control this button because you did not execute it."), ephemeral=True)
  @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
  async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
    if self.user_id != interaction.user.id:
        await interaction.response.send_message(embed=create_embed("You cannot control this button because you did not execute it."), ephemeral=True)
    else:
        self.value = False
        self.stop()
