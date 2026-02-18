import discord
from discord.ext import commands
import json
import os
from config import config
import math

class AutoBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_data()

    def load_data(self):
        if os.path.exists('db/autoban.json'):
            with open('db/autoban.json', 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def save_data(self):
        with open('db/autoban.json', 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_guild_data(self, guild_id):
        if str(guild_id) not in self.data:
            self.data[str(guild_id)] = {'banned_users': []}
        return self.data[str(guild_id)]

    def is_guild_owner():
        async def predicate(ctx):
            if ctx.author == ctx.guild.owner:
                return True
            else:
                await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: You must be the guild owner to use this command.", color=config.hex))
                return False
        return commands.check(predicate)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_data = self.get_guild_data(member.guild.id)
        for user_data in guild_data['banned_users']:
            if member.id == user_data['user_id']:
                await member.ban(reason=f'{self.bot.user.name} @ auto-ban : user blacklisted from joining this guild by the GuildOwner.')
                return

    @commands.group(name="autoban", invoke_without_command=True)
    @is_guild_owner()
    async def autoban(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Autoban Subcommand:", description=f"`autoban add`, `autoban remove`, `autoban config`\n{config.ques_emoji} Example: `autoban add <user>`", color=config.hex))

    @autoban.command(help="automatically bans a blacklisted user from rejoining guild")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @is_guild_owner()
    async def add(self, ctx, user: discord.User):
        guild_data = self.get_guild_data(ctx.guild.id)
        user_data = {'user_id': user.id, 'username': user.name}
        if user_data not in guild_data['banned_users']:
            guild_data['banned_users'].append(user_data)
            self.save_data()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: added **{user.name}** to auto-ban database for this guild, they won't be able to rejoin this guild now.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: **{user.name}** is already blacklisted from joining.", color=config.hex))

    @autoban.command(help="removes autoban blacklist of a user ")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @is_guild_owner()
    async def remove(self, ctx, user: discord.User):
        guild_data = self.get_guild_data(ctx.guild.id)
        user_data = {'user_id': user.id, 'username': user.name}
        if user_data in guild_data['banned_users']:
            guild_data['banned_users'].remove(user_data)
            self.save_data()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed **{user.name}** from guild auto-ban database.", color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: **{user.name}** is not in guild auto-ban database.", color=config.hex))

    @autoban.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @is_guild_owner()
    async def config(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        banned_users = guild_data['banned_users']
        if not banned_users:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: there are no users in auto-ban database for this guild.", color=config.hex))
            return

        pages = []
        items_per_page = 10
        total_pages = math.ceil(len(banned_users) / items_per_page)

        for i in range(0, len(banned_users), items_per_page):
            page = banned_users[i:i+items_per_page]
            embed = discord.Embed(color=config.hex)
            banned_user_mentions = [f"[{user_data['username']}](https://discord.com/users/{user_data['user_id']}) ({user_data['user_id']})" for user_data in page]
            embed.description = "\n".join(banned_user_mentions)
            embed.set_author(icon_url=self.bot.user.avatar, name=f"{ctx.guild.name}'s auto-ban")
            embed.set_footer(text=f"Page {i//items_per_page + 1}/{total_pages}")
            pages.append(embed)

        class PaginatorView(discord.ui.View):
            def __init__(self, *, timeout=180):
                super().__init__(timeout=timeout)
                self.current_page = 0

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

        view = PaginatorView()
        await ctx.send(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(AutoBan(bot))