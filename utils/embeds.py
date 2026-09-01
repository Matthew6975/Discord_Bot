import discord
from utils.models import EmbedType

#embed colors to reference later.
embed_blue = 0x2c76dd
embed_red = 0xdf1141
embed_green = 0x0eaa51
embed_purple = 0x800080


#Generates different embeds to be sent in the chat based on the type used to call the function.
#generally used to show what is playing/what was added to the queue.
async def gen_embed(ctx, song, embed_type):
    if song:
        title = song.title
        link = song.link
        thumbnail = song.thumbnail
    else:
        title = link = thumbnail = None

    author = ctx.author.display_name
    avatar = ctx.author.avatar

    if embed_type == EmbedType.NOW_PLAYING:
        embed = discord.Embed(
            title = "Now Playing",
            description = f"[{title}]({link})",
            color = embed_blue
            )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text = f"Song Added by: {str(author)}", icon_url = avatar)

    elif embed_type == EmbedType.SONG_ADDED:
        embed = discord.Embed(
            title = "Song Added to Queue!",
            description = f"[{title}]({link})",
            color = embed_green
            )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text = f"Song Added by: {str(author)}", icon_url = avatar)
    
    elif embed_type == EmbedType.SONG_REMOVED:
        embed = discord.Embed(
            title = "Song Removed From Queue!",
            description = f"[{title}]({link})",
            color = embed_red
            )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text = f"Song Removed by: {str(author)}", icon_url = avatar)

    elif embed_type == EmbedType.SONG_NEXT:
        embed = discord.Embed(
            title = "Song Inserted Next in Queue!",
            description = f"[{title}]({link})",
            color = embed_purple
            )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text = f"Song Inserted by: {str(author)}", icon_url = avatar)

    elif embed_type == EmbedType.SEARCHING:
        embed = discord.Embed(
            title = "Searching for song ...",
            description = "searching for song ... please wait.",
            color = embed_blue
        )
    return embed
