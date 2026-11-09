"""Hora Romanilor: TikTok LIVE comments/gifts -> SSE events for the web game.

TikTokLive is an unofficial API client; TikTok changes may affect detection.
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, ConnectEvent, DisconnectEvent

USERNAME = os.getenv("TIKTOK_USERNAME", "").strip().lstrip("@")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://dovik-f3697e.netlify.app").strip()
RETRY_SECONDS = 20
clients = set()
status = {"live": False, "username": USERNAME, "configured": bool(USERNAME)}


async def publish(event):
    encoded = json.dumps(event, ensure_ascii=False)
    for queue in list(clients):
        try:
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(encoded)
        except (asyncio.QueueFull, asyncio.QueueEmpty):
            pass


async def set_live(value, error=None):
    status["live"] = value
    if error:
        status["error"] = error[:250]
    else:
        status.pop("error", None)
    await publish({"type": "status", "live": value})


async def connect_forever():
    if not USERNAME:
        status["error"] = "TIKTOK_USERNAME is not configured"
        print("TikTok: missing TIKTOK_USERNAME", flush=True)
        return

    while True:
        client = TikTokLiveClient(unique_id="@" + USERNAME)

        @client.on(ConnectEvent)
        async def on_connect(event):
            print(f"TikTok LIVE CONNECTED: @{USERNAME}", flush=True)
            await set_live(True)

        @client.on(DisconnectEvent)
        async def on_disconnect(event):
            print(f"TikTok LIVE DISCONNECTED: @{USERNAME}", flush=True)
            await set_live(False)

        @client.on(CommentEvent)
        async def on_comment(event):
            user = event.user.nickname or event.user.unique_id
            print(f"TikTok COMMENT: {user}: {event.comment}", flush=True)
            await publish({"type": "comment", "user": user, "text": event.comment})

        @client.on(GiftEvent)
        async def on_gift(event):
            gift = event.gift
            if not gift:
                return
            # Ignore intermediate events within gift streaks to prevent double counting.
            if getattr(event, "streaking", False):
                return
            user = event.user.nickname or event.user.unique_id
            quantity = max(1, int(getattr(event, "repeat_count", 1) or 1))
            name = str(getattr(gift, "name", "Gift"))
            diamonds = int(getattr(gift, "diamond_count", 1) or 1)
            print(f"TikTok GIFT: {user}, {name}, count={quantity}", flush=True)
            await publish({
                "type": "gift", "user": user, "gift": name,
                "diamonds": diamonds, "count": quantity
            })

        try:
            print(f"TikTok: attempting connection to @{USERNAME}", flush=True)
            await client.connect()  # Blocks while the live websocket is connected.
            print("TikTok: connection ended; retry scheduled", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            print(f"TikTok connection error: {message}", flush=True)
            await set_live(False, message)
        finally:
            # Covers both normal disconnect and abnormal websocket closure.
            if status["live"]:
                await set_live(False)

        await asyncio.sleep(RETRY_SECONDS)


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(connect_forever())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"app": "Hora Romanilor bridge", "status": status, "help": "Connect via /events"}


@app.get("/events")
async def events():
    queue = asyncio.Queue(maxsize=200)
    clients.add(queue)

    async def feed():
        try:
            yield "data: " + json.dumps({"type": "status", "live": status["live"]}) + "\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20)
                    yield "data: " + payload + "\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            clients.discard(queue)

    return StreamingResponse(
        feed(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
