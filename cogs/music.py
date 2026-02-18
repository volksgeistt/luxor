import discord
import wavelink
import datetime
from discord.ext import commands
from config import config
from typing import cast, Optional
from wavelink import TrackSource
from discord.ext import commands
from discord.ext.commands import Context

def create_embed(d):
  embed = discord.Embed(description=d, color=config.hex)
  return embed

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="join", description="connect to voice channel")
    async def join(self, ctx: Context, channel:discord.VoiceChannel):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if channel is None:
            channel = ctx.author.voice.channel

        if not player:
            try:
                player = await channel.connect(cls=wavelink.Player)
                embed = create_embed(f"{config.tick} {ctx.author.mention}: successfully connected to `{channel.name}`.")
                await ctx.send(embed=embed)
            except Exception as e:
                embed = create_embed(f"{config.cross} {ctx.author.mention}: unable to connect to the voice channel.")
                return await ctx.send(embed=embed)


    @commands.command(
        name="leave",
        description="leave from the connected voice channel"
    )
    async def leave(self, ctx: Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: there is no voice channel connected.")
            return await ctx.send(embed=embed)

        embed = create_embed(f"{config.tick} {ctx.author.mention}: successfully left the voice channel.")
        await player.disconnect()
        await ctx.send(embed=embed)


    @commands.command(
        name="play",
        description="play a track (query or url)",
        aliases=['p']
    )
    async def play(self, ctx: Context, *, query: str):
        player: wavelink.Player
        player = cast(wavelink.Player, ctx.voice_client)

        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True, timeout=60)  # type: ignore
            except AttributeError:
                embed = create_embed(f"{config.cross} {ctx.author.mention}: there is no voice channel connected.")   
                return await ctx.send(embed=embed)
            except discord.ClientException:
                embed = create_embed(f"{config.cross} {ctx.author.mention}: unable to join the voice channel.")
                return await ctx.send(embed=embed)
                
            
        if not hasattr(player, "home"):
            player.home = ctx.channel
        elif player.home != ctx.channel:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: songs can be only played in {player.home.mention}")
            return await ctx.send(embed=embed)
        
        tracks: wavelink.Search = await wavelink.Playable.search(query, source=TrackSource.YouTube)
        if not tracks:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: unable to find the song.")
            return await ctx.send(embed=embed)
            
        player.autoplay = wavelink.AutoPlayMode.disabled
        player.inactive_timeout = 60

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            embed = create_embed(f"{config.tick} {ctx.author.mention}: playlist **`{tracks.name}`** ({added} tracks) has been added to the queue.")
            await ctx.send(embed=embed)
        else:
            track: wavelink.Playable = tracks[0]
            embed = create_embed(f"{config.tick} {ctx.author.mention}: **`{track}`** has been added to the queue.")
            await player.queue.put_wait(track)
            await ctx.send(embed=embed)

        if not player.playing:
            await player.play(player.queue.get(), volume=30)



    @commands.command(
        name="pause",
        description="pause/resume the current track",
        aliases=['resume']
    )
    async def pause(self, ctx: Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: there is no song currently playing.")
            return await ctx.send(embed=embed)

        if not player.paused:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: pausing the song.")
            await ctx.send(embed=embed)
        else:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: resuming the song.")
            await ctx.send(embed=embed)
        await player.pause(not player.paused)


    @commands.command(
        name="skip",
        description="skip current song"
    )
    async def skip(self, ctx: Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: there is no song currently playing.")
            return await ctx.send(embed=embed)
        
        embed = create_embed(f"{config.tick} {ctx.author.mention}: skipping `{player.current.title}`.")
        await ctx.send(embed=embed)
        await player.skip(force=True)

        
    @commands.command(
        name="nowplaying",
        description="sisplay the current track",
        aliases=["np"]
        )
    async def nowplaying(self, ctx: Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: there is no song currently playing.")
            return await ctx.send(embed=embed)

        if player.playing:
            track = player.current

            embed = discord.Embed(title=f"Luxor Music", color=config.hex)
            embed.add_field(name="Length", value=str(datetime.timedelta(milliseconds=int(track.length))), inline=True)
            embed.add_field(name="Playing", value=f"[{track.title}]({track.uri})", inline=True)
            embed.set_image(url="https://cdn.discordapp.com/attachments/1321755883104899116/1322605380769021963/White_Colorful_Music_Concert_Banner.png?ex=67717bbf&is=67702a3f&hm=5f72d1258d15f964f9ee3f8dfdc03d7b0b9927449936737d6baabb445d156cac&")

            return await ctx.send(embed=embed)

    

    @commands.command(
        name="queue",
        description="display the current queue"
    )
    async def queue(self, ctx: Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        
        if not player:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: there is no song currently playing.")
            return await ctx.send(embed=embed)
        else:
            queue = player.queue
        
        if queue.is_empty == False:
            playtime = 0
            for i, track in enumerate(queue):
                playtime += track.length
            
            playtime = datetime.timedelta(milliseconds=playtime)

            embed = discord.Embed(
                title=f"Playlist ({playtime}): ",
                description="\n".join(f"**{i+1}. {track}**" for i, track in enumerate(queue)),
                color=config.hex
            ).set_thumbnail(url=self.bot.user.avatar)
            return await ctx.send(embed=embed)
        
        else:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: queue is empty.")
            return await ctx.send(embed=embed)


    @commands.command(
        name='remove',
        description='remove a track from the queue'
    )
    async def remove(self, ctx: Context, number: int):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        queue = player.queue

        if number <= 0:
            embed = create_embed(f"{config.cross} {ctx.author.mention}: please enter an integer greater or equal to 1.")
            return await ctx.reply(embed=embed)
        else:
            try:
                removed_track = queue[number-1]
                queue.delete(number-1)
                embed = create_embed(f"{config.tick} {ctx.author.mention}: removed `{removed_track.title}`")
                return await ctx.send(embed=embed)
            except:
                embed = create_embed(f"{config.cross} {ctx.author.mention}: something went wrong!")
                return await ctx.send(embed=embed)


    @commands.command(
        name="empty",
        description="clear the queue",
        aliases=['clearq']
    )
    async def empty(self, ctx: Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        queue = player.queue
        queue.reset()

        embed = create_embed(f"{config.tick} {ctx.author.mention}: queue has been cleared.")
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print("[CONNECTING TO LAVALINK]")
        nodes = [wavelink.Node(uri="https://lava-v4.ajieblogs.eu.org", password="https://dsc.gg/ajidevserver")]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)
        
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        print(f"[CONNECTED] {payload.node!r}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        
        if not player:
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed = discord.Embed(color=config.hex)
        embed.add_field(name="Playing", value=f"[{track.title}]({track.uri})", inline=True)
        embed.add_field(name="Length", value=str(datetime.timedelta(milliseconds=int(track.length))), inline=True)
        embed.set_author(name=f"{self.bot.user.name} Music",icon_url=self.bot.user.avatar)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1321755883104899116/1322605380769021963/White_Colorful_Music_Concert_Banner.png?ex=67717bbf&is=67702a3f&hm=5f72d1258d15f964f9ee3f8dfdc03d7b0b9927449936737d6baabb445d156cac&")

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        if original and original.recommended:
            embed.description = f"\n\n(Added by autoplay)"

        await player.home.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return
        
        members = set()
        for member in player.channel.members:
            members.add(member.id)

        if len(members) <= 1:
            embed = create_embed(f"{config.error_emoji} {player.channel.mention}: no users are in the voice channel, so playback has stopped.")
            await player.home.send(embed=embed)
            await player.stop(force=True)
            player.autoplay = wavelink.AutoPlayMode.disabled
            return
        
        if player.autoplay == wavelink.AutoPlayMode.enabled:
            return
        else:
            try:
                await player.play(player.queue.get(), volume=30)
            except:
                pass

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.player) -> None:
        embed = create_embed(f"{config.error_emoji} {player.channel.mention}: disconnected from the voice channel after `{player.inactive_timeout}` seconds of inactivity.")
        await player.home.send(embed=embed)
        player.autoplay = wavelink.AutoPlayMode.disabled
        await player.disconnect()

async def setup(bot):
    await bot.add_cog(Music(bot))