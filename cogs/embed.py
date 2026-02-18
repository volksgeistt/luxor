import discord
from discord.ext import commands
from discord import ui
import asyncio

class EmbedModal(ui.Modal):
    def __init__(self, field_type: str, *args, **kwargs):
        super().__init__(title=f"Set Embed {field_type}", *args, **kwargs)
        self.field_type = field_type
        
        if field_type == "Title":
            self.add_item(ui.TextInput(label="Title", style=discord.TextStyle.short,
                                     placeholder="Support for {guild.name}, etc."))
        elif field_type == "Description":
            self.add_item(ui.TextInput(label="Description", style=discord.TextStyle.paragraph,
                                     placeholder="Support for {guild.name}, etc."))
        elif field_type == "Footer":
            self.add_item(ui.TextInput(label="Footer Text", style=discord.TextStyle.short,
                                     placeholder="Support for  {guild.name}, etc."))
            self.add_item(ui.TextInput(label="Footer Icon URL (optional)", required=False, style=discord.TextStyle.short))
        elif field_type == "Author":
            self.add_item(ui.TextInput(label="Author Name", style=discord.TextStyle.short,
                                     placeholder="Support for  {guild.name}, etc."))
            self.add_item(ui.TextInput(label="Author URL (optional)", required=False, style=discord.TextStyle.short))
            self.add_item(ui.TextInput(label="Author Icon URL (optional)", required=False, style=discord.TextStyle.short))
        elif field_type in ["Thumbnail", "Image"]:
            self.add_item(ui.TextInput(label="Image URL", style=discord.TextStyle.short))
        elif field_type == "Channel":
            self.add_item(ui.TextInput(label="Channel ID", style=discord.TextStyle.short))
        elif field_type == "Color":
            self.add_item(ui.TextInput(
                label="Color (Hex)",
                placeholder="Enter hex color code (e.g., #FF0000)",
                style=discord.TextStyle.short
            ))

    async def on_submit(self, interaction: discord.Interaction):
        values = {}
        for child in self.children:
            values[child.label] = child.value
        await interaction.response.defer()
        self.stop()
        self.values = values

