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
        log.debug("text_cog is running!")
        #self.bot.loop.create_task(self.daily_shrimp())
            


    # async def daily_shrimp(self):
    #     shrimp_time = datetime.time(hour=9, minute=0, second=0)
    #     now = datetime.datetime.now()
    #     shrimp_datetime = datetime.datetime.combine(now.date(), shrimp_time)
    #     guild_id = 1296635922325962762
    #     channel_id = 1336132931592392724

    #     guild = discord.utils.get(self.bot.guilds, id = guild_id)
    #     if not guild:
    #         print(f"Server with ID {guild_id} not found")

    #     channel = discord.utils.get(guild.text_channels, id = channel_id)
    #     if not channel:
    #         print(f"Channel starting with 'shrimp' not found in server {guild_id}")

    #     if shrimp_facts == []:
    #         shrimp_facts.append(used_shrimp_facts)
    #         used_shrimp_facts.clear()

    #     response = random.choice(shrimp_facts)
    #     shrimp_facts.remove(response)
    #     used_shrimp_facts.append(response)

    #     if now >= shrimp_datetime:
    #         shrimp_datetime += datetime.timedelta(days=1)

    #     wait_time =(shrimp_datetime - now).total_seconds()
    #     print(f"Waiting {wait_time} seconds until Shrimp Time! ({shrimp_datetime})")
    #     await asyncio.sleep(wait_time)
    #     await channel.send("Here is today's Cool Shrimp fact!: \n" + response)



    @commands.command(
            name = "kill",
            aliases = ["k"],
            help = ""
        )
    
    async def kill(self, ctx):
        self.image = discord.File(r"C:\Coding Projects\earth_explosion.jpg")
        log("kill command called!")
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
            log.error(f"self.kill_calls = {self.kill_calls}")
            self.kill_calls = 0
            await ctx.send("--ERROR-- That broke something, but it should be reset now. Try again!")



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


    async def gen_help_embed(self):
            try:
                log.debug("generating help embed.")
                help_embed = discord.Embed(
                title = "Available Commands:",
                description ="**!play, !pl (your search here without the parentheses) -** Causes the bot to join the VC you are in and plays the audio returned from your search. Also resumes music if it is paused as well as adds a song to queue if a song is currently playing.\n\n**!add (your search here without the parentheses) -** Inserts song as next in queue.\n\n**!pause, !stop, -** Stops the music from playing. Can be resumed with !play.\n\n**!skip, !sk, !next -** Skips the current song if there is a song in queue to skip to.\n\n**!previous, !pr -** Goes back and plays the previous song. Does not alter the queue.\n\n**!queue, !q, !list -** Lists the current song playing and up to the next 5 in queue.\n\n**!clear, !c, !empty -** Clears the queue after the current song. Leaves previously played queue in tact.\n\n**!remove, !rem -** Removes the last added song from the queue.\n\n**!leave, !l -** Causes the bot to leave the VC. Clears queue entirely.\n\n**!commands, !options -** Returns a list of all available commands.\n\n**!roast, !ro -** Returns a sick burn.\n\n**!mama, !ma -** Returns a random yo mama joke\n\n**!kill, !k -**" )
                return help_embed
            except Exception as e:
                log.error("error generating help embed")
                log.error(e)
        
    @commands.command(
        name = "commands",
        aliases = ["options"],
        help = ""
        )
    
    async def help(self, ctx):
        print("Commands command called!")
        help = await self.gen_help_embed()
        await ctx.send(embed = help)