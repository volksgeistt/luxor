import discord
from discord.ext import commands
import json
import os
from config import config

class JoinDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "db/JoinDM.json"
        self.db = self.load_db()
        self.color = config.hex

    def load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                return json.load(f)
        else:
            return {}

    def save_db(self):
        with open(self.db_path, "w") as f:
            json.dump(self.db, f, indent=4)

    def guild(self, user, params):
        if "{user}" in params:
            params = params.replace("{user}", str(user))
        if "{user.mention}" in params:
            params = params.replace("{user.mention}", str(user.mention))
        if "{user.name}" in params:
            params = params.replace("{user.name}", str(user.name))
        if "{user.discriminator}" in params:
            params = params.replace("{user.discriminator}", str(user.discriminator))
        if "{guild.name}" in params:
            params = params.replace("{guild.name}", str(user.guild.name))
        if "{guild.id}" in params:
            params = params.replace("{guild.id}", str(user.guild.id))
        if "{guild.count}" in params:
            params = params.replace("{guild.count}", str(user.guild.member_count))
        return params

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        if guild_id in self.db and self.db[guild_id]["message"]:
            message = self.guild(member, self.db[guild_id]["message"])
            use_embed = self.db[guild_id].get("use_embed", False)
            try:
                view = discord.ui.View()
                button = discord.ui.Button(label=f"from ~ {member.guild.name}", disabled=True)
                view.add_item(button)
                
                if use_embed:
                    embed = discord.Embed(description=message, color=self.color)
                    await member.send(embed=embed, view=view)
                else:
                    await member.send(content=message, view=view)
            except discord.HTTPException:
                pass

    @commands.group(name="joindm", aliases=["join-dm","jd","joinmsg","join-message","jm"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joindm(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"JoinDM Subcommands", description=f">>> `joindm message`, `joindm variables`, `joindm config`, `joindm reset`, `joindm test`, `joindm embed`\n{config.ques_emoji} Example: `joindm message <message>`", color=self.color))

    @joindm.command(name="message", aliases=["set", "add", "msg", "enable"], help="setup join-dm message")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def joindm_message(self, ctx, *, message: str):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.db:
            self.db[guild_id] = {"message": "", "variables": {}, "use_embed": False}
        self.db[guild_id]["message"] = message
        self.save_db()
        embed = discord.Embed(color=self.color, description=f"> {config.tick} {ctx.author.mention}: JoinDM message has been saved and updated.")
        embed.add_field(name=f"{config.ques_emoji} JoinDM message", value=f"```{message}```")
        await ctx.send(embed=embed)

    @joindm.command(name="embed", help="toggle between embed and normal text message.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def joindm_toggle_embed(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.db:
            self.db[guild_id] = {"message": "", "variables": {}, "use_embed": False}
        
        self.db[guild_id]["use_embed"] = not self.db[guild_id].get("use_embed", False)
        self.save_db()
        
        status = "enabled" if self.db[guild_id]["use_embed"] else "disabled"
        embed = discord.Embed(color=self.color, description=f"> {config.tick} {ctx.author.mention}: embed has been {status} for JoinDM messages.")
        await ctx.send(embed=embed)

    @joindm.command(name="config", aliases=["setting"], help="shows the configured guild join-dm message")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def joindm_config(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.db or not self.db[guild_id]["message"]:
            embed = discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: JoinDM is not setup in this guild.", color=self.color)
            await ctx.send(embed=embed)
        else:
            message = self.db[guild_id]["message"]
            use_embed = self.db[guild_id].get("use_embed", False)
            embed = discord.Embed(description=f"**JoinDM message:**\n```{message}```", color=self.color)
            embed.add_field(name="JoinDM embed", value="Enabled" if use_embed else "Disabled")
            await ctx.send(embed=embed)

    @joindm.command(name="variables", aliases=["vars","var"], help="shows the join-dm message variables to setup")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joindm_variables(self, ctx):
        embed = discord.Embed(color=self.color, description="""```
{user}               : name#discrim of the user
{user.mention}       : @mention of the user
{user.name}          : name of the user
{user.discriminator} : discriminator of the user
{guild.name}         : name of the guild
{guild.count}        : member count of the guild
{guild.id}           : id of the guild
```""")
        embed.set_author(name="JoinDM Variables", icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed)

    @joindm.command(name="reset", aliases=["delete","clear", "disable"], help="clears the join-dm config")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def joindm_reset(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.db:
            del self.db[guild_id]
            self.save_db()
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: JoinDM config has been cleared for this guild.", color=self.color))
        else:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: JoinDM is not setup for this guild.", color=self.color))

    @joindm.command(name="test", help="test the join-dm message setup.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def joindm_test(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.db or not self.db[guild_id]["message"]:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: JoinDM is not setup for this guild.", color=self.color))
        else:
            message = self.guild(ctx.author, self.db[guild_id]["message"])
            use_embed = self.db[guild_id].get("use_embed", False)
            view = discord.ui.View()
            button = discord.ui.Button(label=f"From {ctx.guild.name}", disabled=True)
            view.add_item(button)
            
            if use_embed:
                embed = discord.Embed(description=message, color=self.color)
                await ctx.author.send(embed=embed, view=view)
            else:
                await ctx.author.send(content=message, view=view)
            
            await ctx.send(embed=discord.Embed(description=f"{config.tick} {ctx.author.mention}: JoinDM test message sent to your DMs.", color=self.color))

async def setup(bot):
    await bot.add_cog(JoinDM(bot))