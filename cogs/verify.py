import discord
from discord.ext import commands
import json
import random
import string
import os
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
from config import config

class CaptchaModal(discord.ui.Modal):
    def __init__(self, captcha, verification_cog):
        super().__init__(title="CAPTCHA Verification")
        self.captcha = captcha
        self.verification_cog = verification_cog
        self.captcha_input = discord.ui.TextInput(
            label="Enter the CAPTCHA",
            placeholder="Enter the code from the image.",
            required=True,
            max_length=7
        )
        self.add_item(self.captcha_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        verifications = self.verification_cog.load_data(self.verification_cog.verifications_file)
        
        if user_id not in verifications:
            await interaction.response.send_message(f"{config.cross}: your verification session has expired, try again!", ephemeral=True)
            return

        verification = verifications[user_id]
        guild_id = verification["guild_id"]
        guild_settings = self.verification_cog.load_data(self.verification_cog.settings_file)
        settings = guild_settings[guild_id]

        if self.captcha_input.value.upper() == self.captcha:
            del verifications[user_id]
            self.verification_cog.save_data(self.verification_cog.verifications_file, verifications)

            guild = interaction.client.get_guild(int(guild_id))
            member = guild.get_member(int(user_id))
            verified_role = guild.get_role(settings['verified_role_id'])
            await member.add_roles(verified_role)

            await interaction.response.send_message(f"{config.tick}: you have been successfully verified.", ephemeral=True)
        else:
            verification["attempts"] += 1
            if verification["attempts"] >= settings['max_attempts']:
                del verifications[user_id]
                await interaction.response.send_message(f"{config.cross}: you have exceeded the maximum number of attempts. Please use the verification button again.", ephemeral=True)
            else:
                verifications[user_id] = verification
                await interaction.response.send_message(f'{config.error_emoji}: incorrect CAPTCHA. You have {settings["max_attempts"] - verification["attempts"]} attempts remaining.', ephemeral=True)
            
            self.verification_cog.save_data(self.verification_cog.verifications_file, verifications)

class VerifyButton(discord.ui.View):
    def __init__(self, verification_cog):
        super().__init__(timeout=None)
        self.verification_cog = verification_cog

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, custom_id="flawverify")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        captcha = self.verification_cog.generate_captcha()
        captcha_image = self.verification_cog.generate_captcha_image(captcha)
        
        user_id = str(interaction.user.id)
        verifications = self.verification_cog.load_data(self.verification_cog.verifications_file)
        verifications[user_id] = {"guild_id": str(interaction.guild.id), "captcha": captcha, "attempts": 0}
        self.verification_cog.save_data(self.verification_cog.verifications_file, verifications)

        embed = discord.Embed(title="CAPTCHA Verification", description="Please enter the CAPTCHA shown in the image below.",color=config.hex)
        embed.set_image(url="attachment://captcha.png")
        embed.set_footer(text=f"This menu will expire after 10 minutes.")
        view = CaptchaView(self.verification_cog, captcha)
        
        await interaction.response.send_message(embed=embed, file=captcha_image, view=view, ephemeral=True)