class EmbedCreatorButtons(ui.View):
    def __init__(self, bot, author_id: int):
        super().__init__(timeout=1200) 
        self.bot = bot
        self.author_id = author_id
        self.embed_data = {}
        self.preview_message = None
        self.editor_message = None

    async def format_variables(self, text: str, user: discord.Member) -> str:
        if not text:
            return text
            
        replacements = {
            "{guild.name}": user.guild.name,
            "{guild.count}": str(user.guild.member_count),
            "{guild.id}": str(user.guild.id),
            "{guild.created_at}": discord.utils.format_dt(user.guild.created_at, style="R"),
            "{guild.boost_count}": str(user.guild.premium_subscription_count),
            "{guild.boost_tier}": str(user.guild.premium_tier)
        }
        
        for key, value in replacements.items():
            if key in text:
                text = text.replace(key, value)
        
        return text

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("you can't use this interaction!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.editor_message:
            await self.editor_message.edit(view=self)

    async def update_preview(self, interaction: discord.Interaction):
        embed = discord.Embed()
        
        if "Color" in self.embed_data:
            try:
                color_hex = self.embed_data["Color"].strip('#')
                embed.color = discord.Color(int(color_hex, 16))
            except ValueError:
                await interaction.followup.send("Invalid color hex code! Using default color.", ephemeral=True)

        if "Title" in self.embed_data:
            embed.title = await self.format_variables(self.embed_data["Title"], interaction.user)
        if "Description" in self.embed_data:
            embed.description = await self.format_variables(self.embed_data["Description"], interaction.user)
        
        if "Footer" in self.embed_data:
            footer_text = await self.format_variables(self.embed_data["Footer"].get("Footer Text", ""), interaction.user)
            embed.set_footer(
                text=footer_text,
                icon_url=self.embed_data["Footer"].get("Footer Icon URL (optional)")
            )
        if "Author" in self.embed_data:
            author_name = await self.format_variables(self.embed_data["Author"].get("Author Name", ""), interaction.user)
            embed.set_author(
                name=author_name,
                url=self.embed_data["Author"].get("Author URL (optional)"),
                icon_url=self.embed_data["Author"].get("Author Icon URL (optional)")
            )
            
        if "Thumbnail" in self.embed_data:
            embed.set_thumbnail(url=self.embed_data["Thumbnail"].get("Image URL"))
        if "Image" in self.embed_data:
            embed.set_image(url=self.embed_data["Image"].get("Image URL"))

        if self.preview_message:
            await self.preview_message.edit(embed=embed)
        else:
            self.preview_message = await interaction.channel.send(embed=embed)

    @discord.ui.button(label="Reset All", style=discord.ButtonStyle.danger, row=4)
    async def reset_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed_data = {} 
        await interaction.response.send_message("All embed settings have been reset!", ephemeral=True)
        if self.preview_message:
            await self.preview_message.delete()
            self.preview_message = None
            embed = discord.Embed(description="*This is a new empty embed. Use the buttons above to customize it.*")
            self.preview_message = await interaction.channel.send(embed=embed)

    @discord.ui.button(label="Set Color", style=discord.ButtonStyle.primary)
    async def set_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Color")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.embed_data["Color"] = modal.values["Color (Hex)"]
        await self.update_preview(interaction)

    @discord.ui.button(label="Set Title", style=discord.ButtonStyle.primary)
    async def set_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Title")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.embed_data["Title"] = modal.values["Title"]
        await self.update_preview(interaction)

    @discord.ui.button(label="Set Description", style=discord.ButtonStyle.primary)
    async def set_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Description")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.embed_data["Description"] = modal.values["Description"]
        await self.update_preview(interaction)

    @discord.ui.button(label="Set Footer", style=discord.ButtonStyle.primary)
    async def set_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Footer")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.embed_data["Footer"] = modal.values
        await self.update_preview(interaction)

    @discord.ui.button(label="Set Author", style=discord.ButtonStyle.primary)
    async def set_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Author")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.embed_data["Author"] = modal.values
        await self.update_preview(interaction)

    @discord.ui.button(label="Set Thumbnail", style=discord.ButtonStyle.primary)
    async def set_thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Thumbnail")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.embed_data["Thumbnail"] = modal.values
        await self.update_preview(interaction)

    @discord.ui.button(label="Set Image", style=discord.ButtonStyle.primary)
    async def set_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Image")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.embed_data["Image"] = modal.values
        await self.update_preview(interaction)

    @discord.ui.button(label="Send Embed", style=discord.ButtonStyle.success)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal("Channel")
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        try:
            channel_id = int(modal.values["Channel ID"])
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await interaction.followup.send("Invalid channel ID!", ephemeral=True)
                return

            embed = discord.Embed()
            if "Color" in self.embed_data:
                try:
                    color_hex = self.embed_data["Color"].strip('#')
                    embed.color = discord.Color(int(color_hex, 16))
                except ValueError:
                    pass

            if "Title" in self.embed_data:
                embed.title = await self.format_variables(self.embed_data["Title"], interaction.user)
            if "Description" in self.embed_data:
                embed.description = await self.format_variables(self.embed_data["Description"], interaction.user)
            if "Footer" in self.embed_data:
                footer_text = await self.format_variables(self.embed_data["Footer"].get("Footer Text", ""), interaction.user)
                embed.set_footer(
                    text=footer_text,
                    icon_url=self.embed_data["Footer"].get("Footer Icon URL (optional)")
                )
            if "Author" in self.embed_data:
                author_name = await self.format_variables(self.embed_data["Author"].get("Author Name", ""), interaction.user)
                embed.set_author(
                    name=author_name,
                    url=self.embed_data["Author"].get("Author URL (optional)"),
                    icon_url=self.embed_data["Author"].get("Author Icon URL (optional)")
                )
            if "Thumbnail" in self.embed_data:
                embed.set_thumbnail(url=self.embed_data["Thumbnail"].get("Image URL"))
            if "Image" in self.embed_data:
                embed.set_image(url=self.embed_data["Image"].get("Image URL"))

            await channel.send(embed=embed)
            await interaction.followup.send("Embed sent successfully!", ephemeral=True)
            
            for child in self.children:
                child.disabled = True
            await self.editor_message.edit(view=self)
            
            self.stop()
            if self.preview_message:
                await asyncio.sleep(5)  
                await self.preview_message.delete()
        except ValueError:
            await interaction.followup.send("Invalid channel ID format!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

class EmbedCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="createembed",aliases=["embed", "embedcreate"],help="craete a custom embed mesasge in the guild.")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    async def create_embed(self, ctx):
        view = EmbedCreatorButtons(self.bot, ctx.author.id)
        help_embed = discord.Embed(
            description="""
### **Use the buttons below to create your custom embed.**

**Supported Variables:**
`{guild.name}` : gets guild name
`{guild.count}` : gets guild member count
`{guild.id}` : gets guild ID
`{guild.boost_count}` : gets guild boost count
`{guild.boost_tier}` : gets guild boost level
""",
            color=discord.Color.blurple()
        )
        editor_message = await ctx.send(embed=help_embed, view=view)
        view.editor_message = editor_message

    @create_embed.error
    async def create_embed_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.0f} seconds.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedCreator(bot))