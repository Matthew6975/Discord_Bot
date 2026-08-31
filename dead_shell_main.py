import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
import logging

custom_format = "[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d | %(message)s"

discord.utils.setup_logging(
    level=logging.DEBUG,
    formatter=logging.Formatter(fmt=custom_format),
    root=True
)
#these lines set the logging level for discord and discord.http to INFO and WARNING respectively, which will ignore the spam of DEBUG messages in the log from discords backend.
#This should let me see my custom logs more easily.
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)

load_dotenv()
dead_shell = os.getenv("dead_shell")
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