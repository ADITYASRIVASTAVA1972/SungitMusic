import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import asyncio
import yt_dlp

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='-', intents=intents)

# Queue dictionary per guild
guild_queues = {}

# FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# YT-DLP options
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True
}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("🎵 Music Bot is READY")

# Join command
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"✅ Joined **{channel}**")
        else:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"✅ Moved to **{channel}**")
    else:
        await ctx.send("❌ You are not in a voice channel!")

# Play command
@bot.command()
async def play(ctx, *, url):
    if ctx.voice_client is None:
        await join(ctx)

    guild_id = ctx.guild.id
    if guild_id not in guild_queues:
        guild_queues[guild_id] = []

    guild_queues[guild_id].append(url)

    # If not already playing, start the queue
    if not ctx.voice_client.is_playing():
        await play_next(ctx)

async def play_next(ctx):
    guild_id = ctx.guild.id
    if len(guild_queues[guild_id]) == 0:
        await ctx.voice_client.disconnect()
        return

    url = guild_queues[guild_id][0]

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    source = FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
    ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(after_song(ctx), bot.loop))

async def after_song(ctx):
    guild_id = ctx.guild.id
    guild_queues[guild_id].pop(0)
    if len(guild_queues[guild_id]) > 0:
        await play_next(ctx)

# Skip command
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipped!")
    else:
        await ctx.send("❌ Nothing is playing!")

# Stop command
@bot.command()
async def stop(ctx):
    guild_id = ctx.guild.id
    if ctx.voice_client:
        ctx.voice_client.stop()
        guild_queues[guild_id] = []
        await ctx.send("⏹ Stopped and cleared the queue!")
    else:
        await ctx.send("❌ Nothing is playing!")

# Pause command
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Paused!")
    else:
        await ctx.send("❌ Nothing is playing!")

# Resume command
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ Resumed!")
    else:
        await ctx.send("❌ Nothing is paused!")

# Queue command
@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in guild_queues and len(guild_queues[guild_id]) > 0:
        msg = "**Queue:**\n"
        for i, song in enumerate(guild_queues[guild_id], start=1):
            msg += f"{i}. {song}\n"
        await ctx.send(msg)
    else:
        await ctx.send("❌ Queue is empty!")

# Now Playing
@bot.command()
async def np(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.send(f"▶ Now Playing: {guild_queues[ctx.guild.id][0]}")
    else:
        await ctx.send("❌ Nothing is playing!")

bot.run("YOUR_BOT_TOKEN")
