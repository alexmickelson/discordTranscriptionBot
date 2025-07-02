from pprint import pprint
import os
from typing import Optional
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel
import discord
from discord.ext import commands, voice_recv
import speech_recognition as sr

load_dotenv()


class BotState(BaseModel):
    is_recording: bool = False
    voice_client: discord.VoiceClient | None = None

    class Config:
        arbitrary_types_allowed = True


bot_state = BotState()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.tree.sync()
    print(f"Synced commands globally.")


@bot.tree.command(
    name="start_recording", description="Start recording audio in your voice channel."
)
async def start(interaction: discord.Interaction):
    print(f"/record start received from {interaction.user}")
    if (
        not isinstance(interaction.user, discord.Member)
        or interaction.user.voice is None
    ):
        await interaction.response.send_message(
            "You are not connected to a voice channel."
        )
        return

    channel = interaction.user.voice.channel
    print("connecting to channel", channel)
    if channel is None:
        await interaction.response.send_message("Could not find your voice channel.")
        return
    if interaction.guild.voice_client is not None:
        print("disconnecting from previous channel")
        await interaction.guild.voice_client.disconnect()

    bot_state.voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)

    # def callback(user: discord.User, data: voice_recv.VoiceData):
    #     print(f"Got packet from {user}")
    #     # ext_data = data.packet.extension_data.get(voice_recv.ExtensionID.audio_power)
    #     # value = int.from_bytes(ext_data, "big")
    #     # power = 127 - (value & 127)
    #     # print("#" * int(power * (79 / 128)), flush=True)

    # def rtcp_callback(packet: voice_recv.RTCPPacket):
    #     print(f"rtcp {packet.length}")
    #     # ext_data = data.packet.extension_data.get(voice_recv.ExtensionID.audio_power)
    #     # value = int.from_bytes(ext_data, "big")
    #     # power = 127 - (value & 127)
    #     # print("#" * int(power * (79 / 128)))

    # # sink = voice_recv.BasicSink(event=callback, rtcp_event=rtcp_callback)
    # sink = voice_recv.extras.speechrecognition.SpeechRecognitionSink(event=callback, rtcp_event=rtcp_callback)

    def process_wit(recognizer: sr.Recognizer, audio: sr.AudioData, user: Optional[str]) -> Optional[str]:
        print(f"Processing audio for user: {user}")
        text: Optional[str] = None
        try:
            # func = getattr(recognizer, 'recognize_google', recognizer.recognize_google)
            # text = func(audio)
            text = recognizer.recognize_faster_whisper(audio)
            print(text)
            # send the transcribed audio to an async event
            # asyncio.run_coroutine_threadsafe(self.handleTranscribedAudio(user, text), self.client.loop)
        except sr.UnknownValueError:
            pass
        return text
    
    sink = voice_recv.extras.speechrecognition.SpeechRecognitionSink(process_cb=process_wit, default_recognizer="whisper")
    bot_state.voice_client.listen(sink)
    bot_state.is_recording = True
    await interaction.response.send_message(f"Started recording in {channel.name}!")


@bot.tree.command(
    name="stop_recording",
    description="Stop recording audio and disconnect from the voice channel.",
)
async def stop(interaction: discord.Interaction):
    print(f"/record stop received from {interaction.user}")
    if bot_state.voice_client and bot_state.voice_client.is_connected():
        bot_state.voice_client.stop_recording()
        await bot_state.voice_client.disconnect()
        bot_state.voice_client = None
        bot_state.is_recording = False
        await interaction.response.send_message(
            "Stopped recording and disconnected from the voice channel."
        )
    else:
        await interaction.response.send_message("I am currently not recording here.")
