import discord
from discord.ext import commands
import asyncio
import logging
from cogs.music_cog import ensure_voice

log = logging.getLogger(__name__)

async def setup(bot):
    await bot.add_cog(admin_cog(bot))

class admin_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log.debug("admin_cog is running!")

    @commands.command(
            name = "reload",
            aliases = ["r"],
            help = "Reloads a cog. Usage: !reload <cog_name>"
    )
    @commands.check(ensure_voice)
    async def reload(self, ctx):
        await ctx.send("Reloading bot...")
        state = ctx.bot.cogs["music_cog"].get_server_state(int(ctx.guild.id))
        if state.vc is not None and state.vc.is_connected():
            await state.vc.disconnect()

        state.is_playing = False
        state.is_paused = False
        state.music_queue = []
        state.queue_index = 0
        state.vc = None
        state.searching_message = None
        state.now_playing_message = None
        state.song_added_message = None
        state.vc_channel = None

        await ctx.send("Bot state safely reloaded")