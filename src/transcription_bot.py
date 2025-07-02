from pprint import pprint
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel
from discord import VoiceClient, VoiceChannel

load_dotenv()


# BotState Pydantic Model
class BotState(BaseModel):
    is_recording: bool = False
    voice_client: VoiceClient | None = None
    connected_channel: VoiceChannel | None = None

    class Config:
        arbitrary_types_allowed = True


# Initialize BotState
bot_state = BotState()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


# Create Slash Command group for recording
record = bot.create_group("record", "Voice recording commands")


@record.command()
async def start(ctx):
    print(f"/record start received from {ctx.author}")
    if not isinstance(ctx.author, discord.Member) or ctx.author.voice is None:
        await ctx.respond("You are not connected to a voice channel.")
        return
    channel = ctx.author.voice.channel
    print("connecting to channel", channel)
    if channel is None:
        await ctx.respond("Could not find your voice channel.")
        return
    if ctx.voice_client is None:
        bot_state.voice_client = await channel.connect()
        bot_state.connected_channel = channel
    else:
        # If already connected, disconnect and reconnect
        await ctx.voice_client.disconnect()
        bot_state.voice_client = await channel.connect()
        bot_state.connected_channel = channel

    vc = bot_state.voice_client

    async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):
        recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
        await sink.vc.disconnect()
        files = []
        for user_id, audio in sink.audio_data.items():
            files.append(discord.File(audio.file, f"{user_id}.{sink.encoding}"))
        pprint(files)
        print(
            f"finished recording audio for: {', '.join(recorded_users)}.",
        )

    vc.start_recording(
        discord.sinks.WaveSink(),
        once_done,
        ctx.channel,
    )
    bot_state.is_recording = True
    await ctx.respond(f"Started recording in {channel.name}!")


@record.command()
async def stop(ctx):
    print(f"/record stop received from {ctx.author}")
    if bot_state.voice_client and bot_state.voice_client.is_connected():
        bot_state.voice_client.stop_recording()
        await bot_state.voice_client.disconnect()
        bot_state.voice_client = None
        bot_state.connected_channel = None
        bot_state.is_recording = False
        await ctx.respond("Stopped recording and disconnected from the voice channel.")
    else:
        await ctx.respond("I am currently not recording here.")
