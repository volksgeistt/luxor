import discord
from discord.ext import commands
from discord import SelectOption
from discord.ui import Select, View
import json
import datetime
from typing import Optional
from pathlib import Path
from enum import Enum
from config import config
class Badges(Enum):
    Developer = ("<:stolen_emoji:1298282242904297535>", 1)
    Owner = ("<:stolen_emoji:1298282340736565300>", 2)
    Supporters = ("<:stolen_emoji:1298282402338045964>", 3)
    Premium = ("<:stolen_emoji:1298283531486887937>", 4)
    Friends = ("<:stolen_emoji:1298283612612984883>", 5)
    Specials = ("<:stolen_emoji:1298283802577342566>", 6)
    Verified = ("<:stolen_emoji:1298291391138496594>", 7)
    Boosters = ("<a:stolen_emoji:1298283892318535701>", 8)
    VIP = ("<:stolen_emoji:1298284135894351893>", 9)
    Partners = ("<:stolen_emoji:1298283966280761408>", 10)
    Users = ("<a:stolen_emoji:1298284224100438098>", 11)
    Clowns = ("<:stolen_emoji:1301546551533113404>", 12)

class BadgeSelect(Select):
    def __init__(self, profile_manager, member):
        self.profile_manager = profile_manager
        self.member = member
        
        user_profile = profile_manager.get_user_profile(member.id)
        current_badges = user_profile["badges"]
        
        options = [
            SelectOption(
                label=badge.name,
                value=badge.name,
                emoji=badge.value[0],
            )
            for badge in Badges
            if badge.name not in current_badges and badge.name != "Users"
        ]
        
        super().__init__(
            placeholder="Select badges to add...",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        added_badges = []
        for badge_name in self.values:
            if self.profile_manager.add_badge(self.member.id, badge_name):
                added_badges.append(f"{Badges[badge_name].value[0]} {badge_name}")
        
        if added_badges:
            embed = discord.Embed(
                title="Badges Added!",
                description=f"Added the following badges to {self.member.mention}:\n" + "\n".join(added_badges),
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="No Changes",
                description="No new badges were added.",
                color=discord.Color.yellow()
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BadgeSelectView(View):
    def __init__(self, profile_manager, member):
        super().__init__()
        self.add_item(BadgeSelect(profile_manager, member))

class ProfileManager:
    def __init__(self, data_path: str = "./db"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(exist_ok=True)
        self.profiles_file = self.data_path / "profiles.json"
        self.cache = self._load_data()

    def _load_data(self) -> dict:
        if self.profiles_file.exists():
            with open(self.profiles_file, 'r') as f:
                return json.load(f)
        return {"users": {}}

    def _save_data(self):
        with open(self.profiles_file, 'w') as f:
            json.dump(self.cache, f, indent=4)

    def get_user_profile(self, user_id: int) -> dict:
        user_id = str(user_id)
        if user_id not in self.cache["users"]:
            self.cache["users"][user_id] = {
                "badges": ["Users"],
                "commands_used": 0,
                "join_date": str(datetime.datetime.utcnow())
            }
            self._save_data()
        return self.cache["users"][user_id]

    def add_badge(self, user_id: int, badge: str) -> bool:
        user_id = str(user_id)
        profile = self.get_user_profile(user_id)
        if badge not in profile["badges"]:
            profile["badges"].append(badge)
            self._save_data()
            return True
        return False

    def remove_badge(self, user_id: int, badge: str) -> bool:
        user_id = str(user_id)
        profile = self.get_user_profile(user_id)
        if badge in profile["badges"] and badge != "Users":
            profile["badges"].remove(badge)
            self._save_data()
            return True
        return False

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.profile_manager = ProfileManager()
        self.color = discord.Color.blue()

    def format_badges(self, badges: list) -> str:
        sorted_badges = sorted(
            badges,
            key=lambda x: Badges[x].value[1]
        )
        
        return "\n".join(
            f"{Badges[badge].value[0]} : {badge}"
            for badge in sorted_badges
        )

    @commands.group(invoke_without_command=True, aliases=['badges', 'pr'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def profile(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        profile_data = self.profile_manager.get_user_profile(member.id)
        
        embed = discord.Embed(
            color=config.hex,
        )
        embed.set_author(name=member.display_name,icon_url=member.display_avatar)
        embed.set_footer(text=f"Luxor - Achievements",icon_url=member.display_avatar)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        if profile_data["badges"]:
            formatted_badges = self.format_badges(profile_data["badges"])
            embed.add_field(name="Badges", value=formatted_badges, inline=False)
        
        embed.add_field(
            name="Stats",
            value=f"<:stolen_emoji:1298285367660642396> Commands Used: {profile_data['commands_used']}\n"
                  f"<:stolen_emoji:1298285557318815786> Member Since: {profile_data['join_date'][:10]}"
        )

        await ctx.reply(embed=embed)

    @profile.command(name="addbadge", aliases=["give"],help="adds badges to user")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.is_owner()
    async def add_badge(self, ctx, member: discord.Member):
        view = BadgeSelectView(self.profile_manager, member)
        await ctx.reply(
            f"Select badges to add to **{member.name}**!",
            view=view,
            ephemeral=True
        )

    @profile.command(name="removebadge", aliases=["take"],help="removes badges of user")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.is_owner()
    async def remove_badge(self, ctx, member: discord.Member, badge: str):
        """Remove a badge from a user's profile"""
        badge = badge.upper()
        try:
            badge_emoji = Badges[badge].value[0]
        except KeyError:
            return await ctx.reply("Invalid badge!")

        if badge == "Users":
            return await ctx.reply("Cannot remove the default Users badge!")

        if self.profile_manager.remove_badge(member.id, badge):
            embed = discord.Embed(
                description=f"{config.tick} {ctx.author.mention}: removed {badge} from {member.mention}",
                color=config.hex
            )
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"{member.mention} doesn't have this badge!")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        profile = self.profile_manager.get_user_profile(ctx.author.id)
        profile["commands_used"] += 1
        self.profile_manager._save_data()

async def setup(bot):
    await bot.add_cog(Profile(bot))