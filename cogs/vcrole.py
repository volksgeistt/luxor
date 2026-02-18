import discord
from discord.ext import commands
import json
from config import config

class VCRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_roles = {}
        self.load_vc_roles()

    def load_vc_roles(self):
        try:
            with open("db/vcrole.json", "r") as f:
                self.vc_roles = json.load(f)
        except FileNotFoundError:
            self.vc_roles = {}

    def save_vc_roles(self):
        with open("db/vcrole.json", "w") as f:
            json.dump(self.vc_roles, f)

    def check_role_permissions(self, role):
        perms = [
            'administrator', 'ban_members', 'kick_members', 'manage_channels',
            'manage_emojis', 'manage_guild', 'manage_messages', 'manage_nicknames',
            'manage_roles', 'manage_webhooks', 'mention_everyone', 'move_members'
        ]
        for permission in perms:
            if getattr(role.permissions, permission):
                return True
        return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = str(member.guild.id)
        if guild_id in self.vc_roles:
            role_id = self.vc_roles[guild_id]
            role = member.guild.get_role(role_id)
            if role:
                if not before.channel and after.channel:  
                    if role not in member.roles:
                        await member.add_roles(role)
                elif before.channel and not after.channel: 
                    if role in member.roles:
                        await member.remove_roles(role)

    @commands.group(name='vcrole', invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def vcrole(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"vc-role Subcommands:",description=f"`vcrole set`, `vcrole remove`, `vcrole config`\n{config.ques_emoji} Example: `vcrole set <role>`",color=config.hex))

    @vcrole.command(name='set',aliases=["setup","add"], help="setup role for vcrole module.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def vcrole_set(self, ctx, role: discord.Role):
        if not self.check_role_permissions(role):
            guild_id = str(ctx.guild.id)
            if guild_id not in self.vc_roles:
                self.vc_roles[guild_id] = role.id
                self.save_vc_roles()
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: vc role set to {role.mention}",color=config.hex))
            else:
                await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you can only have one vc role per guild.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: {role.name} got some dangerous perms in it, therefore you can't add it as vc role.",color=config.hex))

    @vcrole.command(name='remove',aliases=["clear","delete","del"], help="remove role from vcrole module.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def vcrole_remove(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.vc_roles:
            del self.vc_roles[guild_id]
            self.save_vc_roles()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: removed vc role system for your guild.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: your guild doesn't have any vc role setup.",color=config.hex))

    @vcrole.command(name='config',aliases=["show","list"], help="list all the users that are blacklisted from joining vc.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def vcrole_config(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.vc_roles:
            role_id = self.vc_roles[guild_id]
            role = ctx.guild.get_role(role_id)
            if role:
                await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: {role.mention} is setup as vc role in this guild.",color=config.hex))
            else:
                await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: the vc role doesn't exists in the guild.",color=config.hex))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.ques_emoji} {ctx.author.mention}: no vc role is set in this guild.",color=config.hex))

async def setup(bot):
    await bot.add_cog(VCRole(bot))