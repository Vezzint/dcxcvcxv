from fastapi import FastAPI, Request, Response
from aiogram import Bot, types
from bot import dp, BOT_TOKEN, init_db, run_check_once

bot = Bot(token=BOT_TOKEN)
app = FastAPI()

WEBHOOK_URL = "https://dcxcvcxv-49y3.vercel.app/api/webhook"

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot is running"}

@app.get("/set_webhook")
async def set_webhook():
    result = await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    return {"webhook_set": result, "url": WEBHOOK_URL}

@app.get("/api/cron")
async def cron_check():
    await run_check_once()
    return {"status": "checked"}

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    await init_db()
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
        return Response(status_code=200)
    except Exception as e:
        print(f"Error processing update: {e}")
        return Response(status_code=200)
