import discord
from discord.ext import commands
import asyncio
import logging
from utils.models import ServerState, EmbedType
from utils.embeds import gen_embed
from utils.youtube import search_YT, extract_YT, ffmpeg_options

log = logging.getLogger(__name__)

async def setup(bot):
    await bot.add_cog(music_cog(bot))

async def ensure_voice(ctx):
    state = ctx.bot.cogs['music_cog'].get_server_state(int(ctx.guild.id))
    if ctx.author.voice is None:
        await ctx.send("You must be connected to a voice channel to send commands.")
        raise commands.CommandError("Author not in voice channel.")
    if state.vc is not None and ctx.author.voice.channel != state.vc.channel:
        await ctx.send("You must be connected to the same VC as the bot to send commands.")
        raise commands.CommandError("Author in different voice channel.")
    return True


#initialize the music cog to the bot.
class music_cog(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot

        #Initialize the server states dictionary to track the state of the bot in each server.
        self.server_states = {}


    #listener that runs when the bot is ready. Sets all variables to default values each time the code is run/re-run.
    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.bot.user} has connected to Discord!")
        self.server_states.clear()
        for guild in self.bot.guilds:
            self.get_server_state(guild.id)


    #listener that runs when a user leaves a voice channel. If the bot is the only one left in the channel, it disconnects.
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        state = self.get_server_state(int(member.guild.id))
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remaining_channel_members = before.channel.members
            if len(remaining_channel_members) == 1 and remaining_channel_members[0].id == self.bot.user.id and state.vc is not None and state.vc.is_connected():
                await state.vc.disconnect()
                state.is_playing = state.is_paused = False
                state.music_queue = []
                state.queue_index = 0
                state.searching_message = state.now_playing_message = state.song_added_message = state.vc = None



#-----------------------------------NON-CALLABLE FUNCTIONS-----------------------------------------------------


    def get_server_state(self, guild_id: int) -> ServerState:
        if guild_id not in self.server_states:
            self.server_states[guild_id] = ServerState()
        return self.server_states[guild_id]


    #Causes the bot to join the VC of the user that called the command. 
    #Has some error handling to make sure the bot doesn't try to join a channel that doesn't exist or is empty.
    async def join_vc(self, ctx, channel):
        state = self.get_server_state(int(ctx.guild.id))
        log.info("join_vc called")

        if state.vc == None or not state.vc.is_connected():
            state.vc = await channel.connect()

            if state.vc == None:
                await ctx.send("Could not connect to the voice channel")
                return
        else:
            await state.vc.move_to(channel)
    

    def play_next_callback(self, ctx, e):
            if e:
                log.error(f"Player error: {e}")
            asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)

    
    #moves the bot to the next song in the queue if the current song ends.
    #calls itself towards the bottom and incriments the queue to loop and continue playing the next song automatically.
    async def play_next(self, ctx):
        log.info("play next, main")
        state = self.get_server_state(int(ctx.guild.id))
        if not state.is_playing:
            log.debug("play next, if 1")
            return
        if state.queue_index + 1 < len(state.music_queue):
            log.debug("play next, if 2")
            log.debug("length of the music queue: " + str(len(state.music_queue)))
            log.debug("Current position in the queue: " + str(state.queue_index))
            state.is_playing = True
            state.queue_index += 1

            song = state.music_queue[state.queue_index]

            #if a "now playing" message exists, it deletes it and then replaces it with a new, updated one later in the function.
            #has some built-in error handling.
            if state.now_playing_message:
                log.debug("self.now_playing_message, play_next")
                try:
                    await state.now_playing_message.delete()
                except Exception as e:
                    log.error(f"Failed to delete now playing message: {e}")

            #you'll see this code a lot. This is the block that calls gen_embed to generate a embed to send to the chat.
            playing_embed = await gen_embed(ctx, song, EmbedType.NOW_PLAYING)
            state.now_playing_message = await ctx.send(embed = playing_embed)

            state.vc.play(discord.FFmpegOpusAudio(song.source, **ffmpeg_options), after=lambda e: self.play_next_callback(ctx, e))
            # state.vc.play(discord.FFmpegOpusAudio(song["source"], **ffmpeg_options), after = lambda e:  asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop,))
        
        #end of queue handling. Sends a message letting the user(s) know that the queue is empty.
        else:
            log.debug("play next, else")
            await ctx.send("You have reached the end of the queue!")
            state.queue_index += 1
            state.is_playing = False


    #kicks off the music playing process. Very similar to the play next function in most of it's design.
    #upon reviewing this code, I think I could probably combine the two functions into one to practice DRY coding. Will look into this.
    async def play_music(self, ctx):
        log.info("play music called")
        state = self.get_server_state(int(ctx.guild.id))
        if state.queue_index < len(state.music_queue):
            log.debug("play music, 1")
            state.is_playing = True
            state.is_paused = False

            await self.join_vc(ctx, state.vc_channel)

            song = state.music_queue[state.queue_index]

            if state.now_playing_message:
                log.debug("self.now_playing_message, play_next")
                try:
                    await state.now_playing_message.delete()
                except Exception as e:
                    log.error(f"Failed to delete now playing message: {e}")

            if state.searching_message:
                playing_embed = await gen_embed(ctx, song, EmbedType.NOW_PLAYING)
                state.now_playing_message = await state.searching_message.edit(embed = playing_embed)
                state.searching_message = None
            else:
                playing_embed = await gen_embed(ctx, song, EmbedType.NOW_PLAYING)
                state.now_playing_message = await ctx.send(embed = playing_embed)
                
            #state.vc.play(discord.FFmpegOpusAudio(song["source"], **self.ffmpeg_options), after = lambda e:  asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop,))
            state.vc.play(discord.FFmpegOpusAudio(song.source, **ffmpeg_options), after=lambda e: self.play_next_callback(ctx, e))
            
        else:
            log.debug("play music, 2")
            await ctx.send("There are no more songs in the queue")
            state.queue_index += 1
            state.is_playing = False


