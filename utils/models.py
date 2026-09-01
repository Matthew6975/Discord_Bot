import discord
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

#This dataclass is here to track the state of the bot in each server.
#This will replace the need to track 8 different dictionaries for each server and will no longer require [id] everywhere.
@dataclass
class ServerState:
    is_playing: bool = False
    is_paused: bool = False
    music_queue: list = field(default_factory=list)
    queue_index: int = 0
    vc: Optional[discord.VoiceClient] = None
    searching_message: Optional[discord.Message] = None
    now_playing_message: Optional[discord.Message] = None
    song_added_message: Optional[discord.Message] = None
    vc_channel: Optional[discord.VoiceChannel] = None


@dataclass
class Song:
    title: str
    link: str
    thumbnail: str
    source: str


class EmbedType(Enum):
    NOW_PLAYING = 1
    SONG_ADDED = 2
    SONG_REMOVED = 3
    SONG_NEXT = 4
    SEARCHING = 5