class CaptchaView(discord.ui.View):
    def __init__(self, verification_cog, captcha):
        super().__init__()
        self.verification_cog = verification_cog
        self.captcha = captcha

    @discord.ui.button(label="Enter CAPTCHA", style=discord.ButtonStyle.primary)
    async def enter_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CaptchaModal(self.captcha, self.verification_cog))

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(VerifyButton(self))
        self.settings_file = 'db/guild_settings.json'
        self.verifications_file = 'db/verifications.json'
        self.default_timeout = 600
        self.font = ImageFont.truetype("Arial.ttf", 60)

    def load_data(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    def save_data(self, filename, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def generate_captcha(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    def generate_captcha_image(self, text):
        image = Image.new('RGB', (300, 100), color = (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.text((10,10), text, font=self.font, fill=(0, 0, 0))
        for _ in range(1000):
            draw.point((random.randint(0, 300), random.randint(0, 100)), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        for _ in range(5):
            draw.line([(random.randint(0, 300), random.randint(0, 100)) for _ in range(2)], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=2)
        image_binary = io.BytesIO()
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        return discord.File(fp=image_binary, filename='captcha.png')

    @commands.group(name="verification", aliases=["captcha","verify"],invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def verification(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Verification Subcommands",description=f">>> `verification setup`, `verification attempt`, `verification role`, `verification reset`, `verification config`\n{config.ques_emoji} Example: `verification role <role id/mention>`",color=config.hex))


    @verification.command(help="setup verification system")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, role: discord.Role, channel: discord.TextChannel, max_attempts: int):
        guild_settings = self.load_data(self.settings_file)
        guild_settings[str(ctx.guild.id)] = {
            'verified_role_id': role.id,
            'verification_channel_id': channel.id,
            'max_attempts': max_attempts,
            'captcha_timeout': self.default_timeout,
        }
        self.save_data(self.settings_file, guild_settings)
        
        embed = discord.Embed(description="**Click on the button below to start verification.**",color=config.hex)
        embed.set_footer(icon_url=self.bot.user.avatar.url,text=f"{self.bot.user.name} - Verification Made Easy")
        embed.set_author(name=f"Verification",icon_url=self.bot.user.avatar.url,url=config.url)
        embed.set_image(url="https://cdn.discordapp.com/banners/1295610731202609203/f2525f83ec2c3cf8c9faee968fa12a46.png?size=512")
        await channel.send(embed=embed, view=VerifyButton(self))

        embedx=discord.Embed(description=f"{config.tick} {ctx.author.mention}: verification setup completed and panel has been sent to the channel.",color=config.hex)
        await ctx.send(embed=embedx)

    @verification.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def reycqtn9b8432b6t34tymh4739t64c3ty2y5v0c4um899vpn38yt24q59ypntv1837452set(self, ctx, member: discord.Member):
        verifications = self.load_data(self.verifications_file)
        user_id = str(member.id)
        
        if user_id in verifications:
            del verifications[user_id]
            self.save_data(self.verifications_file, verifications)
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: cleared verification data for {member.mention}.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: no active verification found for {member.mention}.",color=config.hex))

    @verification.command(help="shows verification config")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        guild_settings = self.load_data(self.settings_file)
        guild_id = str(ctx.guild.id)
        
        if guild_id not in guild_settings:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: verification module is not setup in this guild yet.",color=config.hex))
            return
        settings = guild_settings[guild_id]
        embed = discord.Embed(title="Verification Configuration", color=config.hex)
        embed.add_field(name="Verified Role", value=f"<@&{settings['verified_role_id']}>", inline=False)
        embed.add_field(name="Verification Channel", value=f"<#{settings['verification_channel_id']}>", inline=False)
        embed.add_field(name="Max Attempts", value=settings['max_attempts'], inline=False)
        embed.add_field(name="Captcha Timeout", value=f"{settings['captcha_timeout']}s", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} Verification Module",icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed)

    @verification.command(help="setup total amount of verification attempts")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def attempt(self, ctx, new_max_attempts: int):
        guild_settings = self.load_data(self.settings_file)
        guild_id = str(ctx.guild.id)
        
        if guild_id not in guild_settings:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: verification module is not setup in this guild yet.",color=config.hex))
            return
        
        guild_settings[guild_id]['max_attempts'] = new_max_attempts
        self.save_data(self.settings_file, guild_settings)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: updated max verification attempt limit to **{new_max_attempts}**",color=config.hex))

    @verification.command(help="setup verification role")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, role: discord.Role):
        guild_settings = self.load_data(self.settings_file)
        guild_id = str(ctx.guild.id)
        
        if guild_id not in guild_settings:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: verification module is not setup in this guild yet.",color=config.hex))
            return
        
        guild_settings[guild_id]['verified_role_id'] = role.id
        self.save_data(self.settings_file, guild_settings)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: updated verified users role to {role.mention}",color=config.hex))

    @verification.command(help="reset whole server verification data")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx):
        guild_id = str(ctx.guild.id)
        
        guild_settings = self.load_data(self.settings_file)
        if guild_id in guild_settings:
            del guild_settings[guild_id]
            self.save_data(self.settings_file, guild_settings)
        
        # Reset verifications for all members in this guild
        verifications = self.load_data(self.verifications_file)
        verifications = {user_id: data for user_id, data in verifications.items() if data["guild_id"] != guild_id}
        self.save_data(self.verifications_file, verifications)
        await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: cleared all verification data for this guild.",color=config.hex))

async def setup(bot):
    await bot.add_cog(Verification(bot))