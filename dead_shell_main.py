import discord
from discord.ext import commands
import asyncio
import os
from pw import dead_shell

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(dead_shell) # This is where your bot token goes

asyncio.run(main())