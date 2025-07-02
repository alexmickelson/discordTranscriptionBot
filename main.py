import os
import fastapi
import asyncio
from contextlib import asynccontextmanager
from src.transcription_bot import bot
import sys

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    bot_task = asyncio.create_task(bot.start(os.environ["DISCORD_TOKEN"]))
    yield
    bot_task.cancel()

app = fastapi.FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}