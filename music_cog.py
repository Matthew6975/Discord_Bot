import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import asyncio
from asyncio import run_coroutine_threadsafe
from yt_dlp import YoutubeDL
from urllib import parse, request
import re

async def setup(bot):
    await bot.add_cog(music_cog(bot))

#initialize the music cog to the bot.
class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        #embed colors to reference later.
        self.embed_blue = 0x2c76dd
        self.embed_red = 0xdf1141
        self.embed_green = 0x0eaa51
        self.embed_yellow = 0xFFFF00
        self.embed_purple = 0x800080

        #initializes variables the bot uses during its function.
        #the first two specifically act like switches (True/False) to help the bot track if it is playing or paused
        self.is_playing = {}
        self.is_paused = {}
        self.music_queue = {}
        self.queue_index = {}
        self.vc = {}

        #options/settings for YoutubeDL and ffmpeg. Full disclosure, I'm not sure what all of these do, 
        #but I got them from sample code online and they work. if it ain't broke, don't fix it.
        self.yt_dl_options = {"format": "bestaudio/best"}
        self.ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

    #listener that runs when the bot is ready. Sets all variables to default values each time the code is run/re-run.
    @commands.Cog.listener()
    async def on_ready(self):
        print("music_cog is running! Command away!")
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.music_queue[id] = []
            self.queue_index[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False
            

    #listener that runs when a user leaves a voice channel. If the bot is the only one left in the channel, it disconnects.
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        id = int(member.guild.id)
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remaining_channel_members = before.channel.members
            if len(remaining_channel_members) == 1 and remaining_channel_members[0].id == self.bot.user.id and self.vc[id].is_connected:
                self.is_playing[id] = self.is_paused[id] = False
                self.music_queue = []
                self.queue_index = 0
                await self.vc[id].disconnect()
                self.vc[id] = None


#-----------------------------------NON-CALLABLE FUNCTIONS-----------------------------------------------------
    #Generates different embeds to be sent in the chat based on the type used to call the function.
    #generally used to show what is playing/what was added to the queue.
    async def gen_embed(self, ctx, song, type):
        if type == 5:
            loading_embed = discord.Embed(
                title = "Searching for song ...",
                description = "searching for song ... please wait.",
                color = self.embed_blue
            )
            return loading_embed
        
        title = song["title"]
        link = song["link"]
        thumbnail = song["thumbnail"]
        author = ctx.author
        avatar = author.avatar

        if type == 1:
            now_playing = discord.Embed(
                title = "Now Playing",
                description = f"[{title}]({link})",
                color = self.embed_blue
                )
            now_playing.set_thumbnail(url=thumbnail)
            now_playing.set_footer(text = f"Song Added by: {str(author)}", icon_url = avatar)
            return now_playing

        if type == 2:
            song_added = discord.Embed(
                title = "Song Added to Queue!",
                description = f"[{title}]({link})",
                color = self.embed_green
                )
            song_added.set_thumbnail(url=thumbnail)
            song_added.set_footer(text = f"Song Added by: {str(author)}", icon_url = avatar)
            return song_added
        
        if type == 3:
            song_removed = discord.Embed(
                title = "Song Removed From Queue!",
                description = f"[{title}]({link})",
                color = self.embed_red
                )
            song_removed.set_thumbnail(url=thumbnail)
            song_removed.set_footer(text = f"Song Removed by: {str(author)}", icon_url = avatar)
            return song_removed

        if type == 4:
            song_next = discord.Embed(
                title = "Song Inserted Next in Queue!",
                description = f"[{title}]({link})",
                color = self.embed_purple
                )
            song_next.set_thumbnail(url=thumbnail)
            song_next.set_footer(text = f"Song Inserted by: {str(author)}", icon_url = avatar)
            return song_next


    #Causes the bot to join the VC of the user that called the command. 
    #Has some error handling to make sure the bot doesn't try to join a channel that doesn't exist or is empty.
    async def join_vc(self, ctx, channel):
        id = int(ctx.guild.id)

        if self.vc[id] == None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()

            if self.vc[id] == None:
                await ctx.send("Could not connect to the voice channel")
                return
        else:
            await self.vc[id].move_to(channel)

    #again, mostly copy-pasted code from the internet.
    #this function searches for a YouTube link based on the search criteria provided by the user who submits the call
    #If they provide a link, it sends that link off to have the audio extracted.
    async def search_YT(self, search):
            if "https://www.youtube.com/watch?v=" in search:
                print("search_YT, if")
                return search
            else:
                print("search_YT, else")
                query_string = parse.urlencode({"search_query": search})
                htm_content = request.urlopen('https://www.youtube.com/results?' + query_string)
                search_results = re.findall('/watch\?v=(.{11})', htm_content.read().decode())
                return search_results[0]
    

    #extracts audio, thumbnail, title, from the YouTube link provided by the Search_YT function.
    #Note: the search_YT function returns to the play function, which then uses this function to extract the audio.
    async def extract_YT(self, url):
        with YoutubeDL(self.yt_dl_options) as ydl:
            try:
                info = ydl.extract_info(url, download = False)
            except:
                return False
        return {
            "link": "https://www.youtube.com/results?/watch\?v=" + url,
            "thumbnail": info["thumbnails"][-1]["url"],
            "source": info["url"],
            "title": info["title"]
        }
    
    #moves the bot to the next song in the queue if the current song ends.
    #calls itself towards the bottom and incriments the queue to loop and continue playing the next song automatically.
    async def play_next(self, ctx):
        print("play next, main")
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            print("play next, if 1")
            return
        if self.queue_index[id] + 1 < len(self.music_queue[id]):
            print("play next, if 2")
            print(len(self.music_queue[id]))
            print(self.queue_index[id])
            self.is_playing[id] = True
            self.queue_index[id] += 1

            song = self.music_queue[id][self.queue_index[id]][0]
            
            #if a "now playing" message exists, it deletes it and then replaces it with a new, updated one later in the function.
            #has some built-in error handling.
            if hasattr(self, "now_playing_message") and self.now_playing_message:
                print("hasattr, play_next")
                try:
                    await self.now_playing_message.delete()
                except Exception as e:
                    print(e)

            #you'll see this code a lot. This is the block that calls gen_embed to generate a embed to send to the chat.
            playing_embed = await self.gen_embed(ctx, song, 1) #final argument decides the type of embed to generate. 1 generates "now playing".
            self.now_playing_message = await ctx.send(embed = playing_embed)

            self.vc[id].play(discord.FFmpegOpusAudio(
                song["source"], **self.ffmpeg_options), after = lambda e:  asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop,))
        
        #end of queue handling. Sends a message letting the user(s) know that the queue is empty.
        else:
            print("play next, else")
            await ctx.send("You have reached the end of the queue!")
            self.queue_index[id] += 1
            self.is_playing[id] = False


    #kicks off the music playing process. Very similar ot the play next function in most of it's design.
    #upon reviewing this code, I think I could probably combine the two functions into one to save space. Will look into this.
    async def play_music(self, ctx):
        print("play music called")
        id = int(ctx.guild.id)
        if self.queue_index[id] < len(self.music_queue[id]):
            print("play music, 1")
            self.is_playing[id] = True
            self.is_paused[id] = False

            await self.join_vc(ctx, self.music_queue[id][self.queue_index[id]][1])

            song = self.music_queue[id][self.queue_index[id]][0]

            if hasattr(self, "now_playing_message") and self.now_playing_message:
                print("hasattr, play_next")
                try:
                    await self.now_playing_message.delete()
                except Exception as e:
                    print(e)

            if self.searching_message:
                playing_embed = await self.gen_embed(ctx, song, 1)
                self.now_playing_message = await self.searching_message.edit(embed = playing_embed)
                self.searching_message = None
            else:
                playing_embed = await self.gen_embed(ctx, song, 1)
                self.now_playing_message = await ctx.send(embed = playing_embed)

            self.vc[id].play(discord.FFmpegOpusAudio(
                song["source"], **self.ffmpeg_options), after = lambda e:  asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        else:
            print("play music, 2")
            await ctx.send("There are no more songs in the queue")
            self.queue_index[id] += 1
            self.is_playing[id] = False



#------------------------------CALLABLE COMMANDS------------------------------------------------------------------------------------

    @commands.command(
            name = "play",
            aliases = ["pl"],
            help = ""
        )
    
    async def play(self, ctx, *args):
        print("Play command called!")
        search = " ".join(args)
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except: 
            await ctx.send("You must be connected to a voice channel.")
            return

        if not args:
            print("Play, 1")
            if len(self.music_queue[id]) == 0:
                print("Play, 2")
                await ctx.send("there are no more songs in queue.")
                return
            elif self.is_playing[id] == False:
                if self.music_queue[id] == None or self.vc[id] == None:
                    print("Play, 3")
                    await self.play_music(ctx)
                else:
                    print("Play, 4")
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                print("Play, 5")
                return
        else:
            loading_embed = await self.gen_embed(ctx, None, 5)
            self.searching_message = await ctx.send(embed = loading_embed)
            print("Play, 6")
            search_results = await self.search_YT(search)
            print(search_results)
            song = await self.extract_YT(search_results)
            if type(song) == type(True):
                print("Play, 7")
                print(song)
                await ctx.send("Could not download song. Incorrect format, try again with some different keywords.")
            else:
                print("Play, 8")
                self.music_queue[id].append([song, user_channel])

                if not self.is_playing[id] and self.is_paused[id]:
                    print("Play, 9")
                    self.queue_index[id] += 1
                    await self.play_music(ctx)
                elif not self.is_playing[id]:
                    print("Play, 10")
                    await self.play_music(ctx)
                else:
                    print("Play, 11")
                    if self.searching_message:
                        message = await self.gen_embed(ctx, song, 2)
                        self.song_added_message = await self.searching_message.edit(embed = message)
                        self.searching_message = None
                    else:
                        message = await self.gen_embed(ctx, song, 2)
                        self.song_added_message = await ctx.send(embed = message)


                

    @commands.command(
        name = "add",
        aliases = ["insert"],
        help = ""
        )
    async def add(self, ctx, *args):
            print("Add command called!")
            search = " ".join(args)
            id = int(ctx.guild.id)
            try:
                print("Add, 1")
                userChannel = ctx.author.voice.channel
            except:
                print("Add, 2")
                await ctx.send("You must be connected to a voice channel.")
                return
            if not args:
                await ctx.send("You need to provide a search term to add a song to the queue.")
            else:
                try:
                    print("Add, 9")
                    loading_embed = await self.gen_embed(ctx, None, 5)
                    self.searching_message = await ctx.send(embed = loading_embed)
                    search_results = await self.search_YT(search)
                    song = await self.extract_YT(search_results)
                    if type(song) == type(True):
                        print("Add, 10")
                        await ctx.send("Could not download the song. Incorrect format, try some different keywords.")
                    else:
                        print("Add, 11")
                        self.music_queue[id].insert(self.queue_index[id] + 1, [song, userChannel])
                        if self.searching_message:
                            message = await self.gen_embed(ctx, song, 4)
                            await self.searching_message.edit(embed = message)
                            self.searching_message = None
                        else:
                            message = await self.gen_embed(ctx, song, 4)
                            await ctx.send(embed = message)
                except Exception as e:
                    print("Add, 12")
                    print(e)



    @commands.command(
        name = "pause",
        aliases = ["stop"],
        help = ""
        )
    async def pause(self, ctx):
        print("Pause command called!")
        id = int(ctx.guild.id)
        try:
            if not self.vc[id]:
                await ctx.send("What do you want me to pause? There's nothing playing, idiot.")
            elif self.is_playing[id]:
                await ctx.send("Audio paused!")
                self.is_playing[id] = False
                self.is_paused[id] = True
                self.vc[id].pause()
        except Exception as e:
            print (e)



    @commands.command(
        name = "skip",
        aliases = ["sk", "next"],
        help = ""
    )
    async def skip(self,ctx):
        id = int(ctx.guild.id)
        print("Skip command called!")
        try:
            if ctx.author.voice == None:
                await ctx.send("You need to be in a VC in this server to use this command.")
            elif self.queue_index[id] >= len(self.music_queue[id]) - 1:
                await ctx.send("End of queue.")
            elif self.vc[id] != None and self.vc[id]:
                self.vc[id].pause()
                self.queue_index[id] += 1
                await self.play_music(ctx)
        except Exception as e:
            print(e)



    @commands.command(
        name = "previous",
        aliases = ["pr"],
        help = ""
    )
    async def previous(self, ctx):
        print("Previous command called!")
        id = int(ctx.guild.id)
        try:
            if self.vc[id] == None:
                await ctx.send("You need to be in a VC to use this command.")
            elif self.queue_index[id] <= 0:
                await ctx.send("there is no previous song in queue.")
            elif self.vc[id] != None and self.vc[id]:
                self.vc[id].pause()
                self.queue_index[id] -= 1
                await self.play_music(ctx)
        except Exception as e:
            print(e)



    @commands.command(
        name = "queue",
        aliases = ["q", "list"],
        help = ""
    )
    async def queue(self, ctx):
        print("Queue command called!")
        id = int(ctx.guild.id)
        try:
            return_value = ""
            if self.music_queue[id] == []:
                await ctx.send("There are currently no songs in the queue!")
                return
            
            for i in range(self.queue_index[id], len(self.music_queue[id])):
                up_next_songs = len(self.music_queue[id]) - self.queue_index[id]
                if i > 6 + up_next_songs:
                    break
                return_index = i - self.queue_index[id]
                if return_index == 0:
                    return_index = "Playing"
                elif return_index == 1:
                    return_index = "Next"
                elif return_index == 2:
                    return_index = 3
                elif return_index == 3:
                    return_index = 4
                elif return_index == 4:
                    return_index = 5
                elif return_index == 5:
                    return_index = 6
                return_value += f"{return_index} - [{self.music_queue[id][i][0]['title']}]({self.music_queue[id][i][0]['link']})\n"

                if return_value == "":
                    await ctx.send("There are no songs in the queue!")
                    return
                
            queue = discord.Embed(
                    title = "Current Queue:",
                    description = return_value,
                    color = self.embed_yellow
            )
            await ctx.send(embed = queue)
        except Exception as e:
            print(e)



    @commands.command(
        name = "clear",
        aliases = ["c", "empty"],
        help = ""
    )
    async def clear(self, ctx):
        print("Clear command called!")
        id = int(ctx.guild.id)
        try:
            if len(self.music_queue[id]) > self.queue_index[id] +1:
                await ctx.send("The queue has been cleared!")
                self.music_queue[id] = self.music_queue[id][:self.queue_index[id] + 1]
            else: 
                len(self.music_queue[id]) == self.queue_index[id]
                await ctx.send("The queue was already empty!")
        except Exception as e:
            print(e)



    @commands.command(
            name = "remove",
            aliases = ["rem"],
            help = ""
            )
    async def remove(self, ctx):
        print("Remove command called!")
        id = int(ctx.guild.id)
        try:
            if self.music_queue[id] != [] and (len(self.music_queue[id]) - self.queue_index[id]) >= 2:
                song = self.music_queue[id][-1][0]
                message = await self.gen_embed(ctx, song, 3)
                await ctx.send(embed = message)
                self.music_queue[id] = self.music_queue[id][:-1]
            else:
                await ctx.send("There are no songs to be removed from the queue")
        except Exception as e:
            print(e)



    @commands.command(
        name = "leave",
        aliases = ["l"],
        help = ""
    )
    async def leave(self, ctx):
        print("Leave command called!")
        id = int(ctx.guild.id)
        try:
            self.is_playing[id] = self.is_paused[id] = False
            self.music_queue[id] = []
            self.queue_index[id] = 0
            if self.vc[id] != None:
                await ctx.send("Bot has left the voice channel.")
                await self.vc[id].disconnect()
                self.vc[id] = None
        except Exception as e:
            print(e)
