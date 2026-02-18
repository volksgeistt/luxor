from discord.ext import commands
import discord
import traceback
import sys
from config import config

class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        
        if isinstance(error, commands.MissingPermissions):
            missing_perms = [perm.replace('_', ' ') for perm in error.missing_permissions]
            if len(missing_perms) > 1:
                formatted_perms = f"{', '.join(missing_perms[:-1])} and {missing_perms[-1]}"
            else:
                formatted_perms = missing_perms[0]
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you need {formatted_perms} permission(s) to use this command", color=config.hex))
            
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            print(error)
            command = ctx.command
            if command:
                help_str = command.help if command.help else ''
                aliases_str = '`, `'.join(command.aliases) if command.aliases else ''
                
                # New parameter formatting logic
                params = []
                for param_name, param in command.params.items():
                    if param_name not in ['self', 'ctx']:
                        if param.default == param.empty:
                            # Required parameter
                            params.append(f"<{param_name}>")
                        else:
                            # Optional parameter
                            params.append(f"[{param_name}]")
                params_str = ' '.join(params)

                embe = discord.Embed(color=config.hex,description=f"```\n< > : Required Arguments\n[ ] : Optional Arguments```").set_author(name=self.bot.user, icon_url=self.bot.user.avatar)
                embe.add_field(name="Command", value=f"{command}", inline=False)
                if help_str:
                    embe.add_field(name="Help", value=f"{help_str}", inline=False)
                if aliases_str:
                    embe.add_field(name="Aliases", value=f"`{aliases_str}`", inline=False)
                if params_str:
                    embe.add_field(name="Usage", value=f"`{command} {params_str}`", inline=False)
                await ctx.reply(embed=embe)
                
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: couldn't find that member in the server", color=config.hex))
            
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_perms).replace("_", " ")
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: i'm missing permissions: {perms}", color=config.hex))
            
        elif isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            if seconds < 60:
                time = f"{seconds} second(s)"
            elif seconds < 3600:
                time = f"{seconds//60} minute(s)"
            elif seconds < 86400:
                time = f"{seconds//3600} hour(s)"
            else:
                time = f"{seconds//86400} day(s)"
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you're on cooldown, try again in {time}", color=config.hex))
            
        elif isinstance(error, commands.NotOwner):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this command is only for bot owners", color=config.hex))
            
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this command is currently disabled", color=config.hex))
            
        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this command can only be used in NSFW channels", color=config.hex))
            
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this command can't be used in DMs", color=config.hex))
            
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this command can only be used in DMs", color=config.hex))
            
        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: too many arguments provided", color=config.hex))
            
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: couldn't find that role in the server", color=config.hex))
            
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: couldn't find that channel in the server", color=config.hex))
            
        elif isinstance(error, commands.EmojiNotFound):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: couldn't find that emoji", color=config.hex))
            
        elif isinstance(error, commands.UserNotFound):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: couldn't find that user", color=config.hex))
            
        elif isinstance(error, commands.MessageNotFound):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: couldn't find that message", color=config.hex))
            
        elif isinstance(error, commands.MissingRole):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you're missing the required role to use this command", color=config.hex))
            
        elif isinstance(error, commands.BotMissingRole):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: i'm missing the required role to perform this command", color=config.hex))
            
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you're missing the required roles to use this command", color=config.hex))
            
        elif isinstance(error, commands.BotMissingAnyRole):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: i'm missing the required roles to perform this command", color=config.hex))
            
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you don't meet the requirements to use this command", color=config.hex))
            
        elif isinstance(error, commands.CheckAnyFailure):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: you don't meet any of the requirements to use this command", color=config.hex))
            
        elif isinstance(error, commands.CommandNotFound):
            return # Silently ignore command not found errors
            
        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: this command is already running at its maximum capacity", color=config.hex))
            
        elif isinstance(error, discord.Forbidden):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: i don't have permission to do that", color=config.hex))
            
        elif isinstance(error, discord.NotFound):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: the requested resource was not found", color=config.hex))
            
        elif isinstance(error, discord.HTTPException):
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an HTTP exception occurred", color=config.hex))
            
        else:
            # Log unhandled errors
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention}: an unexpected error occurred", color=config.hex))

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Log non-command errors"""
        print(f'Ignoring exception in {event}', file=sys.stderr)
        traceback.print_exc()

async def setup(bot):
    await bot.add_cog(Error(bot))