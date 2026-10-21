import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from aiogram import Bot, types
from bot import dp, BOT_TOKEN, init_db

bot = Bot(token=BOT_TOKEN)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        print(f"Ошибка БД: {e}")
    
    webhook_url = "https://dcxcvcxv-49y3.vercel.app/api/webhook"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    print(f"Вебхук установлен на {webhook_url}")
    
    yield
    
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
        return Response(status_code=200)
    except Exception as e:
        print(f"Ошибка при обработке вебхука: {e}")
        return Response(status_code=200) 

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot is running"}
