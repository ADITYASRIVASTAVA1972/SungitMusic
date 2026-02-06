import discord
from discord.ext import commands
from discord.ui import View, Button
import yt_dlp
import asyncio

# ================= CONFIG =================
import os
TOKEN = os.getenv("TOKEN")
PREFIX = "-"
# ==========================================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

queues = {}
stay_247 = False

ytdl = yt_dlp.YoutubeDL({
    "format": "bestaudio",
    "quiet": True
})


# ================= EVENTS =================
@bot.event
async def on_ready():
    print("=================================")
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print("🎵 Sungit Music Bot is READY")
    print("=================================")


# ================= UTILS =================
def get_stream(query):
    info = ytdl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
    return info["url"], info["title"]


async def play_next(ctx):
    if queues.get(ctx.guild.id):
        url, title = queues[ctx.guild.id].pop(0)

        source = discord.FFmpegPCMAudio(url, options="-vn")
        ctx.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx), bot.loop
            )
        )

        embed = discord.Embed(
            title="🎶 Now Playing",
            description=title,
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=Controls(ctx))

    else:
        if not stay_247:
            await asyncio.sleep(20)
            if ctx.voice_client and not ctx.voice_client.is_playing():
                await ctx.voice_client.disconnect()


# ================= BUTTONS =================
class Controls(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="⏯", style=discord.ButtonStyle.primary)
    async def pause(self, interaction: discord.Interaction, button: Button):
        vc = self.ctx.voice_client
        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Paused", ephemeral=True)
        else:
            vc.resume()
            await interaction.response.send_message("▶ Resumed", ephemeral=True)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: Button):
        self.ctx.voice_client.stop()
        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: Button):
        await self.ctx.voice_client.disconnect()
        await interaction.response.send_message("⏹ Stopped & Left VC", ephemeral=True)


# ================= COMMANDS =================
@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ You need to be in VC first")

    if ctx.voice_client:
        return await ctx.send("✅ Already connected")

    await ctx.author.voice.channel.connect()
    await ctx.send(f"✅ Joined **{ctx.author.voice.channel.name}**")


@bot.command(aliases=["p"])
async def play(ctx, *, song: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Join VC first")

    if not ctx.voice_client:
        await ctx.invoke(join)

    url, title = get_stream(song)

    queues.setdefault(ctx.guild.id, []).append((url, title))

    if ctx.voice_client.is_playing():
        return await ctx.send(f"➕ Added to queue: **{title}**")

    await play_next(ctx)


@bot.command()
async def skip(ctx):
    ctx.voice_client.stop()
    await ctx.send("⏭ Skipped")


@bot.command()
async def stop(ctx):
    ctx.voice_client.pause()
    await ctx.send("⏸ Paused")


@bot.command()
async def left(ctx):
    await ctx.voice_client.disconnect()
    await ctx.send("👋 Left VC")


@bot.command(aliases=["q"])
async def queue(ctx):
    q = queues.get(ctx.guild.id)
    if not q:
        return await ctx.send("📭 Queue is empty")

    msg = "\n".join([f"{i+1}. {t[1]}" for i, t in enumerate(q)])
    await ctx.send(f"🎵 **Queue:**\n{msg}")


@bot.command(name="247")
async def stay(ctx):
    global stay_247
    stay_247 = not stay_247
    await ctx.send(f"🔁 24/7 Mode: {'ON' if stay_247 else 'OFF'}")


# ================= START =================
bot.run(TOKEN)
