import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from aiogram import Bot, types
from bot import get_dispatcher, BOT_TOKEN

# Получить URL развертывания Vercel, например: https://your-project.vercel.app
# В настройках проекта Vercel рекомендуется установить переменную окружения WEBHOOK_URL
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://dcxcvcxv-git-main-dd-ser.vercel.app")
WEBHOOK_PATH = "/api/webhook"

bot = Bot(token=BOT_TOKEN)
dp = get_dispatcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Установить Webhook при запуске
    full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(full_url, drop_pending_updates=True)
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """Получать обновления от Telegram"""
    update_data = await request.json()
    update = types.Update(**update_data)
    
    # Установить текущий Bot и Dispatcher (обязательно для aiogram)
    Bot.set_current(bot)
    dp.set_current(dp) # В некоторых версиях aiogram может потребоваться Dispatcher.set_current
    
    # Передать обновление в aiogram для обработки
    await dp.feed_update(bot, update)
    return Response(status_code=200)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot is running"}
