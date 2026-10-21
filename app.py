from fastapi import FastAPI, Request, Response
from aiogram import Bot, types
from your_bot_module import dp, bot  # импортируйте ваш dispatcher и bot

app = FastAPI()

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)
    return Response(status_code=200)
