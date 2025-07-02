import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel
from discord import sinks # Explicitly import sinks

load_dotenv()

# BotState Pydantic Model
class BotState(BaseModel):
    is_recording: bool = False
    voice_client: discord.VoiceClient | None = None
    connected_channel: discord.VoiceChannel | None = None

    class Config:
        arbitrary_types_allowed = True

# Initialize BotState
bot_state = BotState()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def finished_callback(sink: sinks.WaveSink, channel: discord.TextChannel): # type: ignore
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
    await channel.send(f"Finished recording audio for: {', '.join(recorded_users)}.")

    for user_id, audio in sink.audio_data.items():
        file_name = f"{user_id}_{channel.id}.wav"
        with open(file_name, "wb") as f:
            f.write(audio.file.getvalue())
        await channel.send(f"Saved recording for <@{user_id}> to {file_name}")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name="record")
async def record_command(ctx: commands.Context):
    if not ctx.author.voice:
        await ctx.send("You are not in a voice channel.")
        return

    if bot_state.voice_client and bot_state.voice_client.is_connected():
        await ctx.send("I am already connected to a voice channel.")
        return

    try:
        voice_channel = ctx.author.voice.channel
        bot_state.voice_client = await voice_channel.connect()
        bot_state.voice_client.start_recording(sinks.WaveSink(), finished_callback, ctx.channel)
        bot_state.is_recording = True
        bot_state.connected_channel = voice_channel
        await ctx.send(f"Started recording in {voice_channel.name}!")
    except Exception as e:
        await ctx.send(f"Error connecting to voice channel: {e}")

@bot.command(name="stop")
async def stop_command(ctx: commands.Context):
    if not bot_state.voice_client or not bot_state.voice_client.is_connected():
        await ctx.send("I am not currently in a voice channel.")
        return

    if bot_state.is_recording:
        bot_state.voice_client.stop_recording()
        bot_state.is_recording = False
        await ctx.send("Stopped recording.")
    else:
        await ctx.send("I am not currently recording.")

    await bot_state.voice_client.disconnect()
    bot_state.voice_client = None
    bot_state.connected_channel = None

async def start_bot():
    await bot.start(os.environ["DISCORD_TOKEN"])

async def close_bot():
    if bot_state.voice_client and bot_state.voice_client.is_connected():
        await bot_state.voice_client.disconnect()
        bot_state.voice_client = None
        bot_state.connected_channel = None
    await bot.close()