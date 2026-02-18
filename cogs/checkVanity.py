import discord
from discord.ext import commands
import aiohttp
from datetime import datetime
import time
from config import config

class VanityChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self._cache = {}
        
    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @staticmethod
    def format_boolean(value: bool) -> str:
        return "Yes" if value else "No"

    @staticmethod
    def format_verification_level(level: int) -> str:
        return {
            0: "None",
            1: "Low ( Email Verified )",
            2: "Medium",
            3: "High",
            4: "Highest ( Phone Verified)"
        }.get(level, "Unknown")

    @staticmethod
    def format_nsfw_level(level: int) -> str:
        return {
            0: "Default",
            1: "Explicit",
            2: "Safe",
            3: "Age Restricted"
        }.get(level, "Unknown")

    @staticmethod
    def format_mfa_level(level: int) -> str:
        return "Required" if level == 1 else "Not Required"

    def parse_features(self, features: list) -> str:
        if not features:
            return "None"
        
        all_features = [
            'ANIMATED_BANNER',
            'ANIMATED_ICON',
            'APPLICATION_COMMAND_PERMISSIONS_V2',
            'AUTO_MODERATION',
            'BANNER',
            'COMMUNITY',
            'CREATOR_MONETIZABLE_PROVISIONAL',
            'CREATOR_STORE_PAGE',
            'DEVELOPER_SUPPORT_SERVER',
            'DISCOVERABLE',
            'FEATURABLE',
            'INVITES_DISABLED',
            'INVITE_SPLASH',
            'MEMBER_VERIFICATION_GATE_ENABLED',
            'MORE_STICKERS',
            'NEWS',
            'PARTNERED',
            'PREVIEW_ENABLED',
            'PRIVATE_THREADS',
            'ROLE_ICONS',
            'ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE',
            'ROLE_SUBSCRIPTIONS_ENABLED',
            'TICKETED_EVENTS_ENABLED',
            'VANITY_URL',
            'VERIFIED',
            'VIP_REGIONS',
            'WELCOME_SCREEN_ENABLED',
            'THREE_DAY_THREAD_ARCHIVE',
            'SEVEN_DAY_THREAD_ARCHIVE',
            'RAID_ALERTS_DISABLED',
            'TEXT_IN_VOICE_ENABLED',
            'THREADS_ENABLED',
            'THREADS_ENABLED_TESTING',
            'PREMIUM_TIER_3_OVERRIDE',
            'NEW_THREAD_PERMISSIONS',
            'ENABLED_DISCOVERABLE_BEFORE',
            'GUILD_WEB_PAGE_VANITY_URL',
            'LINKED_TO_HUB',
            'MONETIZATION_ENABLED',
            'CHANNEL_BANNER',
            'CHANNEL_HIGHLIGHTS',
            'CHANNEL_HIGHLIGHTS_DISABLED',
            'CLYDE_ENABLED',
            'COMMERCE',
            'COMMUNITY_EXP_LARGE_UNGATED',
            'COMMUNITY_EXP_LARGE_GATED',
            'SOUNDBOARD',
            'GUILD_ONBOARDING',
            'HAD_EARLY_ACTIVITIES_ACCESS',
            'HAS_DIRECTORY_ENTRY',
            'HUB',
            'INTERNAL_EMPLOYEE_ONLY',
            'MOBILE_WEB_PREVIEW',
            'NON_COMMUNITY_RAID_ALERTS',
            'PRODUCTS_AVAILABLE_FOR_PURCHASE',
            'RELAY_ENABLED',
            'RESOURCE_CHANNEL',
            'SCREEN_SHARING_TEST',
            'STREAM_NOTIFICATIONS_ENABLED',
            'SURFACE_TEST_ENTITLEMENTS',
            'EXPOSED_TO_ACTIVITIES_WTP',
            'FORCE_RELAY',
            'BOOSTING_TIERS_EXPERIMENT_MEDIUM',
            'BOOSTING_TIERS_EXPERIMENT_SMALL'
        ]

        server_features = [feature for feature in features if feature in all_features]
        return ', '.join(server_features) if server_features else "Standard"

    @commands.command(name='checkvanity',aliases=['cv'],help="check for a vanity if it is available or not")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def check_vanity(self, ctx, vanity_code: str = None):
        if not vanity_code:
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: provide a vanity code to check",color=config.hex))
            return

        cache_key = f"vanity_{vanity_code}"
        cached_response = self._cache.get(cache_key)
        if cached_response and time.time() - cached_response['timestamp'] < 300:
            await ctx.reply(embed=cached_response['embed'])
            return

        async with ctx.typing():
            start_time = time.perf_counter()
            
            api_url = f"https://discord.com/api/v10/invites/{vanity_code}"
            
            try:
                async with self.session.get(api_url, headers={
                    "Authorization": f"Bot {self.bot.http.token}"
                }) as response:
                    
                    if response.status == 404:
                        embed = discord.Embed(
                            description=f"```The vanity URL '{vanity_code}' is available!```",
                            color=discord.Color.blurple()
                        )
                        embed.set_footer(text=f"API Response Time: {(time.perf_counter() - start_time)*1000:.2f}ms")
                        await ctx.reply(embed=embed)
                        return
                    
                    data = await response.json()
                    guild_info = data.get('guild', {})
                    
                    embed = discord.Embed(
                        description=f"```The vanity URL '{vanity_code}' is taken.```",
                        color=discord.Color.blurple(),
                        timestamp=datetime.utcnow()
                    )

                    basic_info = [
                        f"**Server Name:** {guild_info.get('name', 'N/A')}",
                        f"**Server ID:** {guild_info.get('id', 'N/A')}",
                        f"**Boosts:** {guild_info.get('premium_subscription_count', 0)}"
                    ]
                    embed.add_field(name="Basic Information", value="\n".join(basic_info), inline=False)

                    security_info = [
                        f"**Verification:** {self.format_verification_level(guild_info.get('verification_level', 0))}",
                        f"**NSFW Level:** {self.format_nsfw_level(guild_info.get('nsfw_level', 0))}",
                        f"**2FA Requirement:** {self.format_mfa_level(guild_info.get('mfa_level', 0))}",
                        f"**Content Filter:** {self.format_verification_level(guild_info.get('explicit_content_filter', 0))}"
                    ]
                    embed.add_field(name="Security Settings", value="\n".join(security_info), inline=False)

                    features = guild_info.get('features', [])
                    embed.add_field(
                        name="Server Features", 
                        value=f"```{self.parse_features(features)}```",
                        inline=False
                    )

                    stats_info = []
                    if 'rules_channel_id' in guild_info:
                        stats_info.append("Has Rules Channel")
                    if 'public_updates_channel_id' in guild_info:
                        stats_info.append("Has Updates Channel")
                    if 'preferred_locale' in guild_info:
                        stats_info.append(f"Language: {guild_info['preferred_locale']}")
                    
                    if stats_info:
                        embed.add_field(name="Additional Info", value=" | ".join(stats_info), inline=False)

                    if guild_info.get('icon'):
                        icon_url = f"https://cdn.discordapp.com/icons/{guild_info['id']}/{guild_info['icon']}.png?size=1024"
                        embed.set_thumbnail(url=icon_url)

                    if guild_info.get('banner'):
                        banner_url = f"https://cdn.discordapp.com/banners/{guild_info['id']}/{guild_info['banner']}.png?size=1024"
                        embed.set_image(url=banner_url)

                    embed.set_footer(
                        
                        text=f"API Response Time: {(time.perf_counter() - start_time)*1000:.2f}ms | "
                        
                    )
                    embed.set_author(name=f"Vanity URL Information",icon_url=self.bot.user.avatar)

                    self._cache[cache_key] = {
                        'timestamp': time.time(),
                        'embed': embed
                    }

                    await ctx.reply(embed=embed)

            except aiohttp.ClientError as e:
                await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: network error while checking vanity URL: {str(e)}",color=config.hex))
            except Exception as e:
                await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an unexpected error occurred: {str(e)}",color=config.hex))

async def setup(bot):
    await bot.add_cog(VanityChecker(bot))