#------------------------------CALLABLE COMMANDS------------------------------------------------------------------------------------

    @commands.command(
            name = "play",
            aliases = ["pl"],
            help = ""
        )
    @commands.check(ensure_voice)
    
    async def play(self, ctx, *args):
        log.info("Play command called!")
        search = " ".join(args)
        state = self.get_server_state(int(ctx.guild.id))
        state.vc_channel = ctx.author.voice.channel

        if not args:
            log.debug("Play, 1")
            if len(state.music_queue) == 0:
                log.debug("Play, 2")
                await ctx.send("there are no more songs in queue.")
                return
            elif state.is_playing == False:
                if state.music_queue == None or state.vc == None:
                    log.debug("Play, 3")
                    await self.play_music(ctx)
                else:
                    log.debug("Play, 4")
                    state.is_paused = False
                    state.is_playing = True
                    state.vc.resume()
            else:
                log.debug("Play, 5")
                return
        elif args:
            loading_embed = await gen_embed(ctx, None, EmbedType.SEARCHING)
            state.searching_message = await ctx.send(embed = loading_embed)
            log.debug("Play, 6")
            search_results = await search_YT(search)
            log.debug("search_results" + str(search_results))
            song = await extract_YT(search_results)
            if song == False:
                log.debug("Play, 7")
                await ctx.send("Could not download song. Incorrect format, try again with some different keywords.")
            else:
                log.debug("Play, 8")
                state.music_queue.append(song)
                log.debug(state.music_queue)

                if not state.is_playing and state.is_paused:
                    log.debug("Play, 9")
                    state.queue_index += 1
                    await self.play_music(ctx)
                elif not state.is_playing:
                    log.debug("Play, 10")
                    await self.play_music(ctx)
                else:
                    log.debug("Play, 11")
                    if state.searching_message:
                        message = await gen_embed(ctx, song, EmbedType.SONG_ADDED)
                        state.song_added_message = await state.searching_message.edit(embed = message)
                        state.searching_message = None
                    else:
                        message = await gen_embed(ctx, song, EmbedType.SONG_ADDED)
                        state.song_added_message = await ctx.send(embed = message)


                

    @commands.command(
        name = "add",
        aliases = ["insert"],
        help = ""
        )
    @commands.check(ensure_voice)
    async def add(self, ctx, *args):
            log.info("Add command called!")
            search = " ".join(args)
            state = self.get_server_state(int(ctx.guild.id))
            if not args:
                await ctx.send("You need to provide a search term to add a song to the queue.")
            else:
                try:
                    log.debug("Add, 9")
                    loading_embed = await gen_embed(ctx, None, EmbedType.SEARCHING)
                    state.searching_message = await ctx.send(embed = loading_embed)
                    search_results = await search_YT(search)
                    song = await extract_YT(search_results)
                    if song == False:
                        log.debug("Add, 10")
                        await ctx.send("Could not download the song. Incorrect format, try some different keywords.")
                    else:
                        log.debug("Add, 11")
                        state.music_queue.insert(state.queue_index + 1, song)
                        if state.searching_message:
                            message = await gen_embed(ctx, song, EmbedType.SONG_NEXT)
                            await state.searching_message.edit(embed = message)
                            state.searching_message = None
                        else:
                            message = await gen_embed(ctx, song, EmbedType.SONG_NEXT)
                            await ctx.send(embed = message)
                except Exception as e:
                    log.error("Add, 12")
                    log.exception(f"Add, 12: {e}")



    @commands.command(
        name = "pause",
        aliases = ["stop"],
        help = ""
        )
    @commands.check(ensure_voice)
    async def pause(self, ctx):
        log.info("Pause command called!")
        state = self.get_server_state(int(ctx.guild.id))
        try:
            if not state.vc:
                await ctx.send("There's nothing to pause. The bot is not connected to a voice channel.")
            elif state.is_playing:
                await ctx.send("Audio paused!")
                state.is_playing = False
                state.is_paused = True
                state.vc.pause()
        except Exception as e:
            log.exception(f"Pause, 1: {e}")



    @commands.command(
        name = "skip",
        aliases = ["sk", "next"],
        help = ""
    )
    @commands.check(ensure_voice)
    async def skip(self,ctx):
        state = self.get_server_state(int(ctx.guild.id))
        log.info("Skip command called!")
        try:
            if state.queue_index >= len(state.music_queue) - 1:
                await ctx.send("End of queue.")
            elif state.vc != None and state.vc:
                state.vc.pause()
                state.queue_index += 1
                await self.play_music(ctx)
        except Exception as e:
            log.exception(f"Skip: {e}")



    @commands.command(
        name = "previous",
        aliases = ["pr"],
        help = ""
    )
    @commands.check(ensure_voice)
    async def previous(self, ctx):
        log.info("Previous command called!")
        state = self.get_server_state(int(ctx.guild.id))
        try:
            if state.queue_index <= 0:
                await ctx.send("there is no previous song in queue.")
            elif state.vc != None and state.vc:
                    state.vc.pause()
                    state.queue_index -= 1
                    await self.play_music(ctx)
        except Exception as e:
            log.exception(f"Previous: {e}")



    @commands.command(
        name = "queue",
        aliases = ["q", "list"],
        help = ""
    )
    async def queue(self, ctx):
        log.info("Queue command called!")
        state = self.get_server_state(int(ctx.guild.id))
        try:
            return_value = ""
            if state.music_queue == []:
                await ctx.send("There are currently no songs in the queue!")
                return

            for i in range(state.queue_index, len(state.music_queue)):
                up_next_songs = len(state.music_queue) - state.queue_index
                if i > 6 + up_next_songs:
                    break
                return_index = i - state.queue_index
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
                return_value += f"{return_index} - [{state.music_queue[i].title}]({state.music_queue[i].link})\n"

                if return_value == "":
                    await ctx.send("There are no songs in the queue.")
                    return
                
            queue = discord.Embed(
                    title = "Current Queue:",
                    description = return_value,
                    color = self.embed_yellow
            )
            await ctx.send(embed = queue)
        except Exception as e:
            log.exception(f"Queue: {e}")



    @commands.command(
        name = "clear",
        aliases = ["c", "empty"],
        help = ""
    )
    @commands.check(ensure_voice)
    async def clear(self, ctx):
        log.info("Clear command called!")
        state = self.get_server_state(int(ctx.guild.id))
        try:
            if len(state.music_queue) > state.queue_index +1:
                await ctx.send("The queue has been cleared!")
                state.music_queue = state.music_queue[:state.queue_index + 1]
            else: 
                await ctx.send("The queue was already empty!")
        except Exception as e:
            log.exception(f"Clear: {e}")



    @commands.command(
            name = "remove",
            aliases = ["rem"],
            help = ""
            )
    @commands.check(ensure_voice)
    async def remove(self, ctx):
        log.info("Remove command called!")
        state = self.get_server_state(int(ctx.guild.id))
        try:
            if state.music_queue != [] and (len(state.music_queue) - state.queue_index) >= 2:
                song = state.music_queue[-1]
                message = await gen_embed(ctx, song, EmbedType.SONG_REMOVED)
                await ctx.send(embed = message)
                state.music_queue = state.music_queue[:-1]
            else:
                await ctx.send("There are no songs to be removed from the queue")
        except Exception as e:
            log.exception(f"Remove: {e}")



    @commands.command(
        name = "leave",
        aliases = ["l"],
        help = ""
    )
    @commands.check(ensure_voice)
    async def leave(self, ctx):
        log.info("Leave command called!")
        state = self.get_server_state(int(ctx.guild.id))
        try:
            state.is_playing = state.is_paused = False
            state.music_queue = []
            state.queue_index = 0
            if state.vc != None:
                await ctx.send("Bot has left the voice channel.")
                await state.vc.disconnect()
                state.vc = None
        except Exception as e:
            log.exception(f"Leave: {e}")