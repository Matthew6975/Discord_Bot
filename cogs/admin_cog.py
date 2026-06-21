import discord
from discord.ext import commands
import asyncio

async def setup(bot):
    await bot.add_cog(admin_cog(bot))

class admin_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("admin_cog is running!")

    @commands.command(
            name = "reload",
            aliases = ["r"],
            help = "Reloads a cog. Usage: !reload <cog_name>"
    )
    async def reload(self, ctx):
        await ctx.send("Reloading bot...")
        id = int(ctx.guild.id)
        if self.vc.get(id) != None and self.vc.get(id).is_connected():
            await self.vc[id].disconnect()

        self.is_playing[id] = False
        self.is_paused[id] = False
        self.music_queue[id] = []
        self.queue_index[id] = 0
        self.vc[id] = None
        self.searching_message = None
        self.now_playing_message = None

        await ctx.send("Bot state safely reloaded")