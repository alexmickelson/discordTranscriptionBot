import fastapi
import asyncio
from contextlib import asynccontextmanager
from src.transcription_bot import start_bot, close_bot

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    asyncio.create_task(start_bot())
    yield
    await close_bot()

app = fastapi.FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}