import discord
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(help_cog(bot))


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print("help_cog is running! Command away!")


    async def gen_help_embed(self):
        try:
            print("generating help embed.")
            help_embed = discord.Embed(
            title = "Available Commands:",
            description ="**!play, !pl (your search here without the parentheses) -** Causes the bot to join the VC you are in and plays the audio returned from your search. Also resumes music if it is paused as well as adds a song to queue if a song is currently playing.\n\n**!add (your search here without the parentheses) -** Inserts song as next in queue.\n\n**!pause, !stop, -** Stops the music from playing. Can be resumed with !play.\n\n**!skip, !sk, !next -** Skips the current song if there is a song in queue to skip to.\n\n**!previous, !pr -** Goes back and plays the previous song. Does not alter the queue.\n\n**!queue, !q, !list -** Lists the current song playing and up to the next 5 in queue.\n\n**!clear, !c, !empty -** Clears the queue after the current song. Leaves previously played queue in tact.\n\n**!remove, !rem -** Removes the last added song from the queue.\n\n**!leave, !l -** Causes the bot to leave the VC. Clears queue entirely.\n\n**!commands, !options -** Returns a list of all available commands.\n\n**!roast, !ro -** Returns a sick burn.\n\n**!mama, !ma -** Returns a random yo mama joke\n\n**!kill, !k -**" )
            return help_embed
        except Exception as e:
            print("error generating help embed")
            print(e)
    
    @commands.command(
        name = "commands",
        aliases = ["options"],
        help = ""
        )
    
    async def help(self, ctx):
        print("Commands command called!")
        help = await self.gen_help_embed()
        await ctx.send(embed = help)