import discord
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(help_cog(bot))


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        log.debug("help_cog is running! Command away!")


    