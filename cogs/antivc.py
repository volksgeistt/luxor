import discord
from discord.ext import commands
import json
from config import config
import math

class AntiVC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_banned = {}
        self.load_vc_banned()

    def load_vc_banned(self):
        try:
            with open("db/antivc.json", "r") as f:
                self.vc_banned = json.load(f)
        except FileNotFoundError:
            self.vc_banned = {}

    def save_vc_banned(self):
        with open("db/antivc.json", "w") as f:
            json.dump(self.vc_banned, f)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = str(member.guild.id)
        if after.channel and member.id in self.vc_banned.get(guild_id, []):
            await member.move_to(None)
            await member.send(f"{config.cross} {member.mention} you are not allowed to join voice channels in **{member.guild.name}**. (blacklisted by admin/owner)")

    @commands.group(name='antivc', aliases=['vcban'], invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def uwu(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"AntiVC Subcommands", description=f"`antivc add`, `antivc remove`, `antivc config`\n{config.ques_emoji} Example: `antivc add <user>`", color=config.hex))

    @uwu.command(name='add', help="blacklist user from joining vc in guild.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def vcban_add(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.vc_banned:
            self.vc_banned[guild_id] = []
        member_id = member.id
        if member_id not in self.vc_banned[guild_id]:
            self.vc_banned[guild_id].append(member_id)
            self.save_vc_banned()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added {member.mention} to anti-vc database.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: lol {member.mention} is already in anti-vc database.", color=config.hex))

    @uwu.command(name='remove', help="removes blacklist of user from joining vc.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def vcban_remove(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        member_id = int(member.id)
        if guild_id in self.vc_banned and member_id in self.vc_banned[guild_id]:
            self.vc_banned[guild_id].remove(member_id)
            self.save_vc_banned()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed {member.mention} from anti-vc database.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: lol {member.mention} is not added to anti-vc database.", color=config.hex))

    @uwu.command(name='clear', aliases=["reset"],help="removes all members from the anti-vc database for this guild.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def vcban_clear(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.vc_banned:
            count = len(self.vc_banned[guild_id])
            del self.vc_banned[guild_id]
            self.save_vc_banned()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: cleared all {count} restricted members from the anti-vc database for this guild.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: there are no restricted members in the anti-vc database for this guild.", color=config.hex))


    @uwu.command(name='config', help="shows list of vc blacklisted users.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def vcban_config(self, ctx):
        guild_id = str(ctx.guild.id)
        banned_members = []
        if guild_id in self.vc_banned:
            for member_id in self.vc_banned[guild_id]:
                member = ctx.guild.get_member(member_id)
                if member:
                    banned_members.append(f"[{member.name}](https://discord.com/users/{member.id}) ({member.id})")

        if not banned_members:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: no member found in anti-vc database.", color=config.hex))
            return

        pages = []
        items_per_page = 10
        total_pages = math.ceil(len(banned_members) / items_per_page)

        for i in range(0, len(banned_members), items_per_page):
            page = banned_members[i:i+items_per_page]
            embed = discord.Embed(color=config.hex)
            embed.description = "\n".join(page)
            embed.set_author(name=f"{ctx.guild.name}'s vc restricted users:", icon_url=self.bot.user.avatar)
            embed.set_footer(text=f"Page {i//items_per_page + 1}/{total_pages}")
            pages.append(embed)

        class PaginatorView(discord.ui.View):
            def __init__(self, ctx, *, timeout=600):
                super().__init__(timeout=timeout)
                self.ctx = ctx
                self.current_page = 0

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message(f"{config.cross} : you can't use this interaction menu.", ephemeral=True)
                    return False
                return True

            @discord.ui.button(emoji="<:prev:1229446062335328306>", style=discord.ButtonStyle.grey)
            async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.current_page > 0:
                    self.current_page -= 1
                    await interaction.response.edit_message(embed=pages[self.current_page])
                else:
                    await interaction.response.defer()

            @discord.ui.button(label="🗑️", style=discord.ButtonStyle.red)
            async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.message.delete()

            @discord.ui.button(emoji="<:next:1229446448777527327>", style=discord.ButtonStyle.grey)
            async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.current_page < len(pages) - 1:
                    self.current_page += 1
                    await interaction.response.edit_message(embed=pages[self.current_page])
                else:
                    await interaction.response.defer()

        view = PaginatorView(ctx)
        await ctx.send(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(AntiVC(bot))