import discord
from discord.ext import commands
import datetime
import asyncio
import random
from lists import shrimp_facts, used_shrimp_facts, burns, used_burns, jokes, used_jokes

async def setup(bot):
    await bot.add_cog(text_cog(bot))

class text_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kill_calls = 0


    @commands.Cog.listener()
    async def on_ready(self):
        print("text_cog is running! Command away!")
        self.bot.loop.create_task(self.daily_shrimp())
            


    async def daily_shrimp(self):
        shrimp_time = datetime.time(hour=9, minute=0, second=0)
        now = datetime.datetime.now()
        shrimp_datetime = datetime.datetime.combine(now.date(), shrimp_time)
        guild_id = 1296635922325962762
        channel_id = 1336132931592392724

        guild = discord.utils.get(self.bot.guilds, id = guild_id)
        if not guild:
            print(f"Server with ID {guild_id} not found")

        channel = discord.utils.get(guild.text_channels, id = channel_id)
        if not channel:
            print(f"Channel starting with 'shrimp' not found in server {guild_id}")

        if shrimp_facts == []:
            shrimp_facts.append(used_shrimp_facts)
            used_shrimp_facts.clear()

        response = random.choice(shrimp_facts)
        shrimp_facts.remove(response)
        used_shrimp_facts.append(response)

        if now >= shrimp_datetime:
            shrimp_datetime += datetime.timedelta(days=1)

        wait_time =(shrimp_datetime - now).total_seconds()
        print(f"Waiting {wait_time} seconds until Shrimp Time! ({shrimp_datetime})")
        await asyncio.sleep(wait_time)
        await channel.send("Here is today's Cool Shrimp fact!: \n" + response)



    @commands.command(
            name = "kill",
            aliases = ["k"],
            help = ""
        )
    
    async def kill(self, ctx):
        self.image = discord.File("C:\Coding Projects\earth_explosion.jpg")
        print("kill command called!")
        self.kill_calls += 1
        if self.kill_calls == 1:
            await ctx.send("How messed up are you!? You're just going to use the kill command when you don't even know what it does? Psychotic!")
        elif self.kill_calls == 2:
            await ctx.send("Seriously? Again? You're just going to keep using the kill command?")
        elif self.kill_calls == 3:
            await ctx.send("You really want to do this? I don't think you know what you're asking for.")
        elif self.kill_calls == 4:
            await ctx.send("This isn't going to end well.")
        elif self.kill_calls == 5:
            await ctx.send("Last warning.")
        elif self.kill_calls == 6:
            await ctx.send(file=self.image)
            await ctx.send("You did this")
            self.kill_calls = 0
        else:
            print(f"self.kill_calls = {self.kill_calls}")
            self.kill_calls = 0
            await ctx.send("--ERROR-- That broke something, but it should be reset now. Try it again!")



    @commands.command(
            name = "roast",
            aliases = ["ro"],
            help = ""
            )
    async def roast(self, ctx):

        if burns == []:
            burns.append(used_burns)
            used_burns.clear()
        
        response = random.choice(burns)
        burns.remove(response)
        used_burns.append(response)
        await ctx.send(response)



    @commands.command(
            name = "mama",
            aliases = ["ma"],
            help = ""
            )
    async def mama(self, ctx):

        if jokes == []:
            jokes.append(used_jokes)
            used_jokes.clear()
        
        response = random.choice(jokes)
        jokes.remove(response)
        used_jokes.append(response)
        await ctx.send(response)