"""HORA LIVE: TikTokLive -> Server Sent Events. Unofficial TikTok client. """
import asyncio
import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent

USERNAME=os.getenv('TIKTOK_USERNAME','').strip().lstrip('@')
ALLOWED_ORIGIN=os.getenv('ALLOWED_ORIGIN','https://dovik-f3697e.netlify.app').strip()
clients=set()
status={'live':False,'username':USERNAME,'configured':bool(USERNAME)}

async def publish(event):
    encoded=json.dumps(event,ensure_ascii=False)
    for q in list(clients):
        try:
            if q.full(): q.get_nowait()
            q.put_nowait(encoded)
        except (asyncio.QueueFull,asyncio.QueueEmpty): pass

async def connect_forever():
    if not USERNAME:return
    while True:
        client=TikTokLiveClient(unique_id='@'+USERNAME)
        @client.on(CommentEvent)
        async def comment(event):
            await publish({'type':'comment','user':event.user.nickname or event.user.unique_id,'text':event.comment})
        @client.on(GiftEvent)
        async def gift(event):
            gift_obj=event.gift
            if not gift_obj:return
            if getattr(event,'streaking',False):return
            qty=max(1,int(getattr(event,'repeat_count',1) or 1))
            await publish({'type':'gift','user':event.user.nickname or event.user.unique_id,'gift':str(getattr(gift_obj,'name','Gift')),'diamonds':int(getattr(gift_obj,'diamond_count',1) or 1),'count':qty})
        try:
            await client.connect()
            status['live']=True
            await publish({'type':'status','live':True})
            # client.connect() is normally long running until disconnect
            status['live']=False
        except asyncio.CancelledError: raise
        except Exception as exc:
            status['live']=False
            status['error']=str(exc)[:120]
        await publish({'type':'status','live':False})
        await asyncio.sleep(20)

@asynccontextmanager
async def lifespan(app):
    task=asyncio.create_task(connect_forever())
    yield
    task.cancel()
    try:await task
    except asyncio.CancelledError: pass

app=FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[ALLOWED_ORIGIN],allow_methods=['GET'],allow_headers=['*'])

@app.get('/')
async def root():return {'app':'Hora Românilor bridge','status':status,'help':'Connect via /events'}

@app.get('/events')
async def events():
    q=asyncio.Queue(maxsize=200)
    clients.add(q)
    async def feed():
        try:
            yield 'data: '+json.dumps({'type':'status','live':status['live']})+'\n\n'
            while True:
                try:
                    payload=await asyncio.wait_for(q.get(),timeout=20)
                    yield 'data: '+payload+'\n\n'
                except asyncio.TimeoutError:yield ': ping\n\n'
        finally:clients.discard(q)
    return StreamingResponse(feed(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})
